"""Conflict agent for pulling ACLED data and flagging events."""

import os
import sys
import requests  # type: ignore
import json
from typing import Optional, Tuple, List, Dict, Any, cast
from datetime import date, timedelta
from dotenv import load_dotenv  # auto-load .env
from pathlib import Path

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.guardrails import pii_filter
from src.db.sqlite_writer import init_db, insert_event

load_dotenv()

def get_conflict_feed(limit: int = 5000,
                      region: Optional[str] = None,
                      date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
    """Fetch conflict feed from ACLED, handling pagination."""
    api_key = os.getenv("ACLED_API_KEY")
    if not api_key:
        raise EnvironmentError("ACLED_API_KEY not set in environment")
    email = os.getenv("ACLED_EMAIL")
    if not email:
        raise EnvironmentError("ACLED_EMAIL not set in environment")
    
    all_data: List[Dict[str, Any]] = []
    next_page_url: Optional[str] = "https://api.acleddata.com/acled/read"
    
    # Initial parameters (only for the first request)
    params = {"key": api_key, "limit": limit, "email": email}
    if region:
        params["region"] = region
    # Apply date_range (start_date and end_date) for filtering
    if date_range and len(date_range) == 2:
        params["start_date"], params["end_date"] = date_range
    else:
        # Default to yesterday if no date_range provided
        yesterday = date.today() - timedelta(days=1)
        yesterday_str = yesterday.isoformat()
        params["start_date"] = yesterday_str
        params["end_date"] = yesterday_str
        
    page_count = 0
    max_pages = 100  # Safety break to prevent infinite loops
    # Respect the caller provided limit for the overall number of events
    # returned rather than using a fixed constant.
    total_event_limit = limit

    while next_page_url and page_count < max_pages:
        page_count += 1
        print(f"Fetching ACLED data page {page_count} from: {next_page_url}") # Log progress
        try:
            # --- Corrected request logic for pagination ---
            if page_count == 1:
                # First page: use base URL and constructed params
                resp = requests.get(next_page_url, params=params, timeout=120)
            else:
                # Subsequent pages: use the full next_page_url directly (no extra params)
                resp = requests.get(next_page_url, timeout=120)
            # --- End correction ---
            resp.raise_for_status()
        except requests.RequestException as e:
            # Log error but try to return data fetched so far
            print(f"ACLED API error on page {page_count}: {e}. Returning partial data.")
            break # Exit loop on error
            
        try:
            payload = resp.json()
        except requests.exceptions.JSONDecodeError as e:
            print(f"Failed to decode JSON on page {page_count}: {e}. Response text: {resp.text[:500]}... Returning partial data.")
            break # Exit loop on decode error

        # --- DEBUG: Print raw API payload ---
        if page_count == 1: # Only print for the first page
            print(f"--- Raw ACLED API Payload (Page {page_count}) ---")
            print(json.dumps(payload, indent=2))
            print("--- End Raw Payload ---")
        # --- End DEBUG ---
        
        page_data = payload.get("data", [])
        if isinstance(page_data, list):
            all_data.extend(page_data)
            # --- Check total event limit ---
            if len(all_data) >= total_event_limit:
                 print(f"Reached total event limit of {total_event_limit}. Stopping pagination.")
                 break # Stop fetching more pages
            # --- End check ---
        else:
            print(f"Warning: Unexpected data format on page {page_count}")

        # Get the next page URL from the payload
        next_page_url = payload.get("next_page")
        
        # Clear params after first request as next_page_url contains them
        if page_count == 1:
             params = {} # Params are now baked into next_page_url

    if page_count >= max_pages:
         print(f"Warning: Reached maximum page limit ({max_pages}). Data may be incomplete.")

    # --- Enforce exact limit before returning ---
    final_data = all_data[:total_event_limit]
    print(f"Fetched {len(all_data)} events across {page_count} pages. Returning {len(final_data)} events (limit: {total_event_limit}).")
    # --- End enforcement ---
    
    return final_data
    

def flag_event(event: Dict[str, Any], threshold: int = 10) -> Dict[str, Any]:
    """Flag events where fatalities exceed a threshold."""
    fatal_raw = event.get("fatalities", 0)
    try:
        count = int(fatal_raw)
    except (ValueError, TypeError):
        count = 0
    flagged = count >= threshold
    return {"flagged": flagged, "event": event}

def run() -> Dict[str, Any]:
    """Entrypoint for the conflict agent, with PII sanitization."""
    # Initialize database
    init_db()
    # Determine region override from environment if provided
    region_override = os.getenv("ACLED_REGION")
    
    # Always fetch yesterday's data 
    yesterday = date.today() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    # Limit parameter is handled by default in get_conflict_feed
    events = get_conflict_feed(region=region_override, date_range=(yesterday_str, yesterday_str))
    file_date = yesterday_str # Use yesterday for the filename as well
    
    # Persist events to SQLite
    for e in events:
        insert_event(e)
    # Save raw JSON to data/raw/<date>_conflict.json
    try:
        raw_dir = Path(__file__).parents[2] / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / f"conflict_{file_date}.json"
        with raw_file.open("w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except Exception:
        pass
    flagged = [flag_event(e) for e in events]
    result: Dict[str, Any] = {"status": "success", "data": flagged}
    # Sanitize output for PII
    filtered = pii_filter(json.dumps(result))
    filtered_json = json.loads(filtered)
    return cast(Dict[str, Any], filtered_json)


