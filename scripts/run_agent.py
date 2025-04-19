#!/usr/bin/env python3
"""
CLI for running ForgeNews agents.
"""
import os
import sys
import argparse
import json

# Add the src directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root_dir, 'src'))

from core.ctrl import AGENT_REGISTRY, execute_agent


def main():
    parser = argparse.ArgumentParser(description="Run a ForgeNews agent via CLI")
    parser.add_argument("agent_name", help="Name of the agent to run")
    parser.add_argument("--interval_hours", type=int, default=24,
                        help="Minimum hours between subsequent runs of the same agent")
    args = parser.parse_args()

    if args.agent_name not in AGENT_REGISTRY:
        print(f"Agent '{args.agent_name}' not found.")
        sys.exit(1)

    agent_func = AGENT_REGISTRY[args.agent_name]
    result = execute_agent(agent_func, args.agent_name, args.interval_hours)
    print(json.dumps(result))


if __name__ == "__main__":
    main() 