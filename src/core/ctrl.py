"""
MissionControl (ctrl): Orchestrates agent workflows within ForgeNews.
Ensures efficient deployment and monitoring of modular agents.
"""

from datetime import datetime
import json
import os
from typing import Dict, Any
from pathlib import Path

STATE_FILE = Path("pipeline_state.json")

def load_state() -> Dict[str, Any]:
    """Loads the pipeline state from the state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_state(state: Dict[str, Any]) -> None:
    """Saves the current pipeline state."""
    with open(STATE_FILE, 'w') as file:
        json.dump(state, file, indent=2)

def check_last_run(agent_name: str, interval_hours: int) -> bool:
    """Checks if enough time has elapsed since the agent's last run."""
    state = load_state()
    last_run = state.get(agent_name)
    if last_run:
        last_run_time = datetime.fromisoformat(last_run)
        elapsed_hours = (datetime.utcnow() - last_run_time).total_seconds() / 3600
        return elapsed_hours >= interval_hours
    return True

def log_run(agent_name: str, success: bool) -> None:
    """Logs the agent run status and timestamp."""
    state = load_state()
    state[agent_name] = datetime.utcnow().isoformat()
    save_state(state)

def execute_agent(agent_callable, agent_name: str, interval_hours: int = 24):
    """Executes an agent if conditions are met."""
    if check_last_run(agent_name, interval_hours):
        try:
            agent_callable()
            log_run(agent_name, success=True)
        except Exception as e:
            log_run(agent_name, success=False)
            raise e
