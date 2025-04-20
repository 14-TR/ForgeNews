#!/usr/bin/env python3
import sqlite3
from datetime import date, timedelta
from typing import Dict, Any
import os
import sys
import json

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Update path to use proper module paths
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "conflict_data.db")

def get_summary(period: str = "daily") -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Determine reference date as the most recent event_date in the DB
    cursor.execute("SELECT MAX(event_date) FROM conflict_events")
    row = cursor.fetchone()
    if row and row[0]:
        reference_date = date.fromisoformat(row[0])
    else:
        reference_date = date.today()

    if period == "daily":
        start = end = reference_date
    elif period == "weekly":
        start = reference_date - timedelta(days=7)
        end = reference_date
    elif period == "monthly":
        start = reference_date.replace(day=1)
        end = reference_date
    else:
        raise ValueError(f"Invalid period: {period}")

    cursor.execute(
        """
        SELECT event_type, COUNT(*), IFNULL(SUM(fatalities),0)
        FROM conflict_events
        WHERE event_date BETWEEN ? AND ?
        GROUP BY event_type;
        """,
        (start.isoformat(), end.isoformat()),
    )
    rows = cursor.fetchall()
    # Fetch top 5 locations by event count
    cursor.execute(
        """
        SELECT city, COUNT(*)
        FROM conflict_events
        WHERE event_date BETWEEN ? AND ?
        GROUP BY city
        ORDER BY COUNT(*) DESC
        LIMIT 5;
        """,
        (start.isoformat(), end.isoformat()),
    )
    loc_rows = cursor.fetchall()
    # Gather top locations per event type
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT event_type, city, COUNT(*) as cnt
        FROM conflict_events
        WHERE event_date BETWEEN ? AND ?
        GROUP BY event_type, city
        ORDER BY event_type ASC, cnt DESC;
        """,
        (start.isoformat(), end.isoformat()),
    )
    loc_by_type_rows = cursor.fetchall()
    # Build a mapping of event type to top locations
    locations_by_type = {}
    for etype, city, cnt in loc_by_type_rows:
        locations_by_type.setdefault(etype, []).append({"location": city, "count": cnt})
    # Keep only top 2 locations per type
    for etype in locations_by_type:
        locations_by_type[etype] = locations_by_type[etype][:2]

    # Gather top countries per event type
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT event_type, country, COUNT(*) as cnt
        FROM conflict_events
        WHERE event_date BETWEEN ? AND ?
        GROUP BY event_type, country
        ORDER BY event_type ASC, cnt DESC;
        """,
        (start.isoformat(), end.isoformat()),
    )
    country_by_type_rows = cursor.fetchall()
    countries_by_type = {}
    for etype, country, cnt in country_by_type_rows:
        countries_by_type.setdefault(etype, []).append({"country": country, "count": cnt})
    # Keep only top 2 countries per type
    for etype in countries_by_type:
        countries_by_type[etype] = countries_by_type[etype][:2]

    # Gather overall top countries
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT country, COUNT(*) as cnt
        FROM conflict_events
        WHERE event_date BETWEEN ? AND ?
        GROUP BY country
        ORDER BY cnt DESC
        LIMIT 5;
        """,
        (start.isoformat(), end.isoformat()),
    )
    country_rows = cursor.fetchall()
    top_countries = [{"country": r[0], "count": r[1]} for r in country_rows]

    conn.close()

    # Rank event types by fatalities and build enriched summary entries
    rows_sorted = sorted(rows, key=lambda r: r[2], reverse=True)
    summary_items = []
    for rank, (etype, count, fatalities) in enumerate(rows_sorted, start=1):
        summary_items.append({
            "type": etype,
            "count": count,
            "fatalities": fatalities,
            "importance_rank": rank,
            "top_locations": locations_by_type.get(etype, []),
            "top_countries": countries_by_type.get(etype, [])
        })
    # Identify top priority events (highest severity by fatalities)
    priority_events = summary_items[:3]

    return {
        "period": f"{start.isoformat()} to {end.isoformat()}",
        "summary": summary_items,
        "priority_events": priority_events,
        "top_locations": [{"location": r[0], "count": r[1]} for r in loc_rows],
        "top_countries": top_countries,
        "locations_by_type": locations_by_type,
        "countries_by_type": countries_by_type
    }

def run() -> Dict[str, Any]:
    """Entrypoint for the report_agent"""
    summary = get_summary("daily")
    # Persist summary to JSON for downstream agents
    processed_dir = os.path.join(os.getcwd(), "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    period_key = summary["period"].replace(" to ", "_to_")
    filepath = os.path.join(processed_dir, f"summary_{period_key}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary 