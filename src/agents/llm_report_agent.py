#!/usr/bin/env python3
import os
import sys

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

"""
LLM Report Agent: expands summary into a narrative via OpenAI.
Incorporates comprehensive insights, maps, and charts for rich reporting.
"""
from openai import OpenAI
import base64
from pathlib import Path
from datetime import datetime

from aws_secret_mgt import AWSSecretManager
from typing import Dict, Any, List, Optional
from src.enrichment.spatial import enrich_summary_file
import json
import glob

# Initialize AWS secret manager and load OpenAI API key
secret_manager = AWSSecretManager()
api_key = secret_manager.get_openai_api_key() or os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def image_to_base64(image_path: str) -> Optional[str]:
    """Convert an image file to base64 encoding for embedding in Markdown."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image to base64: {str(e)}")
        return None

def embed_image_in_markdown(image_path: str, alt_text: str = "Visualization") -> str:
    """Create a Markdown image tag with embedded base64 data."""
    try:
        # Determine file extension
        file_ext = Path(image_path).suffix.lower()[1:]  # Remove the dot
        if file_ext not in ["png", "jpg", "jpeg", "gif"]:
            return f"[View {alt_text}]({image_path})"
            
        # Get base64 encoded image
        base64_image = image_to_base64(image_path)
        if not base64_image:
            return f"[View {alt_text}]({image_path})"
            
        # Create the markdown image tag with embedded base64 data
        return f"![{alt_text}](data:image/{file_ext};base64,{base64_image})"
    except Exception:
        # Fallback to simple link if anything goes wrong
        return f"[View {alt_text}]({image_path})"

def get_latest_insight_file() -> Optional[str]:
    """Find the most recent insight snapshot file."""
    processed_dir = os.path.join("data", "processed", "insights")
    if not os.path.exists(processed_dir):
        return None
    
    pattern = os.path.join(processed_dir, "insight_snapshot_*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by filename (assumes format insight_snapshot_YYYYMMDD.json)
    return max(files, key=os.path.getmtime)

def generate_country_section(country_name: str, profile: Dict[str, Any]) -> str:
    """Generate a Markdown section for a specific country profile."""
    section = f"### {country_name}\n\n"
    
    # Add basic stats
    section += f"**Total Events:** {profile.get('total_events', 0)}  \n"
    section += f"**Fatalities:** {profile.get('fatalities', 0)}  \n"
    section += f"**Event Types:** {', '.join(profile.get('event_types', []))}  \n\n"
    
    # Add strategic sites if any
    if profile.get('strategic_sites'):
        section += f"**Strategic Sites:** {', '.join(profile.get('strategic_sites', []))}  \n\n"
    
    # Add top locations if any
    if profile.get('top_locations'):
        section += "**Top Event Locations:**  \n"
        for loc in profile.get('top_locations', [])[:3]:
            section += f"- {loc.get('location')}: {loc.get('count')} events  \n"
        section += "\n"
    
    return section

def generate_event_type_section(event_type: str, data: Dict[str, Any]) -> str:
    """Generate a Markdown section for a specific event type."""
    section = f"### {event_type}\n\n"
    
    # Add basic stats
    section += f"**Events:** {data.get('count', 0)}  \n"
    section += f"**Fatalities:** {data.get('fatalities', 0)}  \n\n"
    
    # Add top locations if any
    if data.get('top_locations'):
        section += "**Top Locations:**  \n"
        for loc in data.get('top_locations', [])[:3]:
            section += f"- {loc.get('location')}: {loc.get('count')} events  \n"
        section += "\n"
    
    # Add top countries if any
    if data.get('top_countries'):
        section += "**Top Countries:**  \n"
        for country in data.get('top_countries', [])[:3]:
            section += f"- {country.get('country')}: {country.get('count')} events  \n"
        section += "\n"
    
    return section

def generate_hotspots_section(hotspots: List[Dict[str, Any]]) -> str:
    """Generate a Markdown section for hotspots."""
    section = "## Conflict Hotspots\n\n"
    
    if not hotspots:
        section += "No significant hotspots identified in this period.\n\n"
        return section
    
    # Add top hotspots
    section += "**Top Event Locations:**  \n"
    for i, hotspot in enumerate(hotspots[:5], 1):
        section += f"{i}. **{hotspot.get('location')}, {hotspot.get('country')}**  \n"
        section += f"   Events: {hotspot.get('count')}, Fatalities: {hotspot.get('fatalities')}  \n"
        section += f"   Event Types: {', '.join(hotspot.get('event_types', []))}  \n\n"
    
    return section

def generate_strategic_alerts_section(alerts: List[Dict[str, Any]]) -> str:
    """Generate a Markdown section for strategic alerts."""
    section = "## Strategic Alerts\n\n"
    
    if not alerts:
        section += "No strategic alerts identified in this period.\n\n"
        return section
    
    # Add alerts with details
    for i, alert in enumerate(alerts, 1):
        section += f"{i}. **{alert.get('location')}, {alert.get('country')}** ({alert.get('event_date')})  \n"
        if alert.get('keywords'):
            section += f"   Keywords: {', '.join(alert.get('keywords'))}  \n"
        if alert.get('notes'):
            section += f"   Details: {alert.get('notes')}  \n\n"
    
    return section

def generate_visualizations_section(insights: Dict[str, Any]) -> str:
    """Generate a Markdown section with embedded visualizations."""
    section = "## Visualizations\n\n"
    
    vis_paths = insights.get('visualization_paths', {})
    if not vis_paths:
        section += "No visualizations available for this period.\n\n"
        return section
    
    # Add charts
    if 'charts' in vis_paths:
        charts = vis_paths['charts']
        
        # Event type distribution chart
        if 'event_type_distribution' in charts:
            section += "### Event Type Distribution\n\n"
            section += embed_image_in_markdown(charts['event_type_distribution'], "Event Type Distribution") + "\n\n"
        
        # Fatalities by country chart
        if 'fatalities_by_country' in charts:
            section += "### Fatalities by Country\n\n"
            section += embed_image_in_markdown(charts['fatalities_by_country'], "Fatalities by Country") + "\n\n"
        
        # Fatalities by event type chart
        if 'fatalities_by_event_type' in charts:
            section += "### Fatalities by Event Type\n\n"
            section += embed_image_in_markdown(charts['fatalities_by_event_type'], "Fatalities by Event Type") + "\n\n"
        
        # Top hotspots chart
        if 'top_hotspots' in charts:
            section += "### Top Hotspots\n\n"
            section += embed_image_in_markdown(charts['top_hotspots'], "Top Hotspots") + "\n\n"
    
    # Add heatmap if available
    if 'heatmap' in vis_paths and vis_paths['heatmap']:
        section += "### Conflict Heatmap\n\n"
        section += f"[View Interactive Conflict Heatmap]({vis_paths['heatmap']})\n\n"
    
    # Add event type maps if available
    if 'event_type_maps' in vis_paths and vis_paths['event_type_maps']:
        section += "### Event Type Maps\n\n"
        section += "Interactive maps for specific event types:\n\n"
        
        for event_type, map_path in vis_paths['event_type_maps'].items():
            section += f"- [{event_type} Map]({map_path})\n"
        
        section += "\n"
    
    return section

def run() -> Dict[str, Any]:
    """Entrypoint for generating an enhanced narrative report via LLM"""
    try:
        # Find the most recent insight snapshot
        insight_file = get_latest_insight_file()
        if not insight_file:
            # Fall back to the old method of finding summary files
            processed_dir = os.path.join("data", "processed")
            pattern = os.path.join(processed_dir, "summary_*.json")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No insight or summary JSON found in {processed_dir}")
            insight_file = max(files, key=os.path.getmtime)
        
        # Load insights
        with open(insight_file, "r", encoding="utf-8") as f:
            insights = json.load(f)
        
        # Extract period information
        period = insights.get("period_analyzed", {})
        period_str = f"{period.get('start_date', 'Unknown')} to {period.get('end_date', 'Unknown')}"
        
        # Start building the comprehensive report
        report_sections = []
        
        # 1. Title and summary section
        report_sections.append(f"# Conflict Analysis Report: {period_str}\n\n")
        
        # 2. Overview section with key metrics
        overview = (
            "## Overview\n\n"
            f"**Total Events:** {insights.get('total_events', 0)}  \n"
            f"**Total Fatalities:** {insights.get('total_fatalities', 0)}  \n"
            f"**Escalation Status:** {'⚠️ Escalating' if insights.get('is_escalating', False) else 'Stable'}  \n"
            f"**Countries Affected:** {len(insights.get('country_profiles', {}))}  \n"
            f"**Strategic Alerts:** {len(insights.get('strategic_alerts', []))}  \n\n"
        )
        report_sections.append(overview)
        
        # 3. Get LLM-generated narrative summary
        prompt_lines = [
            "You are an expert conflict analyst. Produce a detailed narrative overview of the following conflict data:",
            f"Period: {period_str}",
            f"Total Events: {insights.get('total_events', 0)}",
            f"Total Fatalities: {insights.get('total_fatalities', 0)}",
            f"Is Escalating: {insights.get('is_escalating', False)}",
            "\nTop Countries by Events:",
        ]
        
        # Add top countries information
        countries = list(insights.get('country_profiles', {}).keys())
        for country in countries[:5]:
            profile = insights.get('country_profiles', {}).get(country, {})
            prompt_lines.append(f"- {country}: {profile.get('total_events', 0)} events, {profile.get('fatalities', 0)} fatalities")
        
        # Add hotspots information
        prompt_lines.append("\nTop Hotspots:")
        for hotspot in insights.get('hotspots', [])[:5]:
            prompt_lines.append(f"- {hotspot.get('location')}, {hotspot.get('country')}: {hotspot.get('count')} events, {hotspot.get('fatalities')} fatalities")
        
        # Add event type summary
        prompt_lines.append("\nEvent Types:")
        for event_type, data in insights.get('event_type_summary', {}).items():
            prompt_lines.append(f"- {event_type}: {data.get('count')} events, {data.get('fatalities')} fatalities")
        
        # Add strategic alerts
        if insights.get('strategic_alerts'):
            prompt_lines.append("\nStrategic Alerts:")
            for alert in insights.get('strategic_alerts', []):
                prompt_lines.append(f"- {alert.get('location')}, {alert.get('country')}: {alert.get('notes')[:100]}...")
        
        prompt_lines.append("\nPlease write a detailed narrative overview (~200 words) of the conflict situation based on this data. Focus on key patterns, escalations, and strategic developments. Highlight the most significant hotspots and countries.")
        
        prompt = "\n".join(prompt_lines)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert conflict analyst who provides insightful, objective analysis of armed conflicts, protests, and political violence globally."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )
        narrative_overview = response.choices[0].message.content
        report_sections.append(f"## Narrative Overview\n\n{narrative_overview}\n\n")
        
        # 4. Add hotspots section
        report_sections.append(generate_hotspots_section(insights.get('hotspots', [])))
        
        # 5. Add strategic alerts section
        report_sections.append(generate_strategic_alerts_section(insights.get('strategic_alerts', [])))
        
        # 6. Add country profiles section for top 5 countries
        report_sections.append("## Country Profiles\n\n")
        for country in countries[:5]:
            profile = insights.get('country_profiles', {}).get(country, {})
            report_sections.append(generate_country_section(country, profile))
        
        # 7. Add event type summary section for top event types
        report_sections.append("## Event Type Analysis\n\n")
        for event_type, data in list(insights.get('event_type_summary', {}).items())[:5]:
            report_sections.append(generate_event_type_section(event_type, data))
        
        # 8. Add visualizations section
        report_sections.append(generate_visualizations_section(insights))
        
        # 9. Add footer with timestamp
        report_sections.append(f"\n\n---\n\nReport generated by ForgeNews on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Combine all sections into the final report
        report_text = "\n".join(report_sections)
        
        # Save the report to file
        os.makedirs("reports", exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"reports/conflict_report_{date_str}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_text)
        
        return {"status": "success", "report": report_text, "file": filename}
        
    except Exception as e:
        print(f"[llm_report_agent] Error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        } 