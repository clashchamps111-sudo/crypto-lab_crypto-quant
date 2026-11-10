"""Binance kline downloader + cache. Public market data, no API key needed."""
import os
import time

import pandas as pd
import requests

ENDPOINTS = [
    "https://api.binance.com",
    "https://data-api.binance.vision",  # public mirror; works where the main API_geo-blocks
]

COLS = ["OpenTime", "Open", "High", "Low", "Close", "Volume",
        "CloseTime", "QVol", "Trades", "TakerBase", "TakerQuote", "Ignore"]


def _fetch_from(base, symbol, interval, years):
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - int(years * 365 * 24 * 3600 * 1000)
    rows = []
    while start_ms < end_ms:
        r = requests.get(
            f"{base}/api/v3/klines",
            params=dict(symbol=symbol, interval=interval, startTime=start_ms, limit=1000),
            timeout=10,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows += batch
        start_ms = batch[-1][0] + 1
        time.sleep(0.12)
    if not rows:
        raise RuntimeError(f"empty response from {base}")
    df = pd.DataFrame(rows, columns=COLS)
    df["OpenTime"] = pd.to_datetime(df["OpenTime"], unit="ms")
    df = df.set_index("OpenTime").astype(float).sort_index()
    df.index.name = "Date"
    df = df[~df.index.duplicated(keep="first")]
    return df[["Open", "High", "Low", "Close", "Volume"]]


def fetch_klines(symbol, interval, years=2):
    for base in ENDPOINTS:
        try:
            return _fetch_from(base, symbol, interval, years)
        except Exception as e:
            print(f"[data] endpoint {base} failed: {e}")
    raise RuntimeError("All data endpoints failed. Check internet / geo-block.")


def load_or_fetch(symbol, interval, years=2, fresh_minutes=720, suffix=""):
    """Use cached CSV if younger than `fresh_minutes`, else download."""
    os.makedirs("data", exist_ok=True)
    path = os.path.join("data", f"{symbol}_{interval}{suffix}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
        age_min = (pd.Timestamp.now(tz="UTC").tz_localize(None) - df.index[-1]).total_seconds() / 60
        if age_min < fresh_minutes:
            print(f"[data] cache hit {path} ({len(df)} rows, {age_min:.0f} min old)")
            return df
    df = fetch_klines(symbol, interval, years)
    df.to_csv(path)
    print(f"[data] saved {path}: {len(df)} rows  {df.index[0]} -> {df.index[-1]}")
    return df


if __name__ == "__main__":
    for tf in ("1h", "4h"):
        load_or_fetch("BTCUSDT", tf)
        load_or_fetch("ETHUSDT", tf)
