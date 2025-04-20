"""
Unit tests for the example_agent module.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from agents.example_agent import run

def test_example_agent_reads_api_key(monkeypatch, capsys):
    """Ensure that example_agent.run() includes the EXAMPLE_AGENT_API_KEY in its output."""
    monkeypatch.setenv("EXAMPLE_AGENT_API_KEY", "TEST_KEY_123")
    result = run()
    captured = capsys.readouterr()
    assert "TEST_KEY_123" in captured.out
    assert result == {"status": "success"}

