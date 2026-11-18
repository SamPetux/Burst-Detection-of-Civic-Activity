"""H3: does a burst in the context reduce Chronos-2 sensitivity to a second burst, and does
context sanitisation (flagged hours replaced by the forecast median) restore it?

Design per job: first burst (A1, D1) at t0, second burst (A2, D2) at t0 + gap. Compared with the
same second burst without the first one. Thresholds: per-series calibrated to alpha on the
calibration period (same rule as exp_power.py); Chronos-2 is also reported at its nominal q99 rule.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline

spec = importlib.util.spec_from_file_location("exp_power", Path(__file__).with_name("exp_power.py"))
ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)
from bursts import detectors as det  # noqa: E402
from bursts.sanitize import sanitized_value  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forecasts", required=True)
    ap.add_argument("--calib-hours", type=int, default=720)
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--starts", type=int, default=6)
    ap.add_argument("--gaps", default="6,12,24")
    ap.add_argument("--amps2", default="2,3,5")
    ap.add_argument("--a1", type=float, default=8.0)
    ap.add_argument("--d1", type=int, default=6)
    ap.add_argument("--d2", type=int, default=1)
    ap.add_argument("--context", type=int, default=336)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--modes", default="none,median,winsor,budget")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_num_threads(4)
    rng = np.random.default_rng(a.seed)
    gaps = [int(x) for x in a.gaps.split(",")]
    amps2 = [float(x) for x in a.amps2.split(",")]
    MIN_VOL = ep.MIN_VOL

    z = np.load(a.forecasts)
    Q, Y, levels, cols, first = z["q"], z["y"], list(z["levels"]), list(z["columns"]), int(z["first"])
    i50, i99 = levels.index(0.5), levels.index(0.99)
    T, S = Y.shape
    cal = np.zeros(T, bool); cal[first:first + a.calib_hours] = True
    ev_idx = np.arange(first + a.calib_hours, T)

    # calibrated thresholds (same rule as exp_power)
    thr = []
    for s in range(S):
        y = Y[:, s]
        sc = ep.baseline_scores(y)
        sc["chronos2"] = det.chronos_score(y, Q[:, s, i50], Q[:, s, i99])
        th = {}
        n_allowed = int(np.floor(a.alpha * cal.sum()))
        for m in ("chronos2", "nb_seasonal", "robust_z", "seasonal_z"):
            v = sc[m][cal & (y >= MIN_VOL)]; v = v[np.isfinite(v)]
            th[m] = np.sort(v)[::-1][n_allowed] if len(v) > n_allowed else -np.inf
        th["cusum"] = ep.calibrate_cusum(sc["cusum_r"], a.alpha, cal)
        thr.append(th)

    def burst(A, D, mu):
        tau = np.arange(D)
        return rng.poisson(A * np.sqrt(mu + 1.0) * np.exp(-tau / max(D / 2, 0.5))).astype(float)

    jobs = []
    for s in range(S):
        y = Y[:, s]
        mu_seas = np.nanmean(det.seasonal_lags(y, 7), axis=1)
        lo, hi = ev_idx[0] + 24, ev_idx[-1] - max(gaps) - a.d2 - 2
        for t0 in rng.permutation(np.arange(lo, hi, 72))[:a.starts]:
            for gap in gaps:
                for A2 in amps2:
                    t2 = t0 + gap
                    e1 = burst(a.a1, a.d1, mu_seas[t0])
                    e2 = burst(A2, a.d2, mu_seas[t2])
                    for with_first in (True, False):
                        yy = y.copy()
                        if with_first:
                            yy[t0:t0 + a.d1] += e1
                        yy[t2:t2 + a.d2] += e2
                        jobs.append(dict(s=s, t0=int(t0), t2=int(t2), gap=gap, A2=A2, first=with_first, y=yy))

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    # forecasts for every hour from the first modified hour to the end of the second burst,
    # in two context modes: raw and sanitised (flagged hours -> forecast median)
    modes = a.modes.split(",")
    for mode in modes:
        for j in jobs:
            start = j["t0"] if j["first"] else j["t2"]
            j[f"{mode}_start"] = start
            j[f"{mode}_q"] = {}
            j[f"{mode}_ctx"] = j["y"].copy()
            j[f"{mode}_flags"] = []
        max_len = max(j["t2"] + a.d2 - (j[f"{mode}_start"]) for j in jobs)
        for k in range(max_len):
            batch = [j for j in jobs if j[f"{mode}_start"] + k < j["t2"] + a.d2]
            ctxs = []
            for j in batch:
                t = j[f"{mode}_start"] + k
                ctxs.append(j[f"{mode}_ctx"][max(0, t - a.context):t].copy())
            for b in range(0, len(ctxs), 256):
                preds = pipe.predict(ctxs[b:b + 256], prediction_length=1, batch_size=256)
                for j, p in zip(batch[b:b + 256], preds):
                    t = j[f"{mode}_start"] + k
                    qv = p[0, :, 0].numpy()
                    j[f"{mode}_q"][t] = (float(qv[i50]), float(qv[i99]))
                    recent = sum(j[f"{mode}_flags"][-23:])
                    j[f"{mode}_flags"].append(bool(j["y"][t] > qv[i99]))
                    j[f"{mode}_ctx"][t] = float(sanitized_value(mode, np.array(j["y"][t]), np.array(qv[i50]),
                                                                np.array(qv[i99]), np.array(recent)))
            print(f"{mode}: step {k + 1}/{max_len}", flush=True)

    rows = []
    for j in jobs:
        s, t2 = j["s"], j["t2"]
        y = j["y"]
        win = slice(t2, t2 + a.d2)
        yv = y[win]
        r = {"series": cols[s], "gap": j["gap"], "A2": j["A2"], "first": j["first"]}
        for mode in modes:
            q50 = np.array([j[f"{mode}_q"][t][0] for t in range(t2, t2 + a.d2)])
            q99 = np.array([j[f"{mode}_q"][t][1] for t in range(t2, t2 + a.d2)])
            sc = det.chronos_score(yv, q50, q99)
            r[f"chronos2_{mode}_calib"] = bool(((sc > thr[s]["chronos2"]) & (yv >= MIN_VOL)).any())
            r[f"chronos2_{mode}_nominal"] = bool(((yv > q99) & (yv >= MIN_VOL)).any())
        sc = ep.baseline_scores(y[: t2 + a.d2 + 1])
        for m in ("nb_seasonal", "robust_z", "seasonal_z"):
            r[m] = bool(((sc[m][win] > thr[s][m]) & (yv >= MIN_VOL)).any())
        _, st = det.cusum_alarms(sc["cusum_r"][:t2], ep.CUSUM_K, thr[s]["cusum"])
        al, _ = det.cusum_alarms(sc["cusum_r"][win], ep.CUSUM_K, thr[s]["cusum"], s0=st)
        r["cusum"] = bool((al & (yv >= MIN_VOL)).any())
        rows.append(r)
    pd.DataFrame(rows).to_csv(a.out + ".csv", index=False)
    json.dump(vars(a), open(a.out + "_config.json", "w"), indent=1)
    print("done", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
