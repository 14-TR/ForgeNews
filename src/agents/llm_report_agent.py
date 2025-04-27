#!/usr/bin/env python3
import os
import sys
import traceback

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
    
    # Correct the pattern to match the actual insight files
    pattern = os.path.join(processed_dir, "conflict_insights_*.json") 
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
        # Ensure list before slicing
        for loc in (profile.get('top_locations') or [])[:3]:
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
         # Ensure list before slicing
        for loc in (data.get('top_locations') or [])[:3]:
            section += f"- {loc.get('location')}: {loc.get('count')} events  \n"
        section += "\n"
    
    # Add top countries if any
    if data.get('top_countries'):
        section += "**Top Countries:**  \n"
        # --- Corrected Handling for Dictionary ---
        top_countries_dict = data.get('top_countries', {}) # Ensure it's a dict
        # Sort items by count (value) descending, take top 3
        sorted_countries = sorted(top_countries_dict.items(), key=lambda item: item[1], reverse=True)[:3]
        for country_name, count in sorted_countries:
             section += f"- {country_name}: {count} events  \n" # Format directly
        # --- End Correction ---
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
    # Ensure list before slicing (hotspots argument is already checked in run() but double-check)
    for i, hotspot in enumerate((hotspots or [])[:5], 1):
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
        # Correctly access country/countries information
        location_info = alert.get('location', {})
        countries_list = location_info.get('countries', [])
        location_str = location_info.get('location') # Get specific location if present
        
        # Determine primary location display
        if location_str:
            display_location = f"{location_str}, {', '.join(countries_list)}"
        elif countries_list:
            display_location = ', '.join(countries_list)
        else:
            display_location = "Unknown Location"
            
        # Get alert type and severity
        alert_type = alert.get('type', 'Unknown Type')
        severity = alert.get('severity', 'Unknown')

        # Use description which is available in the insights data
        description = alert.get('description', 'No details available.')

        section += f"{i}. **{alert_type} ({severity})**: {display_location}  \n"
        section += f"   Details: {description}  \n\n"
        # Removed access to alert.get('keywords') and alert.get('notes') as they are not in the insight data
        # Added severity and type, using description for details

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

def generate_insight_section(insights: List[Dict[str, Any]]) -> str:
    """Generate a Markdown section for insights with scores."""
    section = "## Key Insights\n\n"
    
    if not insights:
        section += "No insights available for this period.\n\n"
        return section
    
    # Group insights by domain
    domains = {}
    for ins in insights:
        domain = ins.get('domain')
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(ins)
    
    # Add insights by domain
    for domain, domain_insights in domains.items():
        section += f"### {domain.title()} Domain\n\n"
        
        # Sort by relevance and novelty (combined score)
        sorted_insights = sorted(
            domain_insights, 
            key=lambda x: (x.get('relevance', 0) + x.get('novelty', 0)), 
            reverse=True
        )[:5]  # Show top 5 per domain
        
        for ins in sorted_insights:
            section += f"**{ins.get('title', 'Untitled Insight')}**\n\n"
            section += f"{ins.get('body', 'No details available.')}\n\n"
            
            # Add signal scores
            section += f"<p class='meta'>Signal Score: Relevance {ins.get('relevance', 'N/A')}, Novelty {ins.get('novelty', 'N/A')}"
            if ins.get('domain') == "markets":
                section += f", Volatility {ins.get('volatility', 'N/A')}"
            section += f", Confidence: {ins.get('confidence', 'low').title()}</p>\n\n"
    
    return section

def run() -> Dict[str, Any]:
    """Entrypoint for generating an enhanced narrative report via LLM"""
    try:
        # Find the most recent insight snapshot
        insight_file = get_latest_insight_file()
        if not insight_file:
            # Fall back logic remains, but primary target is conflict_insights
            processed_dir = os.path.join("data", "processed")
            pattern = os.path.join(processed_dir, "summary_*.json") # Fallback pattern
            files = glob.glob(pattern)
            if not files:
                 # If fallback also fails, raise specific error
                 raise FileNotFoundError(f"No conflict_insights or summary JSON found.")
            insight_file = max(files, key=os.path.getmtime)
            print(f"Warning: Could not find conflict_insights file. Falling back to {insight_file}")

        # Load insights
        with open(insight_file, "r", encoding="utf-8") as f:
            insights = json.load(f)

        # --- Corrected Period Extraction ---
        # Get metadata safely, defaulting to empty dict if not found
        metadata = insights.get("metadata", {}) 
        period_start = metadata.get('period_start', 'Unknown')
        period_end = metadata.get('period_end', 'Unknown')
        period_str = f"{period_start} to {period_end}"
        total_events = metadata.get('total_events', 0)
        total_fatalities = metadata.get('total_fatalities', 0)
        # --- End Corrected Period Extraction ---

        # Start building the comprehensive report
        report_sections = []

        # 1. Title and summary section
        report_sections.append(f"# Conflict Analysis Report: {period_str}\n\n")

        # 2. Overview section with key metrics
        # Using variables derived safely above
        # Removed non-existent 'is_escalating' flag
        country_profiles_data = insights.get('country_profiles') or {} # Ensure dict before .items()
        strategic_alerts_data = insights.get('strategic_alerts', [])
        overview = (
            "## Overview\n\n"
            f"**Total Events:** {total_events}  \n"
            f"**Total Fatalities:** {total_fatalities}  \n"
            # f"**Escalation Status:** {'⚠️ Escalating' if insights.get('is_escalating', False) else 'Stable'}  \n" # Removed
            f"**Countries Affected:** {len(country_profiles_data)}  \n"
            # f"**Strategic Alerts:** {len(strategic_alerts_data)}  \n\n" # Removed strategic alerts count
        )
        report_sections.append(overview)

        # 3. Get LLM-generated narrative summary
        prompt_lines = [
            "You are an expert conflict analyst. Produce a detailed narrative overview of the following conflict data:",
            f"Period: {period_str}",
            f"Total Events: {total_events}",
            f"Total Fatalities: {total_fatalities}",
            # f"Is Escalating: {insights.get('is_escalating', False)}", # Removed
            "\nTop Countries by Events:",
        ]
        # Safely add top countries to prompt
        for country, profile in list(country_profiles_data.items())[:5]: # Iterate over copy
            prompt_lines.append(f"- {country}: {profile.get('events', 0)} events, {profile.get('fatalities', 0)} fatalities")

        prompt_lines.append("\nTop Event Types:")
        event_type_summary_data = insights.get('event_type_summary', {})
        for event_type, summary in list(event_type_summary_data.items()): # Iterate over copy
            prompt_lines.append(f"- {event_type}: {summary.get('count', 0)} events, {summary.get('fatalities', 0)} fatalities")
        
        prompt_lines.append("\nKey Hotspots:")
        hotspots_data = insights.get('hotspots') or [] # Ensure list before slicing
        for hotspot in hotspots_data[:3]:
             prompt_lines.append(f"- {hotspot.get('location', '?')}, {hotspot.get('country', '?')}: {hotspot.get('count', 0)} events, {hotspot.get('fatalities', 0)} fatalities")

        # prompt_lines.append("\nStrategic Alerts:") # Removed strategic alerts from prompt
        # strategic_alerts_data = insights.get('strategic_alerts') or [] # Ensure list before slicing
        # for alert in strategic_alerts_data[:3]:
        #     prompt_lines.append(f"- {alert.get('type', 'Alert')}: {alert.get('description', 'No description')}")
            
        prompt_lines.append("\nPlease provide a concise narrative summary (2-4 paragraphs) focusing on the overall situation, key conflict dynamics, and major hotspots. Strategic risks are now visualized on the map.") # Updated prompt guidance
        
        prompt = "\n".join(prompt_lines)
        
        # Make LLM call
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert conflict analyst generating report summaries."},
                    {"role": "user", "content": prompt}
                ]
            )
            narrative = completion.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            narrative = "Narrative generation failed due to API error."
            
        report_sections.append("## Narrative Overview\n\n")
        report_sections.append(narrative or "No narrative generated.")
        report_sections.append("\n\n")
        
        # 4. Add generated sections for hotspots, alerts, countries, events
        report_sections.append(generate_hotspots_section(hotspots_data))
        # report_sections.append(generate_strategic_alerts_section(strategic_alerts_data)) # Removed strategic alerts section
        
        # Generate Country Profiles section
        report_sections.append("## Country Profiles\n\n")
        if country_profiles_data:
             for country, profile in country_profiles_data.items():
                 report_sections.append(generate_country_section(country, profile))
        else:
             report_sections.append("No country-specific data available.\n\n")

        # Add insights section with scores
        try:
            # Try to load individual insights with scores
            insights_pattern = os.path.join("data", "processed", "insights", "insights_*.json")
            insights_files = glob.glob(insights_pattern)
            if insights_files:
                latest_insights_file = max(insights_files, key=os.path.getmtime)
                with open(latest_insights_file, "r", encoding="utf-8") as f:
                    insights_data = json.load(f)
                report_sections.append(generate_insight_section(insights_data))
        except Exception as insight_error:
            print(f"Error loading insights: {insight_error}")
            # Continue with report generation even if insights section fails

        # Generate Event Type Analysis section
        report_sections.append("## Event Type Analysis\n\n")
        if event_type_summary_data:
            for event_type, data in event_type_summary_data.items():
                report_sections.append(generate_event_type_section(event_type, data))
        else:
             report_sections.append("No event type data available.\n\n")

        # 5. Add Visualizations section
        report_sections.append(generate_visualizations_section(insights))

        # Combine all sections into the final report
        final_report = "".join(report_sections)
        
        # Add generation timestamp
        final_report += f"\n\n---\n\nReport generated by ForgeNews on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Save report
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        report_filename = f"conflict_report_{datetime.utcnow().strftime('%Y%m%d')}.md"
        report_filepath = reports_dir / report_filename
        
        # --- Added Logging --- 
        print(f"Attempting to write report to: {report_filepath}")
        try:
            with open(report_filepath, "w", encoding="utf-8") as f:
                f.write(final_report)
            print(f"Successfully wrote report to: {report_filepath}") # Log success
        except Exception as write_error:
             print(f"!!! FAILED to write report to {report_filepath}: {write_error}")
             # Optionally re-raise or handle differently
             raise write_error # Re-raise the error to ensure failure status
        # --- End Added Logging ---
            
        return {"status": "success", "report": final_report, "file": str(report_filepath)}

    except FileNotFoundError as e:
         print(f"Error: Input data file not found. {e}")
         return {"status": "error", "message": f"Input data file not found. {e}"}
    except Exception as e:
        print(f"Error in llm_report_agent: {e}")
        # --- Add full traceback printing ---
        print("--- Full Traceback ---")
        traceback.print_exc(file=sys.stdout) # Explicitly print to stdout
        print("--- End Traceback ---")
        # --- End Add ---
        return {"status": "error", "message": str(e)} 