"""Conflict agent for pulling ACLED data and flagging events."""

import os
import requests  # type: ignore
import json
from core.guardrails import pii_filter
from typing import Optional, Tuple, List, Dict, Any, cast
from datetime import date

def get_conflict_feed(limit: int = 100,
                      region: Optional[str] = None,
                      date_range: Optional[Tuple[str, str]] = None) -> List[Dict[str, Any]]:
    """Fetch conflict feed from ACLED with optional region and date range."""
    # Default to today's date if no date_range provided
    if date_range is None:
        today_str = date.today().isoformat()
        date_range = (today_str, today_str)
    api_key = os.getenv("ACLED_API_KEY")
    if not api_key:
        raise EnvironmentError("ACLED_API_KEY not set in environment")
    url = "https://api.acleddata.com/acled/read"
    params = {"key": api_key, "limit": limit}
    if region:
        params["region"] = region
    # Apply date_range (start_date and end_date) for filtering
    if len(date_range) == 2:
        params["start_date"], params["end_date"] = date_range
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"ACLED API error: {resp.status_code}")
    payload = resp.json()
    data = payload.get("data", [])
    return cast(List[Dict[str, Any]], data)


def flag_event(event: Dict[str, Any], threshold: int = 10) -> Dict[str, Any]:
    """Flag events where fatalities exceed a threshold."""
    count = event.get("fatalities", 0)
    flagged = count >= threshold
    return {"flagged": flagged, "event": event}

def run() -> Dict[str, Any]:
    """Entrypoint for the conflict agent, with PII sanitization."""
    events = get_conflict_feed()
    flagged = [flag_event(e) for e in events]
    result: Dict[str, Any] = {"status": "success", "data": flagged}
    # Sanitize output for PII
    filtered = pii_filter(json.dumps(result))
    filtered_json = json.loads(filtered)
    return cast(Dict[str, Any], filtered_json)
