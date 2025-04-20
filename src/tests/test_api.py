"""
Integration tests for the ForgeNews FastAPI /run-agent/ endpoint.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from api.main import app
from core.ctrl import AGENT_REGISTRY

# Set up test client
client = TestClient(app)

def test_run_agent_success(monkeypatch):
    """
    Tests that a registered dummy agent executes and returns 200 OK.
    """

    # Define a dummy callable
    def dummy_agent():
        print("[dummy_agent] executed")
        return {"status": "success"}

    # Inject dummy agent into registry
    AGENT_REGISTRY["dummy_agent"] = dummy_agent

    # Send POST request with correct agent
    response = client.post("/run-agent/", json={
        "agent_name": "dummy_agent",
        "input_text": "Simulate test run"
    })

    assert response.status_code == 200, f"Expected 200 OK but got {response.status_code}"
    assert response.json()["status"] == "Agent executed successfully."
