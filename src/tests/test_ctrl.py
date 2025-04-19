"""
Basic unit tests for the ForgeNews ctrl orchestrator.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import pytest
from core.ctrl import check_last_run, log_run, load_state, save_state

# Test setup: use a temporary pipeline state file
TEST_STATE_FILE = "test_pipeline_state.json"

def setup_module(module):
    """Redirects state file path for testing."""
    from core import ctrl
    ctrl.STATE_FILE = TEST_STATE_FILE


def teardown_module(module):
    """Cleans up the test state file."""
    if os.path.exists(TEST_STATE_FILE):
        os.remove(TEST_STATE_FILE)


def test_initial_check_last_run_returns_true():
    """Should return True when no state is present."""
    assert check_last_run("test_agent", 24) is True


def test_log_run_creates_state_entry():
    """Should log an agent run and reflect it in the state file."""
    log_run("test_agent", True)
    state = load_state()
    assert "test_agent" in state
    assert isinstance(state["test_agent"], str)  # ISO timestamp


def test_check_last_run_after_logging():
    """Should return False if interval hasn't passed yet and True when interval=0."""
    assert check_last_run("test_agent", 24) is False
    assert check_last_run("test_agent", 0) is True 