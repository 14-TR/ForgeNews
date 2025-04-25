"""
MissionControl (ctrl): Orchestrates agent workflows within ForgeNews.
Ensures efficient deployment and monitoring of modular agents.
"""

from datetime import datetime
import json
import os
import sys
from typing import Dict, Any, Callable, Optional, Tuple
from pathlib import Path

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.conflict_agent import run as conflict_agent_run
from src.agents.report_agent import run as report_agent_run
from src.agents.substack_agent import run as substack_agent_run
from src.agents.llm_report_agent import run as llm_report_agent_run
from src.agents.ctrl_agent import run as ctrl_agent_run
from src.agents.ai_news_agent import run as ai_news_agent_run
from src.agents.insight_agent import InsightAgent
import time

# Import tool registry to check risk levels
from src.core.tool_registry import registry as tool_registry

# Default state file, can be overridden for testing
STATE_FILE = "pipeline_state.json"

# Global registry for agents
AGENT_REGISTRY = {}

# Auto register agents
AGENT_REGISTRY["conflict_agent"] = conflict_agent_run
AGENT_REGISTRY["report_agent"] = report_agent_run
AGENT_REGISTRY["substack_agent"] = substack_agent_run
AGENT_REGISTRY["llm_report_agent"] = llm_report_agent_run
AGENT_REGISTRY["ctrl_agent"] = ctrl_agent_run
AGENT_REGISTRY["ai_news_agent"] = ai_news_agent_run
AGENT_REGISTRY["insight_agent"] = lambda: InsightAgent().run()

# Map of agent to associated tools
AGENT_TOOLS = {
    "conflict_agent": ["get_conflict_feed", "flag_event", "get_summary"],
    "report_agent": ["get_summary", "generate_report"],
    "substack_agent": ["get_content", "publish_newsletter"],
    "llm_report_agent": ["get_summary", "generate_llm_report"],
    "ctrl_agent": ["monitor_agents"],
    "ai_news_agent": ["get_ai_news"],
    "insight_agent": ["analyze_conflict"],
}

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
def _append_runlog(agent_name: str, status: str, timestamp: str, duration: Optional[float] = None, 
                  tool_risks: Optional[Dict[str, str]] = None, level: str = "INFO") -> None:
    runlog_path = os.path.join('logs', 'runlog.json')
    try:
        os.makedirs(os.path.dirname(runlog_path), exist_ok=True)
        if os.path.exists(runlog_path):
            with open(runlog_path, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        log_entry = {
            "timestamp": timestamp, 
            "agent": agent_name, 
            "status": status, 
            "duration": duration,
            "level": level
        }
        
        # Add tool risk information if available
        if tool_risks:
            log_entry["tool_risks"] = tool_risks
            
        logs.append(log_entry)
        with open(runlog_path, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error logging to runlog: {str(e)}")

def check_tool_risks(agent_name: str, allow_high_risk: bool = False) -> Tuple[bool, Dict[str, str]]:
    """
    Check the risk level of tools associated with an agent.
    
    Args:
        agent_name: Name of the agent to check
        allow_high_risk: Whether to allow high-risk tools
        
    Returns:
        Tuple of (is_allowed, tool_risk_dict)
    """
    # If agent has no registered tools, allow by default
    if agent_name not in AGENT_TOOLS:
        return True, {}
    
    tool_risks = {}
    for tool_name in AGENT_TOOLS[agent_name]:
        tool_info = tool_registry.get(tool_name)
        if tool_info:
            tool_risks[tool_name] = tool_info.risk_level
        else:
            # If tool not in registry, assume medium risk
            tool_risks[tool_name] = "medium"
    
    # Check if any tool is high risk
    has_high_risk = any(risk.lower() == "high" for risk in tool_risks.values())
    
    # Block execution if high risk tools and not explicitly allowed
    if has_high_risk and not allow_high_risk:
        return False, tool_risks
    
    return True, tool_risks

def execute_agent(agent_callable: Callable[..., Any], agent_name: str, 
                 interval_hours: int = 24, allow_high_risk: bool = False) -> Any:
    """Executes an agent if conditions are met, then logs the outcome."""
    status: str = 'blocked'
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()
    
    # Check tool risk levels
    is_allowed, tool_risks = check_tool_risks(agent_name, allow_high_risk)
    
    if not is_allowed:
        status = 'blocked_high_risk'
        _append_runlog(agent_name, status, timestamp, 0, tool_risks, level="WARNING")
        return {
            "status": "blocked", 
            "message": "Run blocked due to high-risk tools. Use allow_high_risk=True to override."
        }
    
    # Check whether we can run based on timing
    if check_last_run(agent_name, interval_hours):
        try:
            result = agent_callable()
            log_run(agent_name, result=True)
            status = 'success'
            end_time = time.time()
            duration = end_time - start_time
            _append_runlog(agent_name, status, timestamp, duration, tool_risks, level="INFO")
            return result
        except Exception as e:
            log_run(agent_name, result=False)
            status = 'failure'
            end_time = time.time()
            duration = end_time - start_time
            _append_runlog(agent_name, status, timestamp, duration, tool_risks, level="ERROR")
            raise e
    
    # Blocked by timing
    status = 'blocked_interval'
    # No execution, duration = 0
    _append_runlog(agent_name, status, timestamp, 0, tool_risks, level="INFO")
    return {"status": "blocked", "message": "Run blocked due to interval constraint."}
