"""
Integration test for conflict_agent against the real ACLED API.
Skips if `ACLED_API_KEY` is not provided in environment.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from agents.conflict_agent import get_conflict_feed

API_KEY = os.getenv("ACLED_API_KEY")

@pytest.mark.skipif(API_KEY is None, reason="ACLED_API_KEY not set, skipping live API test")
def test_conflict_agent_integration_real_api():
    # Fetch a small batch of today's events
    data = get_conflict_feed(limit=1)
    assert isinstance(data, list), "Expected a list of events"
    # If API returns data, ensure each item is a dict
    for event in data:
        assert isinstance(event, dict)
