#!/usr/bin/env python3
import os
import sys
# Ensure project root is on sys.path for aws_secret_mgt import
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(1, os.path.join(root_dir, 'src'))
"""
LLM Report Agent: expands summary into a narrative via OpenAI.
"""
from openai import OpenAI

from aws_secret_mgt import AWSSecretManager
from typing import Dict, Any
from enrichment.spatial import enrich_summary_file
import json
import glob

# Initialize AWS secret manager and load OpenAI API key
secret_manager = AWSSecretManager()
api_key = secret_manager.get_openai_api_key() or os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def run() -> Dict[str, Any]:
    """Entrypoint for generating a narrative report via LLM"""
    # Load the most recent summary JSON
    processed_dir = os.path.join(os.getcwd(), "data", "processed")
    pattern = os.path.join(processed_dir, "summary_*.json")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No summary JSON found in {processed_dir}")
    latest_file = max(files, key=os.path.getmtime)
    # Load raw summary and extract period
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_summary = json.load(f)
    period = raw_summary.get("period", "Unknown Period")

    # Enrich the summary file with geographic data
    period_key = period.replace(" to ", "_")
    enriched_file = os.path.join(processed_dir, f"enriched_summary_{period_key}.json")
    enrich_summary_file(latest_file, enriched_file)

    # Load enriched summary data for prompt building
    with open(enriched_file, "r", encoding="utf-8") as f:
        enriched_data = json.load(f)

    # Prepare top location and country data for the prompt
    loc_names = [loc.get("location") for loc in raw_summary.get("top_locations", [])]
    top_countries = raw_summary.get("top_countries", [])
    locations_by_type = raw_summary.get("locations_by_type", {})
    countries_by_type = raw_summary.get("countries_by_type", {})

    # Build a detailed prompt including overall hotspots and per-type breakdown
    prompt_lines = [
        "You are an expert conflict analyst. Produce a detailed narrative report based on the following summary.",
        f"Period: {period}",
        "",
        f"Top locations overall: {', '.join(loc_names)}",
        f"Top countries overall: {', '.join([c.get('country') for c in top_countries])}",
        "",
        "Locations by event type:",
    ]
    for etype, locs in locations_by_type.items():
        locs_str = ", ".join([f"{l['location']} ({l['count']} events)" for l in locs])
        prompt_lines.append(f"- {etype}: {locs_str}")
    prompt_lines.append("")
    prompt_lines.append("Countries by event type:")
    for etype, countries in countries_by_type.items():
        ctrs_str = ", ".join([f"{c['country']} ({c['count']} events)" for c in countries])
        prompt_lines.append(f"- {etype}: {ctrs_str}")
    prompt_lines.append("")
    prompt_lines.append("Summary of events (ordered by importance_rank, highest first):")

    # List each event type with its importance rank, counts, deaths, and top areas
    for item in sorted(enriched_data.get("summary", []), key=lambda x: x.get("importance_rank", 0)):
        rank = item.get("importance_rank")
        etype = item.get("type")
        count = item.get("count", 0)
        reported = item.get("reported_deaths", item.get("fatalities", 0))
        # Top locations and countries for this type
        type_locs = item.get("top_locations", [])
        type_ctrs = item.get("top_countries", [])
        locs_str = ", ".join([f"{l['location']} ({l['count']})" for l in type_locs]) if type_locs else None
        ctrs_str = ", ".join([f"{c['country']} ({c['count']})" for c in type_ctrs]) if type_ctrs else None
        parts = [f"Rank {rank}: {etype} ({count} events, {reported} reported deaths)"]
        if locs_str:
            parts.append(f"Locations: {locs_str}")
        if ctrs_str:
            parts.append(f"Countries: {ctrs_str}")
        prompt_lines.append(f"- {'; '.join(parts)}")

    prompt_lines.append("")
    prompt_lines.append("Please write a detailed report (~300 words), prioritizing the highest rank conflicts first.")

    prompt = "\n".join(prompt_lines)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an expert conflict analyst. Use the 'Top locations overall' list to highlight general hotspots, and the 'Locations by event type' section to mention at least one specific city for each event type in your narrative."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=600
    )
    report_text = response.choices[0].message.content

    # Save the report to file
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/report_{period.replace(' to ','_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    return {"status": "success", "report": report_text, "file": filename} 