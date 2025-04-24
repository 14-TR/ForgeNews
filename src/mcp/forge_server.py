"""
ForgeNews MCP Server – 3 tools + 1 prompt
Run with:  python -m src.mcp.forge_server
"""

from mcp.server.fastmcp import FastMCP, Image, Context
from datetime import datetime
from pathlib import Path
import json

mcp = FastMCP("ForgeNews")

DATA_DIR = Path("data/processed")

# ---------- helper -------------------------------------------------
def _load_latest(fname_glob: str) -> list[dict]:
    files = sorted(DATA_DIR.glob(fname_glob), reverse=True)
    if not files:
        return []
    return json.loads(files[0].read_text())

@mcp.tool()
def get_insights(domain: str = "all", limit: int = 10) -> list[dict]:
    """Return the most recent scored insights.
    Args:
        domain: "conflict" | "ai" | "markets" | "global" | "all"
        limit:  max rows to return
    """
    recs = _load_latest("insights_*.json")
    if domain != "all":
        recs = [r for r in recs if r["domain"] == domain]
    return recs[:limit]

@mcp.tool()
def generate_daily_brief() -> str:
    """Produce today's HTML brief (returns as string)."""
    brief_path = Path("reports") / f"brief_{datetime.utcnow():%Y%m%d}.html"
    if not brief_path.exists():
        raise FileNotFoundError("Brief not generated yet. Run pipeline first.")
    return brief_path.read_text()

from src.scoring.scorer import score_insight

@mcp.tool()
def score_text(domain: str, title: str, body: str) -> dict:
    """Score an arbitrary headline/body using ForgeNews heuristics."""
    base = {
        "domain": domain,
        "title": title,
        "body": body,
        "source_id": "ad-hoc",
        "event_date": datetime.utcnow().date().isoformat()
    }
    return score_insight(base)

from mcp.server.fastmcp.prompts import base

@mcp.prompt()
def quick_summary(headline: str, body: str) -> list[base.Message]:
    """LLM prompt template that produces a one-sentence TL;DR."""
    return [
        base.UserMessage(
            f"Summarize in 1 crisp sentence:\n\nHeadline: {headline}\n\n{body}"
        )
    ]

if __name__ == "__main__":
    mcp.run() 