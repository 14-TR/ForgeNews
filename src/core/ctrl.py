"""
MissionControl (ctrl): Orchestrates agent workflows within ForgeNews.
Ensures efficient deployment and monitoring of modular agents.
"""

from datetime import datetime
import json
import os
from typing import Dict, Any
from pathlib import Path
# Temporary agent registry
from agents.example_agent import run as example_agent_run

# Default state file, can be overridden for testing
STATE_FILE = "pipeline_state.json"

# Global registry for agents
AGENT_REGISTRY = {}

# Automatically register the dummy agent
AGENT_REGISTRY["example_agent"] = example_agent_run

def load_state() -> Dict[str, Any]:
    """Load the pipeline state from the state file. Returns a dict."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state: Dict[str, Any]) -> None:
    """Save the given state dict to the state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def check_last_run(agent_name: str, interval_hours: int) -> bool:
    """Check if enough time has passed since the last run of the given agent.\
    Returns True if the agent can be run (either it has never run, or the interval has passed.)."""
    state = load_state()
    if agent_name not in state:
        return True
    try:
        last_run_time = datetime.fromisoformat(state[agent_name])
    except Exception:
        return True
    now = datetime.utcnow()
    diff_hours = (now - last_run_time).total_seconds() / 3600.0
    return diff_hours >= interval_hours

def log_run(agent_name: str, result: bool) -> None:
    """Log an agent run by updating its last run timestamp in the state file.\
    The 'result' parameter can be used for additional processing if needed."""
    state = load_state()
    state[agent_name] = datetime.utcnow().isoformat()
    save_state(state)

def execute_agent(agent_callable, agent_name: str, interval_hours: int = 24):
    """Executes an agent if conditions are met."""
    if check_last_run(agent_name, interval_hours):
        try:
            agent_callable()
            log_run(agent_name, result=True)
        except Exception as e:
            log_run(agent_name, result=False)
            raise e
