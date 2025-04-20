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
sys.path.insert(0, root_dir)

from src.core.ctrl import AGENT_REGISTRY, execute_agent


def main():
    parser = argparse.ArgumentParser(description="Run a ForgeNews agent via CLI")
    parser.add_argument("agent_name", help="Name of the agent to run")
    parser.add_argument("--interval_hours", type=int, default=24,
                        help="Minimum hours between subsequent runs of the same agent")
    parser.add_argument("--start_date", type=str, default=None,
                        help="Override ACLED_START_DATE (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, default=None,
                        help="Override ACLED_END_DATE (YYYY-MM-DD)")
    args = parser.parse_args()

    # Inject ACLED date overrides into environment if provided
    if args.start_date:
        os.environ["ACLED_START_DATE"] = args.start_date
    if args.end_date:
        os.environ["ACLED_END_DATE"] = args.end_date

    if args.agent_name not in AGENT_REGISTRY:
        print(f"Agent '{args.agent_name}' not found.")
        sys.exit(1)

    agent_func = AGENT_REGISTRY[args.agent_name]
    result = execute_agent(agent_func, args.agent_name, args.interval_hours)
    print(json.dumps(result))


if __name__ == "__main__":
    main() 