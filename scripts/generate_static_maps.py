import os
import json
from pathlib import Path
# import pydeck as pdk # No longer needed directly here
import logging

# Import the rendering function from the agent
# Assuming src is importable from scripts/, adjust sys.path if necessary
from src.agents.map_render_agent import render_hotspot_map

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ─── Configuration ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent # Project root is parent of scripts/
insights_dir = ROOT / "data" / "processed" / "insights"
raw_dir      = ROOT / "data" / "raw"
output_dir   = ROOT / "reports" / "maps"
output_dir.mkdir(parents=True, exist_ok=True) # Ensure output dir exists

# Map Generation Config (to be passed to the agent)
MAP_CONFIG = {
    "DEFAULT_RADIUS": 10000,  # meters
    "DEFAULT_ELEVATION_SCALE": 20,
    "DEFAULT_PITCH": 40,
    "DEFAULT_MAP_STYLE": "mapbox://styles/mapbox/dark-v10",
    "DEFAULT_COLORS": {
        "battle": "#FF0000",
        "protest": "#00FF00",
        "attack": "#0000FF",
        "other": "#AAAAAA",
    },
    "DEFAULT_ZOOM": 8 # Zoom level for individual hotspot maps
}

MAX_HOTSPOTS_TO_MAP = 5 # Limit number of maps generated

# ─── Main Script Logic ───────────────────────────────────────────────────────

def generate_maps():
    logging.info("Starting static map generation process.")

    # ─── Load latest insights ───────────────────────────────────────────────
    ins_files = sorted(insights_dir.glob("conflict_insights_*.json"), reverse=True)
    if not ins_files:
        logging.error(f"❌ No insight files found in {insights_dir}")
        return

    latest_insight_file = ins_files[0]
    logging.info(f"Loading insights from: {latest_insight_file.name}")
    try:
        insight = json.loads(latest_insight_file.read_text(encoding='utf-8'))
    except Exception as e:
        logging.error(f"❌ Error reading insights file {latest_insight_file.name}: {e}")
        return

    hotspots = insight.get("hotspots", [])
    if not hotspots:
        logging.warning("No hotspots found in the insight file.")
        return

    # ─── Process each hotspot ───────────────────────────────────────────────
    maps_generated = 0
    for i, hs in enumerate(hotspots):
        if maps_generated >= MAX_HOTSPOTS_TO_MAP:
            logging.info(f"Reached maximum map limit ({MAX_HOTSPOTS_TO_MAP}). Stopping.")
            break

        hotspot_id = hs.get("hotspot_id", f"hotspot_{i+1}")
        logging.info(f"Processing hotspot: {hotspot_id}")

        src_filename = hs.get("source_file", "")
        if not src_filename:
            logging.warning(f"Skipping hotspot {hotspot_id}: No source file linked.")
            continue

        src = raw_dir / src_filename
        if not src.exists():
            logging.warning(f"Skipping hotspot {hotspot_id}: Source file not found at {src}")
            continue

        # ─── Group events for this hotspot ───────────────────────────────
        hotspot_events_by_type: dict[str, list[dict]] = {}
        try:
            data = json.loads(src.read_text(encoding='utf-8'))
            raw_event_list = data.get("data") if isinstance(data, dict) else data
            if not isinstance(raw_event_list, list):
                 logging.warning(f"Skipping hotspot {hotspot_id}: Event data in '{src.name}' is not a list.")
                 continue

            processed_count = 0
            for ev in raw_event_list:
                if not isinstance(ev, dict):
                    continue
                try:
                    lat = float(ev["latitude"])
                    lon = float(ev["longitude"])
                    # Simple classification based on event_type string
                    et_str = ev.get("event_type", "other").lower()
                    if "battle" in et_str: key = "battle"
                    elif "protest" in et_str or "riot" in et_str: key = "protest"
                    elif "attack" in et_str or "violence" in et_str or "explosion" in et_str: key = "attack"
                    else: key = "other"
                    hotspot_events_by_type.setdefault(key, []).append({"lat": lat, "lon": lon})
                    processed_count += 1
                except (KeyError, ValueError, TypeError):
                    continue # Skip invalid event entries silently for now
            logging.info(f"Processed {processed_count} events for hotspot {hotspot_id}.")

        except Exception as e:
             logging.error(f"Error processing file {src.name} for hotspot {hotspot_id}: {e}")
             continue

        if not hotspot_events_by_type:
            logging.warning(f"Skipping map for hotspot {hotspot_id}: No valid event coordinates found.")
            continue

        # ─── Call the Map Render Agent ────────────────────────────────────
        success = render_hotspot_map(
            hotspot_events_by_type=hotspot_events_by_type,
            hotspot_id=hotspot_id,
            output_dir=output_dir,
            config=MAP_CONFIG
        )

        if success:
            maps_generated += 1
        else:
            # Error is logged within the agent function
            # logging.error(f"Map generation failed for hotspot {hotspot_id}.")
            pass # Continue to next hotspot even if one fails

    logging.info(f"Map generation process finished. Generated {maps_generated} maps.")

if __name__ == "__main__":
    # If src is not in PYTHONPATH, you might need this:
    # import sys
    # sys.path.insert(0, str(ROOT))
    generate_maps() 