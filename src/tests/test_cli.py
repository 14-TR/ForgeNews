"""
Integration test for the run_agent.py CLI script using subprocess.
Runs a real agent from ``AGENT_REGISTRY`` to ensure the CLI works end to end.
"""
import os
import sys
import subprocess
import json


def test_cli_example_agent(monkeypatch):
    """Ensure CLI script executes ``ai_news_agent`` successfully."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    script = os.path.join(root, 'scripts', 'run_agent.py')

    # Ensure no previous state to avoid blocking on interval
    state_file = os.path.join(root, 'pipeline_state.json')
    if os.path.exists(state_file):
        os.remove(state_file)

    # Point PYTHONPATH to stub modules so heavy dependencies aren't required
    stub_dir = os.path.join(os.path.dirname(__file__), "stubs")
    env = os.environ.copy()
    env["PYTHONPATH"] = stub_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Execute the CLI script with ai_news_agent
    result = subprocess.run(
        [sys.executable, script, "--agent_name", "ai_news_agent", "--interval_hours", "0"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0

    # Parse the last line of output as JSON
    lines = result.stdout.strip().splitlines()
    json_line = lines[-1]
    data = json.loads(json_line)
    assert data.get("status") == "success"
