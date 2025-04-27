from datetime import date
import requests, csv, io, gzip, json

BASE = "https://api.gdeltproject.org/api/v2/events/search"

def fetch(keyword: str = "conflict", maxrows: int = 250):
    params = {
        "query": keyword,
        "format": "JSON",
        "maxrecords": maxrows,
        "sort": "HybridRel"
    }
    resp = requests.get(BASE, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["features"]

def normalize(raw):
    norm = []
    for item in raw:
        props = item["properties"]
        norm.append({
            "source": "gdelt",
            "event_date": props["date"],
            "actor1": props["actor1"],
            "actor2": props["actor2"],
            "summary": props["eventcontext"],
            "lat": props.get("latitude"),
            "lon": props.get("longitude"),
            "fatalities": None  # not provided
        })
    return norm 