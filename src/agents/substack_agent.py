#!/usr/bin/env python3
import os
import sys
# Ensure project root and src directory are on PYTHONPATH for direct execution
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(1, os.path.join(root_dir, 'src'))
"""
Substack agent: generates a newsletter article from conflict summary data.
"""
from datetime import datetime
from typing import Dict, Any
from agents.report_agent import get_summary


def generate_article(summary: Dict[str, Any]) -> str:
    period = summary.get("period", "N/A")
    title = f"Conflict Report: {period}"
    lines = [f"# {title}",
             "",  # blank line
             "This newsletter provides an overview of the latest conflict events based on available data.",
             ""]
    for item in summary.get("summary", []):
        lines.append(f"- **{item['type']}**: {item['count']} events, {item['fatalities']} fatalities")
    lines.extend(["", "Stay informed with ForgeNews for daily updates."])
    return "\n".join(lines)


def run() -> Dict[str, Any]:
    """Entrypoint for generating a Substack markdown article."""
    # Get the summary for the most recent period (daily)
    summary = get_summary("daily")
    article_md = generate_article(summary)

    # Ensure output directory exists
    output_dir = os.path.join(os.getcwd(), "newsletters")
    os.makedirs(output_dir, exist_ok=True)

    # Filename with UTC date
    filename = f"substack_{datetime.utcnow().strftime('%Y%m%d')}.md"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(article_md)

    # Return status plus article and file path
    return {"status": "success", "article": article_md, "output_file": filepath} 