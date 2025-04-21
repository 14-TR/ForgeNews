#!/usr/bin/env python3
"""
CLI for running ForgeNews agents.
"""
import os
import sys
import argparse
import json
import traceback

# Add the src directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from src.core.ctrl import AGENT_REGISTRY, execute_agent

# Define the pipeline sequence
PIPELINE_SEQUENCE = [
    "conflict_agent",
    "insight_agent",
    "llm_report_agent",
    "substack_agent"
]

def main():
    parser = argparse.ArgumentParser(description="Run the full ForgeNews agent pipeline or a specific agent.")
    # Optional: Run a specific agent instead of the full pipeline
    parser.add_argument("--agent_name", help="Name of a specific agent to run instead of the full pipeline", default=None)
    parser.add_argument("--interval_hours", type=int, default=24,
                        help="Minimum hours between subsequent runs (applies when running a single agent or the full pipeline)")
    parser.add_argument("--allow_high_risk", action='store_true', # Changed to boolean flag
                        help="Allow agents with high-risk tools to run")
    parser.add_argument("--force_run", action='store_true', # Added flag to force run
                        help="Force run agents even if interval hasn't passed (sets interval_hours to 0)")
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

    run_interval = 0 if args.force_run else args.interval_hours

    if args.agent_name:
        # Run a single specified agent
        if args.agent_name not in AGENT_REGISTRY:
            print(f"Agent '{args.agent_name}' not found.")
            sys.exit(1)
        print(f"--- Running single agent: {args.agent_name} ---")
        agent_func = AGENT_REGISTRY[args.agent_name]
        result = execute_agent(agent_func, args.agent_name, run_interval, args.allow_high_risk)
        print(json.dumps(result))
    else:
        # Run the full pipeline sequence
        print("--- Running full pipeline ---")
        pipeline_results = {}
        for agent_name in PIPELINE_SEQUENCE:
            print(f"--- Executing: {agent_name} ---")
            if agent_name not in AGENT_REGISTRY:
                print(f"Agent '{agent_name}' not found in registry. Skipping.")
                pipeline_results[agent_name] = {"status": "not_found"}
                continue
            
            agent_func = AGENT_REGISTRY[agent_name]
            try:
                result = execute_agent(agent_func, agent_name, run_interval, args.allow_high_risk)
                print(f"Result for {agent_name}: {json.dumps(result)}")
                pipeline_results[agent_name] = result
                # Optional: Add logic here to stop pipeline if a step fails crucial output
                # if result.get('status') != 'success': # Example check
                #     print(f"Agent {agent_name} did not succeed. Stopping pipeline.")
                #     break 
            except Exception as e:
                print(f"Error executing agent {agent_name}: {e}")
                print("--- Full Traceback (from run_agent.py) ---")
                traceback.print_exc(file=sys.stdout)
                print("--- End Traceback ---")
                pipeline_results[agent_name] = {"status": "exception", "error": str(e)}
                # Optional: Decide whether to stop the pipeline on exception
                # break 
        print("--- Pipeline finished ---")
        print("Pipeline Summary:")
        print(json.dumps(pipeline_results, indent=2))

if __name__ == "__main__":
    main() 