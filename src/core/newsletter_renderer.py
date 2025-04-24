import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Define the path to the insights directory relative to the project root
INSIGHTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "insights"

def find_latest_insight_file() -> Optional[Path]:
    """Finds the most recent conflict_insights_*.json file."""
    if not INSIGHTS_DIR.exists():
        print(f"Error: Insights directory not found at {INSIGHTS_DIR}")
        return None
    
    try:
        insight_files = list(INSIGHTS_DIR.glob("conflict_insights_*.json"))
        if not insight_files:
            print("Error: No insight files found.")
            return None
        
        # Sort by filename (assumes YYYYMMDD format) in descending order
        latest_file = max(insight_files, key=lambda f: f.name)
        print(f"Found latest insight file: {latest_file}")
        return latest_file
    except Exception as e:
        print(f"Error finding latest insight file: {e}")
        return None

def render_latest_insights_html() -> Optional[str]:
    """Loads the latest insights JSON and renders it as a simple HTML string."""
    latest_file = find_latest_insight_file()
    if not latest_file:
        return "<p>Error: Could not find the latest insight file.</p>"

    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading or parsing insight file {latest_file}: {e}")
        return f"<p>Error: Could not load or parse insight file {latest_file}.</p>"

    # --- Start HTML Rendering --- 
    # Basic styling for readability - Substack might override some of this
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Conflict Insights: {latest_file.stem.split('_')[-1]}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; margin: 20px; }}
        h1, h2 {{ border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 10px; }}
        .summary p {{ margin-bottom: 15px; }}
        .hotspot-item {{ margin-bottom: 15px; border-left: 3px solid #ccc; padding-left: 10px; }}
        .signal-event {{ background-color: #f9f9f9; border: 1px solid #eee; padding: 10px; margin-bottom: 10px; }}
    </style>
</head>
<body>
"""

    report_date = latest_file.stem.split('_')[-1]
    html += f"<h1>Conflict Insights Summary - {report_date}</h1>"

    # Overall Summary Section
    summary = data.get('summary', {})
    html += "<div class='summary'>"
    html += f"<h2>Overall Assessment</h2>"
    html += f"<p><strong>Escalation Status:</strong> {'Escalating' if summary.get('is_escalating') else 'Not Escalating'}</p>"
    html += f"<p><strong>Key Trend:</strong> {summary.get('trend_description', 'N/A')}</p>"
    html += f"<p><strong>Confidence Score:</strong> {summary.get('overall_confidence', 'N/A'):.2f}</p>"
    html += f"<p><strong>Total Events Analyzed:</strong> {data.get('total_events', 'N/A')}</p>"
    html += f"<p><strong>Total Fatalities Reported:</strong> {data.get('total_fatalities', 'N/A')}</p>"
    html += "</div>"

    # Hotspots Section
    hotspots = data.get('hotspots', [])
    if hotspots:
        html += "<h2>Key Hotspots</h2>"
        html += "<ul>"
        for spot in hotspots:
            html += f"<li class='hotspot-item'>"
            html += f"<strong>Location:</strong> {spot.get('location', 'N/A')} <br>"
            html += f"<strong>Reason:</strong> {spot.get('reasoning', 'N/A')} <br>"
            html += f"<strong>Severity:</strong> {spot.get('severity_score', 'N/A'):.2f}<br>"
            related_events = spot.get('related_event_ids', [])
            html += f"<strong>Related Event Count:</strong> {len(related_events)}"
            html += "</li>"
        html += "</ul>"

    # High Signal Events Section
    signal_analysis = data.get('signal_analysis', {})
    high_signal_events = signal_analysis.get('high_signal_events', [])
    if high_signal_events:
        html += "<h2>High Signal Events</h2>"
        html += "<div>"
        for event in high_signal_events:
            html += "<div class='signal-event'>"
            html += f"<strong>Event ID:</strong> {event.get('event_id', 'N/A')} <br>"
            html += f"<strong>Description:</strong> {event.get('description', 'N/A')} <br>"
            html += f"<strong>Location:</strong> {event.get('location', {}).get('location_name', 'N/A')} <br>"
            html += f"<strong>Reason for High Signal:</strong> {event.get('reasoning', 'N/A')}<br>"
            html += f"<strong>Signal Score:</strong> {event.get('signal_score', 'N/A'):.2f}"
            html += "</div>"
        html += "</div>"
    
    # Emerging Trends (if available)
    emerging_trends = data.get('emerging_trends', [])
    if emerging_trends:
        html += "<h2>Emerging Trends</h2>"
        html += "<ul>"
        for trend in emerging_trends:
            html += f"<li>{trend.get('description', 'N/A')} (Confidence: {trend.get('confidence', 'N/A'):.2f})</li>"
        html += "</ul>"

    html += "</body></html>"
    return html

if __name__ == '__main__':
    # Example usage: Render the latest insights and print to console
    # Ensure you have a file like data/processed/insights/conflict_insights_YYYYMMDD.json
    print("Attempting to render latest insights...")
    rendered_html = render_latest_insights_html()
    if rendered_html:
        print("\n--- Rendered HTML --- ")
        # print(rendered_html) # Uncomment to see full HTML
        # Save to a file for easier viewing
        output_path = Path(__file__).resolve().parent.parent.parent / "reports" / "latest_newsletter_preview.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print(f"\nPreview saved to: {output_path}")
    else:
        print("Failed to render HTML.") 