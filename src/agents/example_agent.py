"""
Example dummy agent for the ForgeNews platform.
"""

import os

def run():
    api_key = os.getenv("EXAMPLE_AGENT_API_KEY", "")
    print(f"[example_agent] executed with API_KEY={api_key}")
    return {"status": "success"}
