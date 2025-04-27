import os
import requests
from src.scoring.scorer import score_insight

API_BASE = "https://api.acleddata.com/acled/read"

def fetch(start_date=None, end_date=None, country=None, event_type=None):
    """Fetch ACLED conflict data with optional filters."""
    params = {
        "api_key": os.getenv("ACLED_API_KEY"),
        "email": os.getenv("ACLED_EMAIL"),
        "limit": 500,
        "format": "json"
    }
    
    # Add optional filters if provided
    if start_date:
        params["event_date"] = start_date
    if end_date:
        params["event_date_end"] = end_date
    if country:
        params["country"] = country
    if event_type:
        params["event_type"] = event_type
    
    response = requests.get(API_BASE, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["data"]

def normalize(raw):
    """Normalize ACLED data to standard format."""
    normalized = []
    for event in raw:
        headline = f"{event['actor1']} - {event['actor2']} conflict"
        summary = event["notes"]
        normalized.append(score_insight({
            "domain": "conflict",
            "title": headline,
            "body": summary,
            "source_id": "acled",
            "event_date": event["event_date"],
            "actor1": event["actor1"],
            "actor2": event["actor2"],
            "lat": event["latitude"],
            "lon": event["longitude"],
            "fatalities": event["fatalities"]
        }))
    return normalized 