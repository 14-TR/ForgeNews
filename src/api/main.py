"""
API entrypoint for the ForgeNews platform orchestrator (ctrl).
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Import the ctrl execution engine
from core.ctrl import execute_agent, AGENT_REGISTRY

# Import guardrail logic to protect agent calls
from core.guardrails import execute_guardrails

# Initialize FastAPI app
app = FastAPI(title="ForgeNews ctrl API", version="0.1")

# Define the expected JSON schema for agent execution
class AgentRequest(BaseModel):
    agent_name: str
    input_text: str

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
