import pandas as pd
import requests, io

BASE = "https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"

def fetch(symbol="^spx"):
    url = BASE.format(symbol=symbol.lower())
    csv_bytes = requests.get(url, timeout=15).content
    df = pd.read_csv(io.BytesIO(csv_bytes))
    return df.to_dict(orient="records")

def normalize(raw):
    norm = []
    for row in raw:
        norm.append({
            "source": "stooq",
            "symbol": row["Symbol"],
            "date": row["Date"],
            "open": row["Open"],
            "close": row["Close"],
            "high": row["High"],
            "low": row["Low"],
            "volume": row["Volume"]
        })
    return norm 