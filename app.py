import os
import json
from pathlib import Path

import pydeck as pdk
import streamlit as st

# — helper to convert hex to rgba with some opacity —
def hex_to_rgba(hex_color: str, alpha: int = 180) -> list[int]:
    """Convert hex color to RGBA list."""
    # Strip any whitespace and # symbol
    hex_color = hex_color.strip().lstrip("#")
    
    # Print debug info
    print(f"Converting hex color: #{hex_color} with alpha {alpha}")
    
    # Handle shorthand hex
    if len(hex_color) == 3:
        hex_color = "".join(c*2 for c in hex_color)
    
    # Validate hex length
    if len(hex_color) != 6:
        print(f"Invalid hex length {len(hex_color)}, using fallback grey")
        return [128, 128, 128, alpha]
    
    try:
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Print debug info
        print(f"Converted to RGBA: [{r}, {g}, {b}, {alpha}]")
        
        return [r, g, b, alpha]
    except ValueError as e:
        print(f"Error converting hex: {e}, using fallback grey")
        return [128, 128, 128, alpha]

# Helper function to generate color range from base color
def generate_color_range(base_rgba):
    """Generate a 6-color range from light to dark versions of the base color."""
    r, g, b, a = base_rgba
    
    # Create 6 colors from light to dark
    return [
        [min(255, int(r * 1.5)), min(255, int(g * 1.5)), min(255, int(b * 1.5))],  # Lightest
        [min(255, int(r * 1.2)), min(255, int(g * 1.2)), min(255, int(b * 1.2))],  # Lighter
        [r, g, b],  # Base color
        [int(r * 0.8), int(g * 0.8), int(b * 0.8)],  # Darker
        [int(r * 0.6), int(g * 0.6), int(b * 0.6)],  # Darker still
        [int(r * 0.4), int(g * 0.4), int(b * 0.4)]   # Darkest
    ]

st.set_page_config(
    page_title="Conflict Hotspots Explorer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌐 Conflict Hotspots Explorer")
st.markdown("Adjust the sliders & pickers on the left to explore conflict events in 3D.")

# — locate your data —
ROOT = Path(__file__).resolve().parent
insights_dir = ROOT / "data" / "processed" / "insights"
raw_dir = ROOT / "data" / "raw"

def load_and_group():
    # load latest insights
    if not insights_dir.exists():
        return None, f"❌ Insights dir not found: {insights_dir}"
    ins_files = sorted(insights_dir.glob("conflict_insights_*.json"), reverse=True)
    if not ins_files:
        return None, "❌ No `conflict_insights_*.json` in insights."
    try:
        insight = json.loads(ins_files[0].read_text(encoding="utf-8"))
    except Exception as e:
        return None, f"❌ Failed to read insights file: {e}"

    # group raw events by event_type
    if not raw_dir.exists():
        return None, f"❌ Raw data dir not found: {raw_dir}"

    events: dict[str, list[dict]] = {}
    processed, skipped = 0, 0
    hotspots = insight.get("hotspots", [])[:3]
    if not hotspots:
        return {}, "⚠️ No hotspots in latest insights."

    for hs in hotspots:
        src_fn = hs.get("source_file", "")
        if not src_fn:
            skipped += 1
            continue
        src = raw_dir / src_fn
        if not src.exists():
            skipped += 1
            continue
        try:
            raw = json.loads(src.read_text(encoding="utf-8"))
            recs = raw.get("data") if isinstance(raw, dict) else raw
            if not isinstance(recs, list):
                continue
            for ev in recs:
                if not isinstance(ev, dict):
                    skipped += 1
                    continue
                try:
                    lat = float(ev["latitude"])
                    lon = float(ev["longitude"])
                    et = ev.get("event_type", "unknown").lower().replace(" ", "_")
                    events.setdefault(et, []).append({"lat": lat, "lon": lon})
                    processed += 1
                except Exception:
                    skipped += 1
                    continue
        except Exception:
            skipped += 1
            continue

    msg = f"✅ Loaded {processed} events"
    if skipped:
        msg += f", skipped {skipped} bad entries."
    if not events:
        msg += " ⚠️ No valid events found."

    # sort for consistency
    return {k: events[k] for k in sorted(events)}, msg

events_by_type, status = load_and_group()
st.sidebar.caption(status)

if not events_by_type:
    st.info("No data to display.")
    st.stop()

# default colors
default_hex = {
    "battles": "#FF0000",
    "protests_riots": "#00FF00",
    "violence_attacks": "#0080FF",
    "other": "#CCCCCC",
    "unknown": "#888888",
}

# global map controls
st.sidebar.header("🔧 Map Controls")
radius = st.sidebar.slider("Hexagon Radius (m)", 1000, 50000, 20000, 1000)
elevation_scale = st.sidebar.slider("Elevation Scale", 1, 200, 50, 1)

st.sidebar.markdown("---")
st.sidebar.header("🎨 Event Layers")

# Initialize session state for colors if not exists
if 'layer_colors' not in st.session_state:
    st.session_state.layer_colors = {}

# per-layer visibility + color
layer_settings: dict[str, dict] = {}
for etype in events_by_type:
    label = etype.replace("_", " ").title()
    
    # Create an expander for each layer's settings
    with st.sidebar.expander(f"🎨 {label} Settings"):
        # Visibility checkbox
        vis = st.checkbox("Show Layer", True, key=f"vis_{etype}")
        
        # Color picker for base color
        current_color = st.session_state.layer_colors.get(etype, default_hex.get(etype, "#CCCCCC"))
        col = st.color_picker("Base Color", current_color, key=f"col_{etype}")
        
        # Intensity controls
        intensity = st.slider("Color Intensity", 0.0, 1.0, 0.8, 0.1, key=f"intensity_{etype}")
        
        # Range controls
        min_height = st.number_input("Min Value", 0, 1000, 0, key=f"min_{etype}")
        max_height = st.number_input("Max Value", 0, 1000, 100, key=f"max_{etype}")
        
        # Scale type selector
        scale_type = st.selectbox(
            "Color Scale",
            ["quantize", "quantile", "linear"],
            key=f"scale_{etype}"
        )
    
    # Check if color changed
    if col != current_color:
        print(f"Color changed for {etype}: {current_color} -> {col}")
        st.session_state.layer_colors[etype] = col
        st.rerun()
    
    # Convert color and store settings
    rgba = hex_to_rgba(col)
    layer_settings[etype] = {
        "visible": vis,
        "color": rgba,
        "intensity": intensity,
        "color_domain": [min_height, max_height],
        "scale_type": scale_type
    }

# Add a manual refresh button
if st.sidebar.button("🔄 Refresh Map"):
    st.rerun()

# build pydeck layers
layers = []
for etype, evs in events_by_type.items():
    cfg = layer_settings[etype]
    if not cfg["visible"]:
        continue
    
    rgba = cfg["color"]
    print(f"Creating layer for {etype} with color: {rgba}")
    
    # Create a unique key for this layer
    layer_key = f"hex_{etype}_{hash(str(rgba))}"
    
    layer = pdk.Layer(
        "HexagonLayer",
        id=layer_key,
        data=evs,
        get_position="[lon, lat]",
        radius=radius,
        elevation_scale=elevation_scale,
        extruded=True,
        elevation_range=[0, 1000],
        pickable=True,
        # Color controls using settings
        color_range=generate_color_range(rgba),
        color_domain=cfg["color_domain"],
        color_scale_type=cfg["scale_type"],
        opacity=cfg["intensity"],
        auto_highlight=True,
    )
    layers.append(layer)

# render map with a unique key
if layers:
    all_lats = [e["lat"] for evs in events_by_type.values() for e in evs]
    all_lons = [e["lon"] for evs in events_by_type.values() for e in evs]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=2, pitch=40)
    
    # Create deck with unique key based on colors
    deck_key = hash(str(st.session_state.layer_colors))
    r = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"html": "<b>Events in area:</b> {elevationValue}", "style": {"color": "white"}},
    )
    
    # Render with unique key
    st.pydeck_chart(r, use_container_width=True, key=f"map_{deck_key}")
    
    total = sum(len(v) for v in events_by_type.values())
    shown = sum(len(events_by_type[k]) for k, s in layer_settings.items() if s["visible"])
    count = sum(s["visible"] for s in layer_settings.values())
    st.sidebar.success(f"Showing {shown:,}/{total:,} events across {count} layers")
else:
    st.info("No layers selected.") 
