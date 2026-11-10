"""Indicators: Wilder-style, computed by hand so there are zero TA-Lib dependencies.
All functions accept array-likes and return pandas Series or numpy arrays."""
import numpy as np
import pandas as pd


def ema(s, n):
    return pd.Series(s).ewm(span=n, adjust=False).mean()


def rsi_w(x, n=14):
    x = pd.Series(x).astype(float)
    d = x.diff()
    up = pd.Series(np.where(d > 0, d, 0.0), index=x.index).ewm(alpha=1.0 / n, adjust=False).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0), index=x.index).ewm(alpha=1.0 / n, adjust=False).mean()
    return 100.0 - 100.0 / (1.0 + up / (dn + 1e-12))


def atr_w(high, low, close, n=14):
    h, l, c = pd.Series(high), pd.Series(low), pd.Series(close)
    prev = c.shift(1)
    tr = pd.concat([h - l, (h - prev).abs(), (l - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def vwap_daily(df):
    """Session VWAP anchored on UTC days. Bar-local cumulative construction
    (numerator/denominator cumsum only up to the current bar) => lookahead-safe."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
    v = df["Volume"]
    day = df.index.normalize()
    num = (tp * v).groupby(day).cumsum()
    den = v.groupby(day).cumsum().replace(0.0, np.nan)
    return (num / den).to_numpy()


def vwap_sigma_daily(df):
    """Bar-local volume-weighted intraday sigma of (TP - VWAP), UTC-day anchored,
    same cumulative construction as vwap_daily => lookahead-safe."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
    v = df["Volume"]
    day = df.index.normalize()
    vwap = pd.Series(vwap_daily(df), index=df.index)
    sq = (tp - vwap) ** 2
    num = (sq * v).groupby(day).cumsum()
    den = v.groupby(day).cumsum().replace(0.0, np.nan)
    return num.div(den).pow(0.5).to_numpy()


def vwap_band_arrays(df, min_bars=3):
    """(vwap, sigma) with the first `min_bars` bars of each UTC day masked NaN:
    at 00:xx bars vwap ~ open and sigma ~ 0, which would fire pathological
    early-day signals. Applied consistently in train/test/folds."""
    day = df.index.normalize()
    day_start = df.index.to_series().dt.normalize()
    elapsed = df.index.hour  # UTC hour-of-day on 1h bars
    mask = elapsed < min_bars
    vwap = pd.Series(vwap_daily(df), index=df.index)
    sigma = pd.Series(vwap_sigma_daily(df), index=df.index)
    vwap[mask] = np.nan
    sigma[mask] = np.nan
    return vwap.to_numpy(), sigma.to_numpy()
