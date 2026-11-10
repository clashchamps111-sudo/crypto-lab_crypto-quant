"""Forensics for suspicious H06b gauntlet numbers (534 trades/yr vs audit-frame
baseline, fold-1 zero trades). Compares MARKET vs MAKER entry on (a) the deep
test-year folds and (b) the exact audit 6-month window; anatomizes maker fills
(hold length, win share, zero-bar holds, fill-vs-open spread)."""
import numpy as np
import pandas as pd

from backtesting import Backtest

import audit as A
import config as C
from strategies import ShortTrendPullback, MakerShortPullback

P = dict(n_fast=9, atr_stop=2.5, use_vwap=True)


def market_folds():
    df = A.load("BTCUSDT", "1h", "_deep")
    t0 = df.index[0]
    for i in range(4):
        a = t0 + pd.DateOffset(months=C.TRAIN_MONTHS + i * 3)
        b = t0 + pd.DateOffset(months=C.TRAIN_MONTHS + (i + 1) * 3)
        w = df[(df.index >= a) & (df.index < b)].copy()
        w["VWAP"] = A.vwap_daily(w)
        st = Backtest(w, type(f"MK{i}", (ShortTrendPullback,), {**P, "_vwap": w["VWAP"].to_numpy()}),
                      cash=C.CASH, commission=0.0002, exclusive_orders=True).run()
        t = st["_trades"]
        r = float(t["PnL"].sum()) if len(t) else 0.0
        print(f"MARKET fold{i + 1}: trades {len(t)} realized {r:+.2f} "
              f"Ret {float(st['Return [%]']):+.2f} PF {float(st['Profit Factor']):.2f}")


def window_twin():
    dvp = A.load("BTCUSDT", "1h", "")
    _, test = A.split_for(dvp, "")
    test = test.copy()
    test["VWAP"] = A.vwap_daily(test)
    mkt = Backtest(test, type("M1", (ShortTrendPullback,), {**P, "_vwap": test["VWAP"].to_numpy()}),
                   cash=C.CASH, commission=0.0002, exclusive_orders=True).run()
    mkr = Backtest(test, type("M2", (MakerShortPullback,), {**P, "_vwap": test["VWAP"].to_numpy()}),
                   cash=C.CASH, commission=0.0002, exclusive_orders=True).run()
    tm, tk = mkt["_trades"], mkr["_trades"]
    print(f"6mo-window twins: MARKET trades {len(tm)} ret {float(mkt['Return [%]']):+.2f} "
          f"| MAKER trades {len(tk)} ret {float(mkr['Return [%]']):+.2f}")
    if len(tk):
        hrs = tk["ExitBar"] - tk["EntryBar"]
        print(f"MAKER hold bars: med {int(hrs.median())} mean {float(hrs.mean()):.1f} "
              f"| zero/one-bar holds {int((hrs <= 1).sum())}")
        spreads = tm["EntryPrice"].mean() if len(tm) else np.nan
        print(f"MAKER win share {float((tk['PnL'] > 0).mean()):.3f}; "
              f"MARKET mean entry px ~{float(spreads):.5f} vs MAKER {float(tk['EntryPrice'].mean()):.5f}")
        # exit anatomy: SL-ish = pnl<0 big; TP-ish = +; time/regime = rest
        pnl = tk["PnL"]
        print(f"MAKER pnl quartiles: {tuple(round(float(q), 2) for q in pnl.quantile([0.25, 0.5, 0.75]))}")


if __name__ == "__main__":
    market_folds()
    window_twin()
