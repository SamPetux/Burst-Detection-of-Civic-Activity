"""Confirmatory analysis of H1-H3 exactly as frozen in docs/06_confirmatory_protocol.md."""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

MS = ["chronos2", "nb_seasonal", "robust_z", "seasonal_z", "cusum"]
BINS, LABELS = [0, 0.3, 1, 5, np.inf], ["0.05-0.3", "0.3-1", "1-5", ">5"]
LO, HI = 0.005, 0.02


def mcnemar(a: pd.Series, b: pd.Series) -> tuple[int, int, float]:
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(n10, n10 + n01, 0.5).pvalue if n10 + n01 else 1.0
    return n10, n01, p


def h1(rates: str) -> dict:
    r = pd.read_csv(rates)
    r = r[r.rate_per_hour >= 0.05].copy()
    r["stratum"] = pd.cut(r.rate_per_hour, BINS, labels=LABELS)
    inb = {m: r[f"nominal_{m}"].between(LO, HI) for m in MS}
    by = []
    for s, g in r.groupby("stratum", observed=True):
        by.append({"stratum": s, "n": len(g), **{m: round(inb[m][g.index].mean(), 3) for m in MS}})
    crit = all(row["chronos2"] >= 0.8 for row in by if row["n"] >= 3)
    signs = {}
    for m in MS[1:]:
        a, b = inb["chronos2"], inb[m]
        n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
        signs[m] = {"chronos_only": n10, "baseline_only": n01,
                    "p_one_sided": binomtest(n10, n10 + n01, 0.5, alternative="greater").pvalue if n10 + n01 else 1.0}
    rho = {m: spearmanr(r.rate_per_hour, r[f"nominal_{m}"]).statistic for m in MS}
    return {"n_series": len(r), "share_in_band": {m: round(inb[m].mean(), 3) for m in MS},
            "median_rate_pct": {m: round(r[f"nominal_{m}"].median() * 100, 2) for m in MS},
            "by_stratum": by, "criterion_80pct": crit, "sign_tests": signs, "spearman": rho}


def h2(inj: str, rates: str) -> dict:
    d = pd.read_csv(inj).merge(pd.read_csv(rates)[["series", "rate_per_hour"]], on="series")
    d["stratum"] = pd.cut(d.rate_per_hour, BINS, labels=LABELS)
    det = {m: d[f"det_calib_{m}"].astype(bool) for m in MS}
    rows = []
    for s, g in d.groupby("stratum", observed=True):
        pd_ = {m: det[m][g.index].mean() for m in MS}
        best = max(MS[1:], key=lambda m: pd_[m])
        short = g[g.D <= 3]
        med = {m: short.loc[det[m][short.index], f"delay_calib_{m}"].median() for m in (MS[0], best)}
        rows.append({"stratum": s, "n_inj": len(g), **{m: round(pd_[m], 3) for m in MS}, "best": best,
                     "pd_ok": pd_["chronos2"] >= pd_[best] - 0.02,
                     "delay_chronos2": med["chronos2"], "delay_best": med[best],
                     "delay_ok": med["chronos2"] <= med[best]})
    n_ok = sum(r_["pd_ok"] and r_["delay_ok"] for r_ in rows)
    grid = d.groupby(["A", "D"])[[f"det_calib_{m}" for m in MS]].mean().round(3)
    return {"by_stratum": rows, "strata_passing": n_ok, "criterion": n_ok >= 3,
            "overall_pd": {m: round(det[m].mean(), 3) for m in MS},
            "mcnemar_vs_nb": dict(zip(["chronos_only", "nb_only", "p"], mcnemar(det["chronos2"], det["nb_seasonal"]))),
            "grid": grid.reset_index().to_dict("records")}


def h3(contam: str, rates_w: str, rates_none: str) -> dict:
    d = pd.read_csv(contam)
    on, off = d[d["first"]].reset_index(drop=True), d[~d["first"]].reset_index(drop=True)
    assert (on[["series", "gap", "A2"]].values == off[["series", "gap", "A2"]].values).all()
    c = "chronos2_{}_calib"
    a_ = mcnemar(off[c.format("none")], on[c.format("none")])
    b_ = mcnemar(on[c.format("winsor")], on[c.format("none")])
    w, n = pd.read_csv(rates_w), pd.read_csv(rates_none)
    keep = w.rate_per_hour >= 0.05
    diff_pp = (w.nominal_chronos2[keep].mean() - n.nominal_chronos2[keep].mean()) * 100
    cols = [x for x in d.columns if x not in ("series", "gap", "A2", "first")]
    tab = d.groupby(["first", "gap"])[cols].mean().round(3)
    return {"n_pairs": len(on),
            "a_contamination": {"clean_only": a_[0], "contaminated_only": a_[1], "p": a_[2], "ok": a_[0] > a_[1]},
            "b_winsor_vs_none": {"winsor_only": b_[0], "none_only": b_[1], "p": b_[2], "ok": b_[0] > b_[1]},
            "c_rate_diff_pp": diff_pp, "c_ok": abs(diff_pp) <= 0.5,
            "pd_table": tab.reset_index().to_dict("records")}


def holm(ps: dict) -> dict:
    items, out, run = sorted(ps.items(), key=lambda kv: kv[1]), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, p * (len(items) - i)))
        out[k] = run
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="results/confirm")
    ap.add_argument("--out", default="results/confirm/summary.json")
    a = ap.parse_args()
    res = {"H1": h1(f"{a.prefix}_h1_alarm_rates.csv"),
           "H2": h2(f"{a.prefix}_h2_injections.csv", f"{a.prefix}_h1_alarm_rates.csv")}
    from pathlib import Path
    if Path(f"{a.prefix}_h3.csv").exists():
        res["H3"] = h3(f"{a.prefix}_h3.csv", f"{a.prefix}_h1_alarm_rates.csv", f"{a.prefix}_h1_none_alarm_rates.csv")
    json.dump(res, open(a.out, "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
