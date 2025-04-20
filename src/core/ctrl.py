"""
MissionControl (ctrl): Orchestrates agent workflows within ForgeNews.
Ensures efficient deployment and monitoring of modular agents.
"""

from datetime import datetime
import json
import os
from typing import Dict, Any, Callable, Optional
from pathlib import Path
from agents.example_agent import run as example_agent_run
from agents.conflict_agent import run as conflict_agent_run
from agents.report_agent import run as report_agent_run
from agents.substack_agent import run as substack_agent_run
from agents.llm_report_agent import run as llm_report_agent_run
from agents.ctrl_agent import run as ctrl_agent_run
import time

# Default state file, can be overridden for testing
STATE_FILE = "pipeline_state.json"

# Global registry for agents
AGENT_REGISTRY = {}

# Auto register agents
AGENT_REGISTRY["example_agent"] = example_agent_run
AGENT_REGISTRY["conflict_agent"] = conflict_agent_run
AGENT_REGISTRY["report_agent"] = report_agent_run
AGENT_REGISTRY["substack_agent"] = substack_agent_run
AGENT_REGISTRY["llm_report_agent"] = llm_report_agent_run
AGENT_REGISTRY["ctrl_agent"] = ctrl_agent_run

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

# Helper to append entries to the run log
def _append_runlog(agent_name: str, status: str, timestamp: str, duration: Optional[float] = None) -> None:
    runlog_path = os.path.join('logs', 'runlog.json')
    try:
        if os.path.exists(runlog_path):
            with open(runlog_path, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append({"timestamp": timestamp, "agent": agent_name, "status": status, "duration": duration})
        with open(runlog_path, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception:
        pass

def execute_agent(agent_callable: Callable[..., Any], agent_name: str, interval_hours: int = 24) -> Any:
    """Executes an agent if conditions are met, then logs the outcome."""
    status: str = 'blocked'
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()
    # Check whether we can run
    if check_last_run(agent_name, interval_hours):
        try:
            result = agent_callable()
            log_run(agent_name, result=True)
            status = 'success'
            return result
        except Exception as e:
            log_run(agent_name, result=False)
            status = 'failure'
            raise e
        finally:
            end_time = time.time()
            duration = end_time - start_time
            _append_runlog(agent_name, status, timestamp, duration)
    # Blocked by timing
    status = 'blocked'
    # No execution, duration = 0
    _append_runlog(agent_name, status, timestamp, 0)
    return {"status": "blocked", "message": "Run blocked due to interval constraint."}
