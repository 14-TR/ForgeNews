"""
Unit and integration tests for the insight_agent module.
"""

import os
import sys
import json
from unittest.mock import patch, mock_open
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.insight_agent import (
    summarize_conflict_events,
    score_signal_strength,
    analyze_conflict_data,
    extract_hotspots,
    extract_country_profiles,
    extract_event_type_summary,
    extract_strategic_alerts,
    run
)

# Sample conflict event data for testing
SAMPLE_EVENTS = [
    {
        "event_date": "2025-04-01",
        "country": "Syria",
        "admin1": "Aleppo",
        "event_type": "Violence against civilians",
        "actor1": "Military Forces of Syria",
        "fatalities": 15,
        "notes": "Syrian forces attacked civilian neighborhoods in eastern Aleppo.",
        "location": "Sayda",
        "latitude": "36.12345",
        "longitude": "37.45678"
    },
    {
        "event_date": "2025-04-02",
        "country": "Ukraine",
        "admin1": "Donetsk",
        "event_type": "Battles",
        "actor1": "Military Forces of Russia",
        "fatalities": 8,
        "notes": "Skirmish between Russian and Ukrainian forces near Donetsk.",
        "location": "Donetsk",
        "latitude": "48.12345",
        "longitude": "37.45678"
    },
    {
        "event_date": "2025-04-03",
        "country": "Somalia",
        "admin1": "Mogadishu",
        "event_type": "Explosions/Remote violence",
        "actor1": "Al Shabaab",
        "fatalities": 23,
        "notes": "Bombing in central Mogadishu attributed to Al Shabaab.",
        "location": "Mogadishu",
        "latitude": "2.12345",
        "longitude": "45.45678"
    },
    {
        "event_date": "2025-04-03",
        "country": "Syria",
        "admin1": "Damascus",
        "event_type": "Strategic developments",
        "actor1": "Government of Syria",
        "fatalities": 0,
        "notes": "Peace agreement negotiation with opposition forces announced in Damascus. Military deployment witnessed in suburbs.",
        "location": "Damascus",
        "latitude": "33.12345",
        "longitude": "36.45678"
    },
    {
        "event_date": "2025-04-04",
        "country": "Syria",
        "admin1": "Aleppo",
        "event_type": "Violence against civilians",
        "actor1": "Military Forces of Syria",
        "fatalities": 5,
        "notes": "Another attack in civilian areas of Aleppo.",
        "location": "Sayda",
        "latitude": "36.12345",
        "longitude": "37.45678"
    }
]

def test_summarize_conflict_events():
    """Test that summarize_conflict_events correctly summarizes data."""
    summary = summarize_conflict_events(SAMPLE_EVENTS)
    
    assert summary["status"] == "success"
    assert summary["total_events"] == 5
    assert summary["total_fatalities"] == 51
    
    # Check hotspots (should be 3 locations)
    assert len(summary["hotspots"]) == 4
    
    # Check high fatality events (should be 2 with threshold of 10)
    assert len(summary["high_fatality_events"]) == 2
    
    # Check period analyzed
    assert summary["period_analyzed"]["start_date"] == "2025-04-01"
    assert summary["period_analyzed"]["end_date"] == "2025-04-04"

def test_extract_hotspots():
    """Test that extract_hotspots correctly identifies hotspot locations."""
    hotspots = extract_hotspots(SAMPLE_EVENTS)
    
    # Sayda should be the top hotspot with 2 events
    assert len(hotspots) > 0
    assert hotspots[0]["location"] == "Sayda"
    assert hotspots[0]["country"] == "Syria"
    assert hotspots[0]["count"] == 2
    
    # Check that coordinates are extracted
    assert "lat" in hotspots[0]
    assert "lon" in hotspots[0]
    
    # Check that fatalities are summed correctly
    assert hotspots[0]["fatalities"] == 20  # 15 + 5

def test_extract_country_profiles():
    """Test that extract_country_profiles correctly builds country profiles."""
    profiles = extract_country_profiles(SAMPLE_EVENTS)
    
    # Check that all countries are included
    assert "Syria" in profiles
    assert "Ukraine" in profiles
    assert "Somalia" in profiles
    
    # Check Syria profile details
    syria_profile = profiles["Syria"]
    assert syria_profile["total_events"] == 3
    assert syria_profile["fatalities"] == 20
    assert len(syria_profile["event_types"]) == 2
    assert "Strategic developments" in syria_profile["event_types"]
    
    # Check strategic sites are detected
    assert "Damascus" in syria_profile["strategic_sites"]
    
    # Check locations are tracked
    assert any(item["location"] == "Sayda" for item in syria_profile["top_locations"])
    
    # Check timeline data exists
    assert "timeline" in syria_profile
    assert len(syria_profile["timeline"]) > 0

def test_extract_event_type_summary():
    """Test that extract_event_type_summary correctly summarizes event types."""
    summary = extract_event_type_summary(SAMPLE_EVENTS)
    
    # Check that all event types are included
    assert "Violence against civilians" in summary
    assert "Battles" in summary
    assert "Explosions/Remote violence" in summary
    assert "Strategic developments" in summary
    
    # Check details for Violence against civilians
    vac_summary = summary["Violence against civilians"]
    assert vac_summary["count"] == 2
    assert vac_summary["fatalities"] == 20
    
    # Check that locations are tracked
    assert any(item["location"] == "Sayda" for item in vac_summary["top_locations"])
    
    # Check that countries are tracked
    assert any(item["country"] == "Syria" for item in vac_summary["top_countries"])

def test_extract_strategic_alerts():
    """Test that extract_strategic_alerts correctly identifies strategic developments."""
    alerts = extract_strategic_alerts(SAMPLE_EVENTS)
    
    # Should find the strategic development in Damascus
    assert len(alerts) == 1
    assert alerts[0]["location"] == "Damascus"
    assert alerts[0]["country"] == "Syria"
    assert alerts[0]["event_type"] == "Strategic developments"
    
    # Should extract strategic keywords
    assert len(alerts[0]["keywords"]) > 0
    assert "peace agreement" in alerts[0]["keywords"]
    assert "deployment" in alerts[0]["keywords"]

def test_summarize_conflict_events_empty():
    """Test that summarize_conflict_events handles empty input correctly."""
    summary = summarize_conflict_events([])
    assert summary["status"] == "error"
    assert "No events" in summary["message"]

def test_score_signal_strength():
    """Test that score_signal_strength correctly scores events."""
    # High score case: high fatalities, severe event type, high-interest actor, volatile region
    high_score_event = {
        "fatalities": 120,
        "event_type": "Violence against civilians",
        "actor1": "Military Forces of Syria",
        "country": "Syria"
    }
    assert score_signal_strength(high_score_event) == 10  # Max score
    
    # Medium score case
    medium_score_event = {
        "fatalities": 15,
        "event_type": "Riots",
        "actor1": "Civilians",
        "country": "France"
    }
    medium_score = score_signal_strength(medium_score_event)
    assert 3 <= medium_score <= 5
    
    # Low score case
    low_score_event = {
        "fatalities": 0,
        "event_type": "Protests",
        "actor1": "Civilians",
        "country": "Canada"
    }
    assert score_signal_strength(low_score_event) <= 2

@patch("agents.insight_agent.load_conflict_events")
def test_analyze_conflict_data(mock_load):
    """Test that analyze_conflict_data correctly analyzes and scores events."""
    mock_load.return_value = SAMPLE_EVENTS
    
    result = analyze_conflict_data("dummy_path.json")
    
    assert result["status"] == "success"
    
    # Check that new insight layers are present
    assert "hotspots" in result
    assert "country_profiles" in result
    assert "event_type_summary" in result
    assert "strategic_alerts" in result
    
    # Check that signal analysis is present
    assert "signal_analysis" in result
    assert "average_signal_strength" in result["signal_analysis"]
    assert 0 <= result["signal_analysis"]["average_signal_strength"] <= 10
    
    # Check high signal events list exists
    assert "high_signal_events" in result["signal_analysis"]

@patch("os.path.exists")
@patch("os.listdir")
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"data": SAMPLE_EVENTS}))
@patch("json.dump")
@patch("os.makedirs")
@patch("agents.insight_agent.generate_conflict_heatmap")
@patch("agents.insight_agent.generate_event_type_maps")
@patch("agents.insight_agent.generate_charts")
def test_run_insight_agent(mock_charts, mock_maps, mock_heatmap, mock_makedirs, mock_json_dump, 
                          mock_file, mock_listdir, mock_exists):
    """Test the full run function of the insight agent."""
    mock_exists.return_value = True
    mock_listdir.return_value = ["conflict_2025-04-19.json"]
    mock_heatmap.return_value = "path/to/heatmap.html"
    mock_maps.return_value = {"Violence against civilians": "path/to/vac_map.html"}
    mock_charts.return_value = {"event_type_distribution": "path/to/chart.png"}
    
    result = run()
    
    assert result["status"] == "success"
    assert "insights_file" in result
    assert "summary" in result
    assert "events_analyzed" in result["summary"]
    assert result["summary"]["events_analyzed"] == 5
    assert "countries" in result["summary"]
    assert "strategic_alerts" in result["summary"]

@patch("os.listdir")
def test_run_no_conflict_files(mock_listdir):
    """Test run function when no conflict files are available."""
    mock_listdir.return_value = []
    
    result = run()
    
    assert result["status"] == "error"
    assert "No conflict data files found" in result["message"]

# Integration tests
@pytest.mark.integration
def test_integration_with_real_data():
    """Integration test using real data files from the repository."""
    # Skip if running in CI environment without real data files
    data_path = os.path.join("data", "raw")
    if not os.path.exists(data_path) or not os.listdir(data_path):
        pytest.skip("No real data files available for integration testing")
    
    # Find conflict data files
    conflict_files = [f for f in os.listdir(data_path) if f.startswith("conflict_") and f.endswith(".json")]
    if not conflict_files:
        pytest.skip("No conflict data files available for integration testing")
    
    # Test with the real file
    file_path = os.path.join(data_path, conflict_files[0])
    
    # File size check - skip if file is empty
    if os.path.getsize(file_path) < 10:
        pytest.skip("Conflict data file appears to be empty")
    
    result = analyze_conflict_data(file_path)
    assert result["status"] == "success"
    assert "total_events" in result
    assert "signal_analysis" in result