"""
API entrypoint for the ForgeNews platform orchestrator (ctrl).
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the ctrl execution engine
from src.core.ctrl import execute_agent, AGENT_REGISTRY

# Import guardrail logic to protect agent calls
from src.core.guardrails import execute_guardrails

# Initialize FastAPI app
app = FastAPI(title="ForgeNews ctrl API", version="0.1")

# Define the expected JSON schema for agent execution
class AgentRequest(BaseModel):
    agent_name: str
    input_text: str

class LogFilter(BaseModel):
    agent_name: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# Endpoint to execute any registered agent
@app.post("/run-agent/")
async def run_agent(request: Request):
    """
    Runs the requested agent after passing through guardrails.
    Returns success if the agent executes safely.
    """
    data = await request.json()
    agent_name = data.get("agent_name")
    input_text = data.get("input_text", "")
    
    if not agent_name or agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Execute guardrails check
    if not execute_guardrails(input_text, ""):
        raise HTTPException(status_code=400, detail="Guardrails triggered, unsafe input detected.")
    
    agent_func = AGENT_REGISTRY[agent_name]
    result = agent_func()
    if result.get("status") == "success":
        return {"status": "Agent executed successfully."}
    else:
        return {"status": "Agent execution failed."}

@app.get("/dashboard/")
async def dashboard():
    """
    Provides a dashboard view of log data and pipeline state.
    Allows filtering logs by agent, status, and date.
    """
    # Load run logs
    runlog_path = os.path.join('logs', 'runlog.json')
    pipeline_state_path = "pipeline_state.json"
    
    logs = []
    if os.path.exists(runlog_path):
        try:
            with open(runlog_path, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    
    # Load pipeline state
    pipeline_state = {}
    if os.path.exists(pipeline_state_path):
        try:
            with open(pipeline_state_path, 'r') as f:
                pipeline_state = json.load(f)
        except json.JSONDecodeError:
            pipeline_state = {}
    
    # Get latest insights if available
    latest_insight = get_latest_insight()
    
    return {
        "logs": logs,
        "pipeline_state": pipeline_state,
        "latest_insight": latest_insight
    }

@app.post("/dashboard/filter")
async def filter_logs(filter_params: LogFilter):
    """
    Filter logs based on specified criteria.
    """
    runlog_path = os.path.join('logs', 'runlog.json')
    
    if not os.path.exists(runlog_path):
        return {"logs": []}
    
    try:
        with open(runlog_path, 'r') as f:
            logs = json.load(f)
    except json.JSONDecodeError:
        return {"logs": []}
    
    # Apply filters
    filtered_logs = logs
    
    # Filter by agent name
    if filter_params.agent_name:
        filtered_logs = [log for log in filtered_logs if log.get("agent") == filter_params.agent_name]
    
    # Filter by status
    if filter_params.status:
        filtered_logs = [log for log in filtered_logs if log.get("status") == filter_params.status]
    
    # Filter by date range
    if filter_params.date_from:
        try:
            date_from = datetime.fromisoformat(filter_params.date_from)
            filtered_logs = [
                log for log in filtered_logs 
                if "timestamp" in log and datetime.fromisoformat(log["timestamp"]) >= date_from
            ]
        except ValueError:
            pass
    
    if filter_params.date_to:
        try:
            date_to = datetime.fromisoformat(filter_params.date_to)
            filtered_logs = [
                log for log in filtered_logs 
                if "timestamp" in log and datetime.fromisoformat(log["timestamp"]) <= date_to
            ]
        except ValueError:
            pass
    
    return {"logs": filtered_logs}

def get_latest_insight() -> Dict[str, Any]:
    """
    Retrieve the latest insight summary from processed data.
    """
    insight_dir = os.path.join("data", "processed", "insights")
    if not os.path.exists(insight_dir):
        return {}
    
    insight_files = [f for f in os.listdir(insight_dir) if f.startswith("conflict_insights_") and f.endswith(".json")]
    if not insight_files:
        return {}
    
    # Sort by filename (assumes format conflict_insights_YYYYMMDD.json)
    insight_files.sort(reverse=True)
    latest_file = os.path.join(insight_dir, insight_files[0])
    
    try:
        with open(latest_file, 'r') as f:
            insight_data = json.load(f)
            
            # Create a simplified preview
            preview = {
                "file": latest_file,
                "total_events": insight_data.get("total_events", 0),
                "total_fatalities": insight_data.get("total_fatalities", 0),
                "is_escalating": insight_data.get("is_escalating", False),
                "hotspots": insight_data.get("hotspots", [])[:3],  # Top 3 hotspots
                "high_signal_events": insight_data.get("signal_analysis", {}).get("high_signal_events", [])[:2]  # Top 2 high signal events
            }
            
            return preview
    except Exception:
        return {}
