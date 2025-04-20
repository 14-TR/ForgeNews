import sqlite3
import os
from typing import Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "conflict_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conflict_events (
            id TEXT PRIMARY KEY,
            event_date TEXT,
            event_type TEXT,
            sub_event_type TEXT,
            actor1 TEXT,
            actor2 TEXT,
            assoc_actor_1 TEXT,
            assoc_actor_2 TEXT,
            fatalities INTEGER,
            region TEXT,
            country TEXT,
            admin1 TEXT,
            admin2 TEXT,
            city TEXT,
            lat REAL,
            lon REAL,
            source TEXT,
            description TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def insert_event(event: Dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO conflict_events (
            id, event_date, event_type, sub_event_type, actor1, actor2,
            assoc_actor_1, assoc_actor_2, fatalities, region, country,
            admin1, admin2, city, lat, lon, source, description, tags
        ) VALUES (
            :event_id_cnty, :event_date, :event_type, :sub_event_type, :actor1, :actor2,
            :assoc_actor_1, :assoc_actor_2, :fatalities, :region, :country,
            :admin1, :admin2, :location, :latitude, :longitude, :source, :notes, :tags
        );
    """, event)
    conn.commit()
    conn.close() 