"""
Integration test for CLI script run_agent.py using subprocess to invoke example_agent.
"""
import os
import sys
import subprocess
import json


def test_cli_example_agent(monkeypatch):
    """Ensure CLI script returns correct JSON output for example_agent."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    script = os.path.join(root, 'scripts', 'run_agent.py')

    # Ensure no previous state to avoid blocking on interval
    state_file = os.path.join(root, 'pipeline_state.json')
    if os.path.exists(state_file):
        os.remove(state_file)

    # Ensure environment variable is set
    monkeypatch.setenv("EXAMPLE_AGENT_API_KEY", "KEY123")

    # Execute the CLI script
    result = subprocess.run([sys.executable, script, 'example_agent'], capture_output=True, text=True)
    assert result.returncode == 0

    # Parse the last line of output as JSON
    lines = result.stdout.strip().splitlines()
    json_line = lines[-1]
    data = json.loads(json_line)
    assert data == {"status": "success"} 