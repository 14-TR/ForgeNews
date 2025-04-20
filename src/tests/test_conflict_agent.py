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

def test_get_conflict_feed_with_region_and_date_range(monkeypatch):
    """Ensure get_conflict_feed applies region and date_range parameters to the API request."""
    fake_events = [{'fatalities': 0}]
    class FakeResp:
        status_code = 200
        def json(self):
            return {'data': fake_events}
    def fake_get(url, params):
        assert params['region'] == 'TestRegion'
        assert params['start_date'] == '2021-01-01'
        assert params['end_date'] == '2021-12-31'
        return FakeResp()
    monkeypatch.setenv('ACLED_API_KEY', 'dummy_key')
    monkeypatch.setattr('agents.conflict_agent.requests.get', fake_get)
    data = get_conflict_feed(limit=5, region='TestRegion', date_range=('2021-01-01','2021-12-31'))
    assert data == fake_events

def test_flag_event_threshold():
    """Ensure flag_event marks events correctly based on threshold."""
    low = {'fatalities': 5}
    high = {'fatalities': 15}
    assert flag_event(low, threshold=10)['flagged'] is False
    assert flag_event(high, threshold=10)['flagged'] is True

def test_get_conflict_feed_defaults_to_today(monkeypatch):
    """Ensure get_conflict_feed defaults to today's date for start_date and end_date."""
    # Prepare fake response
    fake_events = []
    class FakeResp:
        status_code = 200
        def json(self):
            return {'data': fake_events}

    # Monkeypatch date to return a fixed date
    import agents.conflict_agent as mod
    import datetime
    monkeypatch.setenv('ACLED_API_KEY', 'dummy_key')
    class FakeDate:
        @classmethod
        def today(cls):
            return datetime.date(2025, 4, 19)
    monkeypatch.setattr(mod, 'date', FakeDate)
    # Patch requests.get
    def fake_get(url, params):
        assert params['start_date'] == '2025-04-19'
        assert params['end_date'] == '2025-04-19'
        return FakeResp()
    monkeypatch.setattr('agents.conflict_agent.requests.get', fake_get)

    # Call without date_range
    data = get_conflict_feed()
    assert data == fake_events
