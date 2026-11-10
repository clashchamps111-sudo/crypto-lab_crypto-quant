"""Universe widening - fetch 5y spot klines (1h) for the 8 new basket symbols.
Pre-registered in JOURNAL Session 6. BTC/ETH deep files already exist."""
from data import load_or_fetch

UNIVERSE = ["BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
            "ADAUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT"]

if __name__ == "__main__":
    for sym in UNIVERSE:
        if sym == "BTCUSDT":
            continue
        try:
            load_or_fetch(sym, "1h", years=5, suffix="_deep")
        except Exception as e:
            print(f"[fetch] {sym} FAILED: {e}")
