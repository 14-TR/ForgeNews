from src.scoring.scorer import score_insight

def test_score_bounds():
    base = score_insight({
        "domain":"ai",
        "title":"OpenAI launches new model",
        "body":"OpenAI announced...",
        "source_id":"test",
        "event_date":"2025-04-23"
    })
    for k in ("relevance","novelty"):
        assert 0 <= base[k] <= 1
        
def test_market_volatility():
    market = score_insight({
        "domain":"markets",
        "title":"S&P 500 up 2%",
        "body":"The S&P 500 index rose 2% today.",
        "source_id":"test",
        "event_date":"2025-04-23",
        "change_pct": 2.5
    })
    assert 0 <= market["volatility"] <= 1
    assert market["volatility"] > 0  # Should be non-zero for 2.5% change

def test_confidence_levels():
    # High confidence test
    high = score_insight({
        "domain":"ai",
        "title":"OpenAI launches new AI model",
        "body":"OpenAI announced a new large language model (LLM) today with advanced training.",
        "source_id":"test",
        "event_date":"2025-04-23"
    })
    # Above should have high relevance and novelty due to keywords
    
    # Low confidence test
    low = score_insight({
        "domain":"conflict",
        "title":"Weather report",
        "body":"Sunny conditions expected tomorrow.",
        "source_id":"test",
        "event_date":"2025-04-23"
    })
    # Above should have low relevance as keywords don't match domain
    
    assert high["confidence"] in ["low", "medium", "high"]
    assert low["confidence"] in ["low", "medium", "high"]
    # Should be different confidence levels
    assert high["relevance"] > low["relevance"] 