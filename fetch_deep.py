"""Pull 5 years of Binance klines as the deep dataset (suffix _deep).
Rationale: the 2y sample exhausted its fresh test window; H03 needs a genuinely
untouched final year. More data > more peeks at the same window."""
from data import load_or_fetch

if __name__ == "__main__":
    for sym in ("BTCUSDT", "ETHUSDT"):
        for tf in ("1h", "4h"):
            load_or_fetch(sym, tf, years=5, suffix="_deep")
