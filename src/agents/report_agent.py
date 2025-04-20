#!/usr/bin/env python3
import sqlite3
from datetime import date, timedelta
from typing import Dict, Any
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "db", "conflict_data.db")

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
    conn.close()

    return {
        "period": f"{start.isoformat()} to {end.isoformat()}",
        "summary": [{"type": r[0], "count": r[1], "fatalities": r[2]} for r in rows],
        "top_locations": [{"location": r[0], "count": r[1]} for r in loc_rows]
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