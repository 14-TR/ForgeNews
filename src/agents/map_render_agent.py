import json
from pathlib import Path
import pydeck as pdk
import logging

# Configure basic logging if needed when used as a module
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ─── Helper Functions ───────────────────────────────────────────────────────

def hex_to_rgba(hex_color: str, alpha: int = 180) -> list[int]:
    '''Convert #RRGGBB or #RGB to [r,g,b,alpha].'''
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c*2 for c in hex_color)
    if len(hex_color) != 6:
        # Use logging if configured externally
        # logging.warning(f"Invalid hex color format: '{hex_color}'. Using grey.")
        return [128, 128, 128, alpha] # Default to grey
    try:
        r, g, b = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
    except ValueError:
        # logging.warning(f"Could not parse hex color: '{hex_color}'. Using grey.")
        return [128, 128, 128, alpha] # Default to grey
    return [r, g, b, alpha]

# ─── Core Map Rendering Function ──────────────────────────────────────────

def render_hotspot_map(
    hotspot_events_by_type: dict[str, list[dict]],
    hotspot_id: str,
    output_dir: Path,
    config: dict
) -> bool:
    '''Renders a static PyDeck HexagonLayer map for a single hotspot's events.

    Args:
        hotspot_events_by_type: Dict mapping event type (str) to list of event dicts (each with 'lat', 'lon').
        hotspot_id: A unique identifier string for the hotspot (used in filename and layer IDs).
        output_dir: The directory (Path object) where the HTML map file should be saved.
        config: A dictionary containing rendering parameters:
            DEFAULT_RADIUS (int): Radius for hexagons in meters.
            DEFAULT_ELEVATION_SCALE (int): Scale factor for hexagon elevation.
            DEFAULT_PITCH (int): Initial map pitch.
            DEFAULT_MAP_STYLE (str): Mapbox style URL.
            DEFAULT_COLORS (dict): Mapping from event type string to hex color string.
            DEFAULT_ZOOM (int): Initial map zoom level.

    Returns:
        True if the map was generated and saved successfully, False otherwise.
    '''

    if not hotspot_events_by_type:
        logging.warning(f"No event data provided for hotspot {hotspot_id}. Cannot render map.")
        return False

    output_dir.mkdir(parents=True, exist_ok=True) # Ensure output dir exists

    # Extract config or use defaults
    radius = config.get("DEFAULT_RADIUS", 10000)
    elevation_scale = config.get("DEFAULT_ELEVATION_SCALE", 20)
    pitch = config.get("DEFAULT_PITCH", 40)
    map_style = config.get("DEFAULT_MAP_STYLE", "mapbox://styles/mapbox/dark-v10")
    default_colors = config.get("DEFAULT_COLORS", {"other": "#AAAAAA"})
    default_other_color = default_colors.get("other", "#AAAAAA")
    zoom = config.get("DEFAULT_ZOOM", 8)

    # ─── Build pydeck layers ──────────────────────────────────────────────
    layers = []
    all_lats = []
    all_lons = []
    for etype, evs in hotspot_events_by_type.items():
        if not evs: # Skip if no events for this type
            continue

        color_hex = default_colors.get(etype, default_other_color)
        rgba = hex_to_rgba(color_hex)
        layers.append(
            pdk.Layer(
                "HexagonLayer",
                data=evs,
                get_position="[lon, lat]",
                radius=radius,
                elevation_scale=elevation_scale,
                extruded=True,
                pickable=True,
                elevation_range=[0, 1_000], # Fixed elevation range for now
                get_fill_color=rgba[:3], # RGB
                opacity=rgba[3]/255.0,    # Alpha (0-1)
                auto_highlight=True,
                id=f"hex_{hotspot_id}_{etype}",
            )
        )
        # Collect coords for centering
        all_lats.extend([pt["lat"] for pt in evs])
        all_lons.extend([pt["lon"] for pt in evs])

    if not layers:
         logging.warning(f"No layers generated for hotspot {hotspot_id}. Skipping map.")
         return False

    # ─── Center map and create Deck ───────────────────────────────────
    if not all_lats or not all_lons:
        logging.warning(f"Could not determine center for hotspot {hotspot_id}. Skipping map.")
        return False

    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=pitch,
    )

    r = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style,
        tooltip={"html": "<b>Events:</b> {elevationValue}", "style": {"color": "white"}}, # Use elevationValue for HexLayer
    )

    # ─── Save map to HTML ──────────────────────────────────────────────
    map_filename = output_dir / f"{hotspot_id}_map.html"
    try:
        # Ensure filename is a string for pydeck
        r.to_html(str(map_filename), notebook_display=False, iframe_width='100%')
        logging.info(f"✅ Successfully generated map: {map_filename.name}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to save map {map_filename.name}: {e}")
        return False

# Example Usage (if run directly, though typically imported)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("Map Render Agent Module - Contains render_hotspot_map function.")
    # Example data structure:
    # example_events = {
    #     "battle": [{'lat': 10.0, 'lon': 20.0}, {'lat': 10.1, 'lon': 20.1}],
    #     "protest": [{'lat': 10.2, 'lon': 20.2}]
    # }
    # example_config = {
    #     "DEFAULT_RADIUS": 5000,
    #     "DEFAULT_ELEVATION_SCALE": 10,
    #     "DEFAULT_PITCH": 45,
    #     "DEFAULT_MAP_STYLE": "mapbox://styles/mapbox/light-v10",
    #     "DEFAULT_COLORS": {"battle": "#FF0000", "protest": "#FFFF00", "other": "#888888"},
    #     "DEFAULT_ZOOM": 9
    # }
    # example_output_dir = Path("./temp_maps")
    # success = render_hotspot_map(example_events, "example_hs_1", example_output_dir, example_config)
    # print(f"Example map generation successful: {success}") 