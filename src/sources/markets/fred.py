import requests, os, datetime

URL = "https://api.stlouisfed.org/fred/series/observations"

def fetch(series_id="T10Y2Y"):
    params = {
        "series_id": series_id,
        "api_key": os.getenv("FRED_API_KEY"),
        "file_type": "json",
        "sort_order": "desc",
        "limit": 10
    }
    data = requests.get(URL, params=params, timeout=20).json()
    return data["observations"]

def normalize(raw):
    out = []
    for obs in raw:
        out.append({
            "source": "fred",
            "series": obs["series_id"],
            "date": obs["date"],
            "value": float(obs["value"]) if obs["value"] != "." else None
        })
    return out 