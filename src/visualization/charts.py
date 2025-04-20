#!/usr/bin/env python3
"""
Visualization module for ForgeNews.
Provides functions to generate charts and maps from conflict data.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import os
from pathlib import Path
import folium
from folium.plugins import HeatMap
from datetime import datetime
import json

# Set matplotlib style for consistent, professional visualizations
plt.style.use('ggplot')

# Create directories
def ensure_dirs():
    """Ensure all required directories exist."""
    dirs = [
        os.path.join("data", "processed", "insights"),
        os.path.join("data", "visualizations", "charts"),
        os.path.join("data", "visualizations", "maps")
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def event_type_distribution_chart(event_type_summary: Dict[str, Dict[str, Any]], 
                                 title: str = "Event Type Distribution") -> str:
    """
    Create a bar chart showing distribution of event types.
    
    Args:
        event_type_summary: Dictionary of event types with their stats
        title: Chart title
        
    Returns:
        Path to saved chart image
    """
    ensure_dirs()
    
    # Extract data
    types = list(event_type_summary.keys())
    counts = [data.get('count', 0) for data in event_type_summary.values()]
    
    # Sort by count in descending order
    sorted_data = sorted(zip(types, counts), key=lambda x: x[1], reverse=True)
    types = [x[0] for x in sorted_data]
    counts = [x[1] for x in sorted_data]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Create horizontal bar chart
    bars = plt.barh(types, counts, color='steelblue')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                 f'{int(width)}', ha='left', va='center')
    
    # Set title and labels
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Number of Events', fontsize=12)
    plt.tight_layout()
    
    # Save chart
    chart_path = os.path.join("data", "visualizations", "charts", f"event_type_distribution_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def fatalities_by_country_chart(country_profiles: Dict[str, Dict[str, Any]], 
                               title: str = "Fatalities by Country") -> str:
    """
    Create a bar chart showing fatalities by country.
    
    Args:
        country_profiles: Dictionary of country profiles with fatality data
        title: Chart title
        
    Returns:
        Path to saved chart image
    """
    ensure_dirs()
    
    # Extract data
    countries = list(country_profiles.keys())
    fatalities = [profile.get('fatalities', 0) for profile in country_profiles.values()]
    
    # Sort by fatalities in descending order
    sorted_data = sorted(zip(countries, fatalities), key=lambda x: x[1], reverse=True)
    countries = [x[0] for x in sorted_data[:10]]  # Top 10 countries
    fatalities = [x[1] for x in sorted_data[:10]]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Create horizontal bar chart
    bars = plt.barh(countries, fatalities, color='firebrick')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                 f'{int(width)}', ha='left', va='center')
    
    # Set title and labels
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Number of Fatalities', fontsize=12)
    plt.tight_layout()
    
    # Save chart
    chart_path = os.path.join("data", "visualizations", "charts", f"fatalities_by_country_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def fatalities_by_event_type_chart(event_type_summary: Dict[str, Dict[str, Any]], 
                                  title: str = "Fatalities by Event Type") -> str:
    """
    Create a bar chart showing fatalities by event type.
    
    Args:
        event_type_summary: Dictionary of event types with their stats
        title: Chart title
        
    Returns:
        Path to saved chart image
    """
    ensure_dirs()
    
    # Extract data
    types = list(event_type_summary.keys())
    fatalities = [data.get('fatalities', 0) for data in event_type_summary.values()]
    
    # Sort by fatalities in descending order
    sorted_data = sorted(zip(types, fatalities), key=lambda x: x[1], reverse=True)
    types = [x[0] for x in sorted_data]
    fatalities = [x[1] for x in sorted_data]
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Create horizontal bar chart
    bars = plt.barh(types, fatalities, color='darkred')
    
    # Add data labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                 f'{int(width)}', ha='left', va='center')
    
    # Set title and labels
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Number of Fatalities', fontsize=12)
    plt.tight_layout()
    
    # Save chart
    chart_path = os.path.join("data", "visualizations", "charts", f"fatalities_by_event_type_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def top_hotspots_chart(hotspots: List[Dict[str, Any]], 
                      title: str = "Top Conflict Hotspots") -> str:
    """
    Create a horizontal bar chart showing top hotspots.
    
    Args:
        hotspots: List of hotspot dictionaries
        title: Chart title
        
    Returns:
        Path to saved chart image
    """
    ensure_dirs()
    
    # Extract data (top 10 hotspots max)
    data = hotspots[:10]
    locations = [f"{h.get('location')}, {h.get('country')}" for h in data]
    events = [h.get('count', 0) for h in data]
    fatalities = [h.get('fatalities', 0) for h in data]
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Sort by events count
    sorted_indices = sorted(range(len(events)), key=lambda i: events[i], reverse=True)
    locations = [locations[i] for i in sorted_indices]
    events = [events[i] for i in sorted_indices]
    fatalities = [fatalities[i] for i in sorted_indices]
    
    # Create stacked bar chart
    y_pos = np.arange(len(locations))
    
    plt.barh(y_pos, events, align='center', alpha=0.7, color='steelblue', label='Events')
    plt.barh(y_pos, fatalities, align='center', alpha=0.7, color='darkred', label='Fatalities')
    
    plt.yticks(y_pos, locations)
    plt.xlabel('Count')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend()
    
    plt.tight_layout()
    
    # Save chart
    chart_path = os.path.join("data", "visualizations", "charts", f"top_hotspots_{datetime.now().strftime('%Y%m%d')}.png")
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return chart_path

def generate_heatmap(events: List[Dict[str, Any]], title: str = "Conflict Events Heatmap") -> str:
    """
    Generate a Folium heatmap from conflict events.
    
    Args:
        events: List of conflict events with lat/long data
        title: Map title
        
    Returns:
        Path to saved HTML map
    """
    ensure_dirs()
    
    # Extract coordinates and weight by fatalities (or 1 if no fatalities)
    heat_data = []
    for event in events:
        lat = event.get('latitude')
        lon = event.get('longitude')
        fatalities = event.get('fatalities', 1)
        
        if lat is not None and lon is not None:
            try:
                lat_float = float(lat)
                lon_float = float(lon)
                if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                    weight = max(1, fatalities)  # Minimum weight of 1
                    heat_data.append([lat_float, lon_float, weight])
            except (ValueError, TypeError):
                continue
    
    if not heat_data:
        print("No valid coordinates found for heatmap")
        return ""
    
    # Create base map centered at the mean of coordinates
    avg_lat = sum(row[0] for row in heat_data) / len(heat_data)
    avg_lon = sum(row[1] for row in heat_data) / len(heat_data)
    
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=4, tiles='CartoDB positron')
    
    # Add title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>{title}</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=10, gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}).add_to(m)
    
    # Save to HTML file
    map_path = os.path.join("data", "visualizations", "maps", f"conflict_heatmap_{datetime.now().strftime('%Y%m%d')}.html")
    m.save(map_path)
    
    return map_path

def generate_event_type_maps(events: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate a separate map for each event type.
    
    Args:
        events: List of conflict events
        
    Returns:
        Dict mapping event types to their map file paths
    """
    ensure_dirs()
    
    # Group events by type
    events_by_type = {}
    for event in events:
        event_type = event.get('event_type')
        if event_type:
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append(event)
    
    # Generate a map for each event type
    map_paths = {}
    for event_type, type_events in events_by_type.items():
        map_path = os.path.join("data", "visualizations", "maps", f"{event_type.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.html")
        
        # Extract coordinates
        points = []
        for event in type_events:
            lat = event.get('latitude')
            lon = event.get('longitude')
            fatalities = event.get('fatalities', 0)
            location = event.get('location', 'Unknown')
            notes = event.get('notes', '')
            date = event.get('event_date', '')
            
            if lat is not None and lon is not None:
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                        points.append({
                            'lat': lat_float, 
                            'lon': lon_float,
                            'fatalities': fatalities,
                            'location': location,
                            'notes': notes[:100] + '...' if len(notes) > 100 else notes,
                            'date': date
                        })
                except (ValueError, TypeError):
                    continue
        
        if not points:
            continue
        
        # Create base map centered at the mean of coordinates
        avg_lat = sum(p['lat'] for p in points) / len(points)
        avg_lon = sum(p['lon'] for p in points) / len(points)
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=4, tiles='CartoDB positron')
        
        # Add title
        title_html = f'''
            <h3 align="center" style="font-size:16px"><b>{event_type} Events</b></h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Add markers
        for point in points:
            # Scale marker size by fatalities
            radius = 6
            if point['fatalities'] > 0:
                radius = min(10, 6 + point['fatalities'] / 2)
                
            popup_text = f"""
            <b>{point['location']}</b><br>
            Date: {point['date']}<br>
            Fatalities: {point['fatalities']}<br>
            {point['notes']}
            """
            
            folium.CircleMarker(
                location=[point['lat'], point['lon']],
                radius=radius,
                popup=popup_text,
                color='red',
                fill=True,
                fill_color='red'
            ).add_to(m)
        
        # Save map
        m.save(map_path)
        map_paths[event_type] = map_path
    
    return map_paths

def generate_all_charts(insights: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Generate all charts and maps for the insights.
    
    Args:
        insights: Complete insights dictionary
        
    Returns:
        Dictionary of visualization paths by type
    """
    visualization_paths = {
        'charts': {},
        'event_type_maps': {},
        'heatmap': None
    }
    
    # Generate charts
    if 'event_type_summary' in insights:
        visualization_paths['charts']['event_type_distribution'] = event_type_distribution_chart(
            insights['event_type_summary']
        )
    
    if 'country_profiles' in insights:
        visualization_paths['charts']['fatalities_by_country'] = fatalities_by_country_chart(
            insights['country_profiles']
        )
    
    if 'event_type_summary' in insights:
        visualization_paths['charts']['fatalities_by_event_type'] = fatalities_by_event_type_chart(
            insights['event_type_summary']
        )
    
    if 'hotspots' in insights and insights['hotspots']:
        visualization_paths['charts']['top_hotspots'] = top_hotspots_chart(
            insights['hotspots']
        )
    
    # Generate maps if we have events
    if 'events' in insights and insights['events']:
        # Generate heatmap
        visualization_paths['heatmap'] = generate_heatmap(insights['events'])
        
        # Generate event type maps
        visualization_paths['event_type_maps'] = generate_event_type_maps(insights['events'])
    
    return visualization_paths 