"""SESSION 10.6.1 - P2: CROSS-COIN STATISTICAL-ARB PAIRS (pre-registered).

Design is registered VERBATIM in JOURNAL (Session 10.6.1) BEFORE this
code exists. Summary:
- 45 unordered pairs screened on TRAIN daily ln-closes [start -> 2025-11-05):
  Engle-Granger ADF (const + 1 lag, plain OLS SE) on OLS-hedged spread;
  qualify iff t < -1.5 AND train hourly log-return corr >= 0.60; top 6.
- z-score of walk-forward spread (beta=1 unit or monthly refit OLS);
  rolling stats on trailing W bars SHIFT(1), full-window min_periods.
- Entry |z| >= z_in {2.0,2.5} (short rich leg / long cheap leg); exit
  |z| <= 0.5; ruin-stop |z| > 4.0; time stop 720 bars.
- Per $100 GROSS notional (legs $50/$50): 28bp matched RT fees, 3bp/day
  gross haircut, signed net funding = dir x $50 x (r_A - r_B) per print
  while held (exit-bar print included), realized-only verdicts.
- Train pick per pair (max train net, >= 8 train trades) -> frozen
  winner judged OOS [2025-11-05 -> end); z_in +-0.25 neighbors info.
- Four-bar table + mandatory regime split + funding-divergence tag.
"""
import os

import numpy as np
import pandas as pd

import audit as A

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")
DIRF = os.path.join(ROOT, "data", "funding_breadth")
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
         "DOGEUSDT", "ADAUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT"]

JUDGE = pd.Timestamp("2025-11-05")
GROSS, M = 100.0, 50.0
FEE = 0.0007
HAIRCUT_DAY = 0.0003
Z_OUT, Z_STOP = 0.5, 4.0
TIME_STOP = 720
W_LIST = [30 * 24, 90 * 24]
Z_IN_LIST = [2.0, 2.5]
BETA_MODES = ["unit", "ols"]
CORR_FLOOR, ADF_GATE, N_TOP = 0.60, -1.5, 6
W90 = 90 * 24

PX = FUND = None


def load_data():
    global PX, FUND
    if PX is not None:
        return
    cols = {}
    for s in COINS:
        cols[s] = A.load(s, "1h", "_deep")["Close"].astype(float)
    PX = pd.DataFrame(cols).sort_index()
    fr = {}
    for s in COINS:
        d = pd.read_csv(os.path.join(DIRF, f"usdt_{s}.csv"),
                        parse_dates=["fundingTime"]).sort_values("fundingTime")
        fr[s] = d.set_index("fundingTime")["r"]
    FUND = pd.DataFrame(fr).sort_index()


def pair_hourly(a, b):
    f = PX[[a, b]].dropna()
    return np.log(f)


def pair_daily(a, b):
    return np.log(PX[[a, b]].dropna().resample("1D").last()).dropna()


def eg_tstat(y, x):
    b = np.polyfit(x, y, 1)[0]
    s = y - b * x
    d = np.diff(s)
    Y = d[1:]
    X = np.column_stack([np.ones(len(Y)), s[1:-1], d[:-1]])
    coef = np.linalg.lstsq(X, Y, rcond=None)[0]
    resid = Y - X @ coef
    s2 = float(resid @ resid) / (len(Y) - X.shape[1])
    inv = np.linalg.inv(X.T @ X)
    t = float(coef[1]) / float(np.sqrt(s2 * inv[1, 1]))
    X1 = np.column_stack([np.ones(len(s) - 1), s[:-1]])
    rho = float(np.linalg.lstsq(X1, s[1:], rcond=None)[0][1])
    hl = -np.log(2.0) / np.log(rho) if 0.0 < rho < 1.0 else np.inf
    return t, float(hl)


def beta_series(lh, a, b):
    la, lb = lh[a], lh[b]
    idx = la.index
    mlab = np.asarray(idx.to_period("M").astype(np.int64))
    starts = np.flatnonzero(np.r_[True, mlab[1:] != mlab[:-1]])
    beta = np.full(len(idx), np.nan)
    for si, st in enumerate(starts):
        e = int(starts[si + 1]) if si + 1 < len(starts) else len(idx)
        lo = max(0, st - W90)
        ya, yb = la.values[lo:st], lb.values[lo:st]
        ok = np.isfinite(ya) & np.isfinite(yb)
        if ok.sum() < 100:
            continue
        cov = float(np.mean((ya[ok] - ya[ok].mean()) *
                            (yb[ok] - yb[ok].mean())))
        var = float(np.mean((yb[ok] - yb[ok].mean()) ** 2))
        if var <= 0:
            continue
        beta[st:e] = cov / var
    return pd.Series(beta, index=idx).ffill().bfill()   # bfill = warmup only


def run_pair(lh, a, b, W, z_in, beta_mode):
    la, lb = lh[a], lh[b]
    idx = la.index
    beta = (pd.Series(1.0, index=idx) if beta_mode == "unit"
            else beta_series(lh, a, b))
    s = la - beta * lb
    mu = s.rolling(W, min_periods=W).mean().shift(1)
    sd = s.rolling(W, min_periods=W).std(ddof=1).shift(1)
    zv = ((s - mu) / sd).replace([np.inf, -np.inf], np.nan).values
    av, bv = la.values, lb.values
    frv = (FUND[a].reindex(idx) - FUND[b].reindex(idx)).values
    n = len(idx)
    pos, e0, hold = 0, -1, 0
    fund_acc = hair_acc = 0.0
    hair_bar = HAIRCUT_DAY * GROSS / 24.0
    trades = []
    skipped = 0
    for t in range(n):
        if pos != 0:
            f = frv[t]
            if np.isfinite(f):
                fund_acc += pos * M * f
            else:
                skipped += 1
            hair_acc += hair_bar
            hold += 1
            zz = zv[t]
            reason = None
            if np.isfinite(zz):
                if abs(zz) <= Z_OUT:
                    reason = "z-out"
                elif abs(zz) >= Z_STOP:
                    reason = "z-stop"
            if hold >= TIME_STOP:
                reason = reason or "time-stop"
            if reason:
                dpa = av[t] / av[e0] - 1.0
                dpb = bv[t] / bv[e0] - 1.0
                price = pos * M * (dpb - dpa)
                net = price + fund_acc - hair_acc - 4 * FEE * M
                trades.append(dict(ts_in=idx[e0], ts_out=idx[t], i_out=t,
                                   dir=pos, price=price, fund=fund_acc,
                                   hair=hair_acc, net=net, bars=hold,
                                   reason=reason))
                pos, e0, hold = 0, -1, 0
                fund_acc = hair_acc = 0.0
        if pos == 0:
            zz = zv[t]
            if np.isfinite(zz) and abs(zz) >= z_in:
                pos = 1 if zz > 0 else -1
                e0 = t
                hold = 0
                fund_acc = hair_acc = 0.0
    stream = np.zeros(n)
    for tr in trades:
        stream[tr["i_out"]] = tr["net"]
    return trades, stream, skipped


def stream_mdd(stream, idx, start_ts):
    j = int(idx.searchsorted(start_ts))
    cs = stream[j:].cumsum()
    if not len(cs):
        return 0.0
    return float((cs - np.maximum.accumulate(cs)).min())


def tstats(trades):
    if not trades:
        return dict(n=0, net=0.0, pf=None, avg=0.0, fund=0.0, hair=0.0,
                    price=0.0)
    nets = np.array([t["net"] for t in trades])
    win = float(nets[nets > 0].sum())
    los = float(-nets[nets <= 0].sum())
    pf = (win / los) if los > 0 else None
    return dict(n=len(trades), net=float(nets.sum()), pf=pf,
                avg=float(nets.mean()),
                fund=float(sum(t["fund"] for t in trades)),
                hair=float(sum(t["hair"] for t in trades)),
                price=float(sum(t["price"] for t in trades)))


def fmt_pf(pf):
    return "inf" if pf is None else f"{pf:.2f}"


def regime_map():
    d = A.daily_df("BTCUSDT")
    ret30 = d["Close"].pct_change(30)
    month_end = d.groupby(pd.Grouper(freq="ME"))["Close"].last().dropna()
    lab = {}
    for m in month_end.index:
        r = float(ret30.asof(m))
        lab[pd.Timestamp(m).to_period("M")] = ("bull" if r >= 0.10 else
                                               "bear" if r <= -0.10 else
                                               "sideways")
    return lab


def buckets(jtrades, rmap):
    bk = {"bull": [0.0, 0], "sideways": [0.0, 0], "bear": [0.0, 0]}
    for t in jtrades:
        b = rmap.get(t["ts_in"].to_period("M"), "sideways")
        bk[b][0] += float(t["net"])
        bk[b][1] += 1
    return bk


def main():
    load_data()
    data_end = PX.index[-1]
    years = (data_end - JUDGE).total_seconds() / (365.25 * 86400)
    md = ["# P2 PAIRS REPORT (Session 10.6.1, pre-registered)", "",
          f"Data {PX.index[0]} -> {data_end} (1h); train [start -> "
          f"2025-11-05); judge [2025-11-05 -> end) ~ {years:.2f}y.",
          "Legs = USDT-M perps both sides; per $100 GROSS notional",
          "(legs $50/$50; per-capital = /2 conservative, hedged-margin",
          "advantage unmodeled). Costs: 28bp matched RT (7bp/side x4) +",
          "3bp/day gross haircut + signed net funding per print on entry",
          "notional (exit-bar print included). Realized-only verdicts.", ""]
    lh_cache = {}

    def L(a, b):
        if (a, b) not in lh_cache:
            lh_cache[(a, b)] = pair_hourly(a, b)
        return lh_cache[(a, b)]

    # ---------- screen ----------
    md += ["## Pair screen (TRAIN-ONLY)", "",
           "EG-ADF t on daily OLS-hedged train spread; qualify: t < -1.5 "
           f"AND hourly-return corr >= {CORR_FLOOR}; rank most-negative t.",
           "", "| A | B | ADF t | corr | HL (d) | qual |", "|---|---|---|---|---|---|"]
    rows = []
    for i in range(len(COINS)):
        for j in range(i + 1, len(COINS)):
            a, b = COINS[i], COINS[j]
            d = pair_daily(a, b)
            mtr = d.index < JUDGE
            t, hl = eg_tstat(d[a].values[mtr], d[b].values[mtr])
            r1 = L(a, b).diff().dropna()
            r1 = r1[r1.index < JUDGE]
            corr = float(r1[a].corr(r1[b]))
            rows.append((a, b, t, corr, hl))
    df = pd.DataFrame(rows, columns=["a", "b", "t", "corr", "hl"])
    df["q"] = (df["t"] < ADF_GATE) & (df["corr"] >= CORR_FLOOR)
    for _, r0 in df.sort_values("t").iterrows():
        md.append(f"| {r0['a']} | {r0['b']} | {r0['t']:+.2f} | "
                  f"{r0['corr']:+.2f} | "
                  + (f"{r0['hl']:.1f}" if np.isfinite(r0["hl"]) else "inf")
                  + f" | {'YES' if r0['q'] else '-'} |")
    q = df[df["q"]].sort_values("t").head(N_TOP)
    md += ["", f"- qualifiers: {int(df['q'].sum())}/45; selected top {len(q)} "
           "by most-negative t.", ""]
    print(f"[screen] qualifiers {int(df['q'].sum())}/45 -> top {len(q)}")

    verdict = None
    frozen = []
    if len(q) < 3:
        md += [f"**FAMILY VERDICT: EMPTY** (only {int(df.q.sum())} "
               "qualifiers < 3 minimum).", ""]
        verdict = "EMPTY"
    # ---------- per-pair battery ----------
    rmap = regime_map()
    for _, pr0 in q.iterrows():
        a, b = pr0["a"], pr0["b"]
        lh = L(a, b)
        md += [f"## {a} / {b}  (t {pr0['t']:+.2f}, corr {pr0['corr']:+.2f}, "
               f"HL {pr0['hl']:.1f}d)", "",
               "| W | beta | z_in | train net $ | train trips |",
               "|---|---|---|---|---|"]
        picks = []
        for W in W_LIST:
            for bm in BETA_MODES:
                for zi in Z_IN_LIST:
                    trades, _, _ = run_pair(lh, a, b, W, zi, bm)
                    st = tstats([t for t in trades if t["ts_in"] < JUDGE])
                    md.append(f"| {W // 24}d | {bm} | {zi:.2f} | "
                              f"{st['net']:+.2f} | {st['n']} |")
                    picks.append((st["net"], st["n"],
                                  dict(W=W, beta_mode=bm, z_in=zi)))
        ok = [p for p in picks if p[1] >= 8]
        if not ok:
            md += ["- NO-SIGNAL: no combo reaches the 8-train-trade floor "
                   "-> pair excluded from judge per pre-registration.", ""]
            continue
        best = max(ok, key=lambda p: p[0])
        c = best[2]
        md += ["", f"- TRAIN PICK: W={c['W'] // 24}d beta={c['beta_mode']} "
               f"z_in={c['z_in']:.2f} (train net {best[0]:+.2f}$ on "
               f"{best[1]} trips)", ""]
        trades, stream, skipped = run_pair(lh, a, b, c["W"], c["z_in"],
                                           c["beta_mode"])
        jtr = [t for t in trades if t["ts_in"] >= JUDGE]
        stj = tstats(jtr)
        mddj = stream_mdd(stream, lh.index, JUDGE)
        stj["mdd"] = mddj
        stj["skipped"] = skipped
        stj["reasons"] = {}
        for t in jtr:
            stj["reasons"][t["reason"]] = stj["reasons"].get(t["reason"], 0) + 1
        stj["bk"] = buckets(jtr, rmap)
        # funding-divergence tag (pre-registered)
        income_gross = (sum(max(t["price"], 0.0) for t in jtr) +
                        max(0.0, stj["fund"]))
        stj["ftag"] = (max(0.0, stj["fund"]) > 0.5 * income_gross
                       and income_gross > 0)
        # neighbors (informational)
        neigh = []
        for zn in (c["z_in"] - 0.25, c["z_in"] + 0.25):
            tn, sn_stream, _ = run_pair(lh, a, b, c["W"], zn, c["beta_mode"])
            sn = tstats([t for t in tn if t["ts_in"] >= JUDGE])
            sn["mdd"] = stream_mdd(sn_stream, lh.index, JUDGE)
            neigh.append((zn, sn))
        frozen.append(dict(a=a, b=b, c=c, stj=stj, train_net=best[0],
                           train_n=best[1], neigh=neigh, t=pr0.t,
                           corr=pr0.corr))
        pf_j = fmt_pf(stj["pf"])
        tag = " [FUNDING-DISGUISED]" if stj["ftag"] else ""
        md += [f"**JUDGE {c['W'] // 24}d/{c['beta_mode']}/z{c['z_in']:.2f}: "
               f"trips {stj['n']} | net {stj['net']:+.2f}$ "
               f"({stj['net'] / years:+.2f}%/yr gross) | PF {pf_j} | "
               f"avg/trade {stj['avg']:+.3f} | fund {stj['fund']:+.2f}$ "
               f"hair {stj['hair']:+.2f}$ | MDD {mddj:+.2f}$ | exits "
               f"{stj['reasons']}{tag}**", ""]
        nb_txt = "; ".join(f"z{zn:.2f}: {sn['n']} trips {sn['net']:+.2f}$ "
                           f"(MDD {sn['mdd']:+.2f})"
                           for zn, sn in neigh)
        md += [f"- Neighbors (informational): {nb_txt}",
               f"- Regime split (mandatory lens): " + "; ".join(
                   f"{k} {v[0]:+.2f}$ ({v[1]}t)" for k, v in stj["bk"].items()),
               ""]
        print(f"[pair] {a}/{b}: judge {stj['n']} trips, net "
              f"{stj['net']:+.2f}$/{years:.2f}y, fund {stj['fund']:+.2f}")

    if verdict != "EMPTY" and frozen:
        alive = [f for f in frozen if f["stj"]["n"] >= 8 and
                 f["stj"]["net"] > 0]
        pooled = sum(f["stj"]["net"] for f in frozen)
        pooled_n = sum(f["stj"]["n"] for f in frozen)
        best = max(frozen, key=lambda f: f["stj"]["net"] / max(years, 1e-9))
        ann_best = best["stj"]["net"] / years
        ann_pool = pooled / years
        md += ["## Verdict", "",
               f"- Frozen winners run: {len(frozen)}; ALIVE (net>0 AND >=8 "
               f"judge trades): {len(alive)}",
               f"- Pooled judge book: {pooled:+.2f}$ / {years:.2f}y = "
               f"{ann_pool:+.2f}%/yr gross ({pooled_n} trades total)",
               ""]
        md += ["### Four-bar table (per $100 GROSS notional; capital = /2)",
               "", "| Bar | Definition | Best winner "
               f"({best['a']}/{best['b']}) | Pooled six |", "|---|---|---|---|"]
        for nm, thr in (("A any-positive", None), ("B beats certified", 4.77),
                        ("C beats always-in", 6.82),
                        ("D double-digit capital", 20.0)):
            def bar(v):
                return ("PASS" if v > 0 else "FAIL") if thr is None else \
                    ("PASS" if v >= thr else "FAIL")
            lab = "net > 0" if thr is None else f">= {thr}%/yr"
            md.append(f"| {nm} | {lab} | {bar(ann_best)} ({ann_best:+.2f}) | "
                      f"{bar(ann_pool)} ({ann_pool:+.2f}) |")
        fam = ("ALIVE" if alive else
               "CLOSED - no winner cleared (net>0 AND >=8 judge trades)")
        if alive and not [f for f in alive if f["stj"]["n"]]:
            fam = "CLOSED - stat floor"
        md += ["", f"**P2 FAMILY VERDICT: {fam}**", ""]
        if alive:
            # brittleness flags
            for f in alive:
                if (f["neigh"][0][1]["net"] <= 0 and
                        f["neigh"][1][1]["net"] <= 0):
                    md.append(f"- BRITTLENESS flag {f['a']}/{f['b']}: "
                              "winner passes, both neighbors fail (S6-style "
                              "neighbor instability).")
            md.append("")
        verdict = fam
    path = os.path.join(OUT, "P2_pairs_report.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[P2] verdict: {verdict} -> {path}")


if __name__ == "__main__":
    main()
