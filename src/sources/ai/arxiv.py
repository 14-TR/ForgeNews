import requests
import xml.etree.ElementTree as ET
import datetime

def fetch(category="cs.AI"):
    """Fetch arXiv RSS feed for a specific category."""
    url = f"https://export.arxiv.org/rss/{category}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text

def normalize(raw_xml):
    """Parse XML and normalize to consistent format."""
    root = ET.fromstring(raw_xml)
    items = root.findall(".//item")
    
    today = datetime.date.today().isoformat()
    results = []
    
    for item in items:
        title = item.find("title").text
        link = item.find("link").text
        description = item.find("description").text
        
        results.append({
            "source": "arxiv",
            "date": today,
            "title": title,
            "url": link,
            "summary": description[:500] if description else ""
        })
    
    return results 