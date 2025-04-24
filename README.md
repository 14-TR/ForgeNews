# ForgeNews

ForgeNews is a modular, multi-agent system for global intelligence gathering in conflict, technology, AI, and financial domains. It features a FastAPI-based orchestrator with guardrails, agent registration, and logging.

## Features
- **Modular Agents**: Each agent (e.g., `example_agent`, `conflict_agent`) is independently developed and registered.
- **Orchestration**: Central `ctrl` engine manages execution state and scheduling.
- **Guardrails**: Input safety, relevance, and moderation checks with PII filtering.
- **API & CLI**: Run agents via HTTP (`/run-agent/`) or command line (`scripts/run_agent.py`).
- **Persistent Logging**: Tracks runs with timestamps, durations, and outcomes in `logs/runlog.json`.
- **Markets:** Stooq free quotes (CC-BY), US Federal Reserve FRED API (public-domain).

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

## SQLite Integration

Your `conflict_agent` now persists events to a local SQLite database at `src/db/conflict_data.db`. To seed and query:

1. Seed the database with ACLED events:
   ```bash
   python scripts/run_agent.py conflict_agent --interval_hours 0
   ```
2. Inspect the database:
   ```bash
   sqlite3 src/db/conflict_data.db
   .tables
   SELECT COUNT(*) FROM conflict_events;
   ```
3. Generate a report of the most recent events:
   ```bash
   python scripts/run_agent.py report_agent --interval_hours 0 > daily_report.json
   ```

## AI Narrative Reports

The `llm_report_agent` generates a detailed narrative based on the conflict summary using OpenAI. To configure and run:

1. Ensure AWS credentials and secret configurations:
   ```bash
   # AWS env vars or in your .env
   export AWS_ACCESS_KEY_ID=<your-access-key>
   export AWS_SECRET_ACCESS_KEY=<your-secret-key>
   export AWS_REGION=<your-aws-region>
   ```
   - Create or update a secret in AWS Secrets Manager named `open-ai` (or adjust `OPENAI_SECRET_NAME` in `aws_config.AWSConfig`) containing JSON:
     ```json
     {"OPENAI_API_KEY": "<your-openai-key>"}
     ```
2. (Optional) Override the OpenAI model in `.env`:
   ```env
   OPENAI_MODEL=gpt-4
   ```
3. Run the agent and save the narrative:
   ```bash
   python scripts/run_agent.py llm_report_agent --interval_hours 0
   ```
   The markdown report will be saved to `reports/report_<YYYYMMDD>.md`.

## Signal Scoring

Each `Insight` carries heuristic scores (`relevance`, `novelty`, `volatility`, `confidence`). Scoring logic lives in `src/scoring/`. Novelty uses a rolling 30-day TF-IDF-ish memory stored at `data/.novelty_index.json`.

- **Relevance**: Measures how well the content aligns with the domain's keywords
- **Novelty**: Tracks content uniqueness against recently seen content (30-day window)
- **Volatility**: For markets, measures the magnitude of price movements
- **Confidence**: Determined by a combination of relevance and novelty scores

You can adjust the novelty memory location in your `.env` file:
```env
FORGENEWS_NOVELTY_MEM=data/.novelty_index.json
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
