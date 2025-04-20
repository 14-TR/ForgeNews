"""Conflict agent for pulling ACLED data and flagging events."""

import os
import sys
import requests  # type: ignore
import json
from typing import Optional, Tuple, List, Dict, Any, cast
from datetime import date
from dotenv import load_dotenv  # auto-load .env
from pathlib import Path

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.guardrails import pii_filter
from src.db.sqlite_writer import init_db, insert_event

load_dotenv()

def get_conflict_feed(limit: int = 100,
                      region: Optional[str] = None,
                      date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
    """Fetch conflict feed from ACLED with optional region and date range."""
    api_key = os.getenv("ACLED_API_KEY")
    if not api_key:
        raise EnvironmentError("ACLED_API_KEY not set in environment")
    email = os.getenv("ACLED_EMAIL")
    if not email:
        raise EnvironmentError("ACLED_EMAIL not set in environment")
    url = "https://api.acleddata.com/acled/read"
    params = {"key": api_key, "limit": limit, "email": email}
    if region:
        params["region"] = region
    # Default to today's date if no date_range provided
    if date_range is None:
        today_str = date.today().isoformat()
        date_range = (today_str, today_str)
    # Apply date_range (start_date and end_date) for filtering
    if len(date_range) == 2:
        params["start_date"], params["end_date"] = date_range
    # Fetch only one record without pagination
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"ACLED API error: {e}")
    payload = resp.json()
    data = payload.get("data", [])
    # Process all records returned by the API
    # Ensure data is properly formatted
    if not isinstance(data, list):
        print("Warning: Unexpected data format from ACLED API")
        data = []
    
    # Return all records instead of limiting to first record
    return data
    

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
    # Determine date_range override from environment if provided
    start_date = os.getenv("ACLED_START_DATE")
    end_date = os.getenv("ACLED_END_DATE")
    if start_date and end_date:
        events = get_conflict_feed(region=region_override, date_range=(start_date, end_date))
        file_date = start_date
    else:
        events = get_conflict_feed(region=region_override)
        file_date = date.today().isoformat()
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


