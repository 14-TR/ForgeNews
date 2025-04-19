"""
Example dummy agent for the ForgeNews platform.
"""

import os

EXAMPLE_AGENT_API_KEY = os.getenv("EXAMPLE_AGENT_API_KEY", "")

def run():
    print(f"[example_agent] executed with API_KEY={EXAMPLE_AGENT_API_KEY}")
    return {"status": "success"}
