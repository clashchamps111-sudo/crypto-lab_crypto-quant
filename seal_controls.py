"""SESSION 7 OPENER - POSITIVE-CONTROLS RE-RUN SEAL.

Trigger (standing rule): 'positive controls re-run after any harness change.'
Since the Session 3 controls passed, the following grew WITHOUT touching the
engine path: strategies.py (added MakerMixIn/DonchianMaker/MakerShortPullback;
DailyMomentum/DailyRegime untouched; VwapBandReversion added S5),
indicators.py (added vwap_sigma_daily/vwap_band_arrays; originals untouched),
and five new runner scripts. config.py constants verified unchanged
(CASH=100, 7bp/side, 1x, PATH... PRICE_SCALE=1e6, kill rails).
This re-run calls audit.positive_controls() byte-for-byte unmodified and
compares against the Session 3 stored stamp (out/audit_report.md):
  H00a: params n_sma=100, n_roc=30 | Test Ret +4.29% (net +1.27%) | 4/4 gates
  H00b: params n_sma=150           | Test Ret +8.32% (net +7.63%) | 4/4 gates
  Freeze decision: BOTH PASS
SEAL criterion: freeze == BOTH PASS AND H00a identity numbers identical to S3
to the last 2dp (H00b reported for record; its S3 stamp was PASS-but-fragile
under realized-only accounting - unchanged standard).
"""
import os
import re

import pandas as pd

import audit as A
import config as C

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out")

S3 = {  # stored Session 3 stamp
    "H00a": dict(params="n_sma=100, n_roc=30", ret=4.29, net=1.27),
    "H00b": dict(params="n_sma=150", ret=8.32, net=7.63),
}


def data_integrity(md):
    df = A.load("BTCUSDT", "1h", "_deep")
    fund = pd.read_csv(os.path.join(ROOT, "data", "funding_BTCUSDT.csv"))
    md += ["## Data integrity", "",
           f"- BTCUSDT_1h_deep: {len(df)} rows, {df.index[0]} -> {df.index[-1]}",
           f"- funding_BTCUSDT.csv: {len(fund)} prints", ""]
    return dict(btc_rows=len(df), fund_rows=len(fund))


def parse_controls(md_ready):
    out = {}
    for tag in ("H00a", "H00b"):
        m = re.search(rf"### H00[a-b][^\n]*\n[^\n]*\n[^\n]*", md_ready)
        pm = re.search(rf"### {tag}[^:]*\(params: ([^)]+)\)", md_ready)
        sm = re.search(rf"### {tag}.*?Test stats: Ret (-?\d+\.\d+)%", md_ready, re.S)
        nm = re.search(rf"### {tag}.*?NET Ret (-?\d+\.\d+)%", md_ready, re.S)
        gm = re.search(rf"### {tag}.*?Gates: (.+)", md_ready, re.S)
        out[tag] = dict(params=pm.group(1) if pm else "?",
                        ret=float(sm.group(1)) if sm else None,
                        net=float(nm.group(1)) if nm else None,
                        gates=gm.group(1) if gm else "?")
    fz = re.search(r"Freeze decision: (.+)", md_ready)
    out["freeze"] = fz.group(1).strip() if fz else "?"
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    md = ["# POSITIVE-CONTROLS RE-RUN SEAL (Session 7 opener)", "",
          "Provenance: standing rule 'controls re-run after any harness change'.",
          "Triggers since S3: strategies.py/indicators.py grew (additive only),",
          "5 new runners added; engine constants untouched (verified in header).",
          "Method: audit.positive_controls() called EXACTLY as in S3; zero edits",
          "to audit.py, strategies.py control classes, indicators core, config.",
          "", "Expected S3 stamp: H00a Ret +4.29% (net +1.27%) 4/4 gates; "
          "H00b Ret +8.32% (net +7.63%) 4/4 gates; BOTH PASS.", ""]
    di = data_integrity(md)
    md2 = []
    freeze = A.positive_controls(md2)
    md += md2

    got = parse_controls("\n".join(md))
    checks = []
    for tag in ("H00a", "H00b"):
        g, s = got[tag], S3[tag]
        same_params = g["params"].replace(" ", "") == s["params"].replace(" ", "")
        same_ret = g["ret"] is not None and abs(g["ret"] - s["ret"]) < 0.005
        same_net = g["net"] is not None and abs(g["net"] - s["net"]) < 0.005
        checks.append((tag, same_params, same_ret, same_net,
                       f"S3: Ret {s['ret']:+.2f} net {s['net']:+.2f} | "
                       f"re-run: Ret {g['ret']:+.2f} net {g['net']:+.2f}, gates: {g['gates']}"))
    ok_h00a = checks[0][1] and checks[0][2] and checks[0][3]
    seal = (freeze == "BOTH PASS -> machine can certify green. Prior verdicts STAND."
            and ok_h00a)

    md += ["## Comparison vs Session 3 stamp", ""]
    for tag, _, _, _, msg in checks:
        md.append(f"- {tag}: {msg}")
    md += [f"- Freeze decision (re-run): {freeze}",
           f"- H00a identity match (params/Ret/NET all within 0.005): {'YES' if ok_h00a else 'NO'}",
           "",
           f"**SEAL: {'PASS - harness certified green; all Session 3-6 verdicts STAND.' if seal else 'FAIL - freeze all further testing until explained.'}**",
           "",
           f"Integrity: BTC deep {di['btc_rows']} rows, funding {di['fund_rows']} prints.",
           ""]
    path = os.path.join(OUT, "controls_rerun_seal.md")
    open(path, "w", encoding="utf-8").write("\n".join(md))
    print(f"[seal] freeze: {freeze}")
    print(f"[seal] H00a match: {ok_h00a} | H00b match: "
          f"{checks[1][1] and checks[1][2] and checks[1][3]}")
    print(f"[seal] verdict: {'SEAL PASS' if seal else 'SEAL FAIL'}")
    print(f"[seal] written: {path}")


if __name__ == "__main__":
    main()
