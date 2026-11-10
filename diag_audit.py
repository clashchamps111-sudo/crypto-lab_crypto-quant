"""Session 3 addendum diagnostics (run right after audit.py):
1. M2M split for the positive controls: does 'Return [%]' come from REALIZED
   closed-trade PnL or from a position still OPEN at the window cutoff?
   (Found: backtesting.py echoes open-position mark-to-market into Return but
   excludes it from _trades / Profit Factor / Exposure Time.)
2. Full trade anatomy of the two maker-alive cost-matrix survivors (H02b 1h
   short, H03 1h deep Donchian) at 2bp vs 7bp - input for the flip stamps.
Writes findings to stdout; interpretation goes into JOURNAL.md Session 3."""
import os

import numpy as np
import pandas as pd

from backtesting import Backtest

import config as C
from strategies import DailyMomentum, DailyRegime, DonchianBreakout, ShortTrendPullback

import audit as A


def m2m_split(st):
    t = st["_trades"]
    realized = float(t["PnL"].sum()) if len(t) else 0.0
    final = float(st["_equity_curve"]["Equity"].iloc[-1])
    m2m = final - C.CASH
    return realized, m2m - realized


def controls():
    df = A.daily_df("BTCUSDT")
    ts = df.index[0] + pd.DateOffset(months=C.TRAIN_MONTHS)
    te = ts + pd.DateOffset(months=C.TEST_MONTHS)
    test = df[(df.index >= ts) & (df.index < te)]
    print("== CONTROLS: realized vs unrealized (open-at-cutoff) ==")
    for tag, cls, params in [("H00a", DailyMomentum, dict(n_sma=100, n_roc=30)),
                             ("H00b", DailyRegime, dict(n_sma=150))]:
        bt = Backtest(test, type(tag, (cls,), params), cash=C.CASH,
                      commission=0.0003, exclusive_orders=True)
        st = bt.run()
        realized, unreal = m2m_split(st)
        ret = float(st["Return [%]"])
        print(f"{tag}: M2M {ret:+.2f}% | realized ${realized:+.2f} | "
              f"unrealized(open@cutoff) ${unreal:+.2f} | closed trades {int(st['# Trades'])}")


def candidates():
    print("\n== MAKER-ALIVE CANDIDATES: trade anatomy ==")

    def one(tag, tf, suf, cls, params, comm):
        df = A.load("BTCUSDT", tf, suf)
        _, test = A.split_for(df, suf)
        if params.get("use_vwap"):
            df["VWAP"] = A.vwap_daily(df)
            _, test = A.split_for(df, suf)
            params = dict(params)
            params["_vwap"] = test["VWAP"].to_numpy()
        bt = Backtest(test, type(f"HP_{tag.split()[0]}", (cls,), params),
                      cash=C.CASH, commission=comm, exclusive_orders=True)
        st = bt.run()
        t = st["_trades"]
        realized, unreal = m2m_split(st)
        holds = t["ExitBar"] - t["EntryBar"] if len(t) else []
        print(f"{tag} @{comm * 10000:.0f}bp: Ret {float(st['Return [%]']):+.2f}% "
              f"Sharpe {float(st['Sharpe Ratio']):+.2f} MaxDD {float(st['Max. Drawdown [%]']):.2f}% "
              f"PF {float(st['Profit Factor']):.2f} Trades {int(st['# Trades'])} "
              f"Win {float(st['Win Rate [%]']):.0f}% | realized ${realized:+.2f} "
              f"unreal ${unreal:+.2f} | med hold {int(np.median(holds)) if len(holds) else 'n/a'} bars")

    one("H02b 1h", "1h", "", ShortTrendPullback,
        dict(n_fast=9, atr_stop=2.5, use_vwap=True), 0.0002)
    one("H02b 1h", "1h", "", ShortTrendPullback,
        dict(n_fast=9, atr_stop=2.5, use_vwap=True), 0.0007)
    one("H03 1h deep", "1h", "_deep", DonchianBreakout,
        dict(n_enter=20, n_exit=10, atr_stop=3.0), 0.0002)
    one("H03 1h deep", "1h", "_deep", DonchianBreakout,
        dict(n_enter=20, n_exit=10, atr_stop=3.0), 0.0007)


if __name__ == "__main__":
    controls()
    candidates()
