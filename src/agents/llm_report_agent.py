#!/usr/bin/env python3
import os
import sys
# Ensure project root is on sys.path for aws_secret_mgt import
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)
sys.path.insert(1, os.path.join(root_dir, 'src'))
"""
LLM Report Agent: expands summary into a narrative via OpenAI.
"""
import openai

from aws_secret_mgt import AWSSecretManager
from typing import Dict, Any
import json
import glob

# Initialize AWS secret manager and load OpenAI API key
secret_manager = AWSSecretManager()
api_key = secret_manager.get_openai_api_key() or os.getenv('OPENAI_API_KEY')
openai.api_key = api_key
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def run() -> Dict[str, Any]:
    """Entrypoint for generating a narrative report via LLM"""
    # Load the most recent summary JSON
    processed_dir = os.path.join(os.getcwd(), "data", "processed")
    pattern = os.path.join(processed_dir, "summary_*.json")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No summary JSON found in {processed_dir}")
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r", encoding="utf-8") as f:
        summary = json.load(f)
    period = summary.get("period", "Unknown Period")
    prompt_lines = [
        "You are an expert conflict analyst. Produce a detailed narrative report based on the following summary.",
        f"Period: {period}",
        "",
        "Summary of events:"
    ]
    for item in summary.get("summary", []):
        prompt_lines.append(f"- {item['type']}: {item['count']} events, {item['fatalities']} fatalities")
    prompt_lines.append("")
    prompt_lines.append("Please write a detailed report (~300 words).")
    prompt = "\n".join(prompt_lines)

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=600
    )
    report_text = response.choices[0].message.content

    # Save the report to file
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/report_{period.replace(' to ','_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    return {"status": "success", "report": report_text, "file": filename} 