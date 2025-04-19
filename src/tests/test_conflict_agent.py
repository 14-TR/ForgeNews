"""
Unit tests for the conflict_agent module.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from agents.conflict_agent import get_conflict_feed, flag_event, run

def test_get_conflict_feed_returns_list():
    """Ensure that get_conflict_feed() returns a list."""
    feed = get_conflict_feed()
    assert isinstance(feed, list)

def test_flag_event_wraps_event():
    """Ensure that flag_event() returns a dict with flagged and event keys."""
    sample = {'id': 42, 'info': 'sample'}
    result = flag_event(sample)
    assert isinstance(result, dict)
    assert 'flagged' in result and 'event' in result
    assert result['event'] == sample

def test_run_returns_success_and_data(monkeypatch):
    """Ensure run() returns success status and data list of flagged events."""
    dummy_events = [{'id': 1}, {'id': 2}]
    # Patch get_conflict_feed to return dummy_events
    monkeypatch.setattr('agents.conflict_agent.get_conflict_feed', lambda: dummy_events)
    # Patch flag_event to mark flagged True
    monkeypatch.setattr('agents.conflict_agent.flag_event', lambda e: {'flagged': True, 'event': e})

    result = run()
    assert result['status'] == 'success'
    assert isinstance(result['data'], list)
    assert all(item.get('flagged') for item in result['data'])
