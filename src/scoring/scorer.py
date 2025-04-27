from datetime import datetime, timedelta
from hashlib import md5
from textwrap import shorten
from collections import defaultdict
import re, math, os, json

# --- naive TF-IDF novelty memory (rolling 30-day) -----------
MEM_PATH = os.getenv("FORGENEWS_NOVELTY_MEM", "data/.novelty_index.json")
WINDOW_DAYS = 30

def _load_index():
    if os.path.exists(MEM_PATH):
        return json.loads(open(MEM_PATH).read())
    return {}

def _save_index(idx):
    os.makedirs(os.path.dirname(MEM_PATH), exist_ok=True)
    with open(MEM_PATH, "w") as f:
        json.dump(idx, f)

def novelty_score(text: str) -> float:
    idx = _load_index()
    today = datetime.utcnow().date().isoformat()
    words = {w.lower() for w in re.findall(r"\b\w{4,}\b", text)}
    seen = sum(1 for w in words if w in idx)
    score = 1 - (seen / max(1, len(words)))
    # update
    for w in words:
        idx.setdefault(w, []).append(today)
    # prune old
    cutoff = (datetime.utcnow() - timedelta(days=WINDOW_DAYS)).date().isoformat()
    for w in list(idx):
        idx[w] = [d for d in idx[w] if d >= cutoff]
        if not idx[w]:
            del idx[w]
    _save_index(idx)
    return round(score, 2)

# ---------- relevance (keyword overlap to domain keywords) ---------
DOMAIN_KEYWORDS = {
    "conflict": {"attack","troop","strike","protest","shell"},
    "ai": {"model","ai","llm","training","paper"},
    "markets": {"bond","yield","equity","price","index"}
}

def relevance_score(domain: str, text: str) -> float:
    base = DOMAIN_KEYWORDS[domain]
    overlap = sum(1 for w in base if w in text.lower())
    return round(min(1, overlap / len(base)), 2)

# ---------- volatility (markets only) ------------------------------
def volatility_score(change_percent: float) -> float:
    return round(min(1, abs(change_percent) / 5), 2)  # >5% day move = 1.0

# ---------- wrapper -------------------------------------------------
def score_insight(insight_dict: dict) -> dict:
    dom = insight_dict["domain"]
    txt = f"{insight_dict['title']} {insight_dict['body']}"
    insight_dict["novelty"] = novelty_score(txt)
    insight_dict["relevance"] = relevance_score(dom, txt)
    if dom == "markets":
        pct = insight_dict.get("change_pct", 0)
        insight_dict["volatility"] = volatility_score(pct)
    # simple confidence heuristic
    insight_dict["confidence"] = (
        "high" if insight_dict["relevance"] > 0.8 and insight_dict["novelty"] > 0.5 else
        "medium" if insight_dict["relevance"] > 0.5 else "low"
    )
    return insight_dict 