import requests, datetime

URL = "https://paperswithcode.com/api/v0/trending"

def fetch():
    data = requests.get(URL, timeout=20).json()
    return data

def normalize(raw):
    today = datetime.date.today().isoformat()
    out = []
    for paper in raw:
        out.append({
            "source": "paperswithcode",
            "date": today,
            "title": paper["title"],
            "url": paper["url"],
            "summary": paper.get("abstract", "")[:500]
        })
    return out 