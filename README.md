# ForgeNews

ForgeNews is a modular, multi-agent system for global intelligence gathering in conflict, technology, AI, and financial domains. It features a FastAPI-based orchestrator with guardrails, agent registration, and logging.

## Features
- **Modular Agents**: Each agent (e.g., `example_agent`, `conflict_agent`) is independently developed and registered.
- **Orchestration**: Central `ctrl` engine manages execution state and scheduling.
- **Guardrails**: Input safety, relevance, and moderation checks with PII filtering.
- **API & CLI**: Run agents via HTTP (`/run-agent/`) or command line (`scripts/run_agent.py`).
- **Persistent Logging**: Tracks runs with timestamps, durations, and outcomes in `logs/runlog.json`.

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/ForgeNews.git
   cd ForgeNews
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate    # macOS/Linux
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```env
   ACLED_API_KEY=your_acled_api_key
   ACLED_EMAIL=your_login_email
   EXAMPLE_AGENT_API_KEY=your_example_agent_key
   ```

## Running the HTTP API
1. Start the server:
   ```bash
   uvicorn api.main:app --reload
   ```
2. Call the `/run-agent/` endpoint:
   ```bash
   curl -X POST http://localhost:8000/run-agent/ \
     -H 'Content-Type: application/json' \
     -d '{"agent_name": "conflict_agent","input_text": "Test"}'
   ```

## Using the CLI
```bash
python scripts/run_agent.py conflict_agent --interval_hours 12
```

## Testing
Run the test suite:
```bash
pytest src/tests
```

## Next Steps
- Scale existing agents with more advanced logic
- Finalize guardrails and tool metadata
- Expand test coverage
