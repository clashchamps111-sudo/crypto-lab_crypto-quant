"""SESSION 9 - perp kline history fetch (H09 basis model).

fapi /fapi/v1/klines, BTCUSDT, 1h, 2021-11-01 -> present, paginated with
sleep+retry (the funding-history fetch pattern that worked). Output:
data/BTCUSDT_perp_1h.csv (close marked at bar end; funding prints join at
their timestamp via the bar containing it - close of that bar is the exchange
mark used for basis at print time approximation, declared in h09 header).
"""
import json
import os
import time
import urllib.request

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(ROOT, "data", "BTCUSDT_perp_1h.csv")
URL = "https://fapi.binance.com/fapi/v1/klines"
T0 = int(pd.Timestamp("2021-11-01", tz="UTC").timestamp() * 1000)


def fetch_all():
    recs = []
    start = T0
    page = 0
    while True:
        u = f"{URL}?symbol=BTCUSDT&interval=1h&startTime={start}&limit=1000"
        for attempt in range(3):
            try:
                kl = json.loads(urllib.request.urlopen(u, timeout=30).read())
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"[fetch] retry {attempt + 1} page {page}: {e.__class__.__name__}")
                time.sleep(3)
        if not kl:
            break
        recs.extend(kl)
        page += 1
        if page % 10 == 0:
            print(f"[fetch] page {page}: {len(recs)} bars, last {pd.to_datetime(int(kl[-1][6]), unit='ms')}")
        if len(kl) < 1000:
            break
        nxt = int(kl[-1][6]) + 1
        if nxt <= start:
            break
        start = nxt
        time.sleep(0.7)
    df = pd.DataFrame(recs, columns=["openTime", "open", "high", "low", "close",
                                     "volume", "closeTime", "_", "__", "___", "____", "_____"])
    df["openTime"] = pd.to_datetime(df["openTime"], unit="ms")
    df["close"] = df["close"].astype(float)
    df = df[["openTime", "close"]].drop_duplicates("openTime").sort_values("openTime")
    df.to_csv(CSV, index=False)
    return df


def main():
    if os.path.exists(CSV):
        df = pd.read_csv(CSV, parse_dates=["openTime"])
        last = df["openTime"].max()
        if last >= pd.Timestamp.utcnow() - pd.Timedelta(days=3):
            print(f"[fetch] cached file current through {last}; nothing to do")
            return df
    df = fetch_all()
    print(f"[fetch] saved {len(df)} perp bars: {df['openTime'].min()} -> {df['openTime'].max()}")
    return df


if __name__ == "__main__":
    main()
