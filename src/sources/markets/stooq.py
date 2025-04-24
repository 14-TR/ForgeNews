import pandas as pd
import requests, io
from src.scoring.scorer import score_insight

BASE = "https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"

def fetch(symbol="^spx"):
    url = BASE.format(symbol=symbol.lower())
    csv_bytes = requests.get(url, timeout=15).content
    df = pd.read_csv(io.BytesIO(csv_bytes))
    return df.to_dict(orient="records")

def normalize(raw):
    norm = []
    for row in raw:
        # Calculate percentage change
        change_pct = 0
        if row["Open"] > 0:
            change_pct = (row["Close"] - row["Open"]) / row["Open"] * 100
        
        title = f"{row['Symbol']} moved {change_pct:.2f}% on {row['Date']}"
        body = f"Open: {row['Open']}, Close: {row['Close']}, High: {row['High']}, Low: {row['Low']}, Volume: {row['Volume']}"
        
        norm.append(score_insight({
            "domain": "markets",
            "title": title,
            "body": body,
            "source_id": "stooq",
            "event_date": row["Date"],
            "symbol": row["Symbol"],
            "open": row["Open"],
            "close": row["Close"],
            "high": row["High"],
            "low": row["Low"],
            "volume": row["Volume"],
            "change_pct": change_pct
        }))
    return norm 