#!/usr/bin/env python3
"""
Ctrl Agent: orchestrates summary persistence and LLM narrative generation.
"""
import os
import sys
from typing import Dict, Any

# Add the parent directory to the Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.agents.report_agent import run as report_run
from src.agents.llm_report_agent import run as llm_run

def run() -> Dict[str, Any]:
    # Generate and persist summary JSON
    summary = report_run()
    # Generate narrative report via LLM based on the summary
    llm_result = llm_run()
    return {
        "status": llm_result.get("status", "failure"),
        "summary": summary,
        "narrative": llm_result.get("report"),
        "file": llm_result.get("file")
    } 