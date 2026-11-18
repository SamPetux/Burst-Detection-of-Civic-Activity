"""Alarm rate (H1) and detection power at matched alarm rate (H2) with injected bursts.

Periods (exploratory data): calibration = first `--calib-hours` forecast hours, evaluation = rest.
Nominal mode: textbook thresholds. Calibrated mode: per-series threshold giving `--alpha` alarm
rate on the calibration period. Injected bursts: Poisson extra counts with amplitude
A * sqrt(seasonal mean + 1) and an exponentially decaying kernel of duration D hours.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline

from bursts import detectors as det
from bursts.sanitize import sanitized_value

MIN_VOL = 3
NOMINAL = {"chronos2": None, "nb_seasonal": 2.0, "robust_z": 3.5, "seasonal_z": 3.5, "stl": 3.5, "cusum": 5.0}
THRESHOLDED = ("chronos2", "nb_seasonal", "robust_z", "seasonal_z", "stl")
CUSUM_K = 0.5


def baseline_scores(y: np.ndarray, stl: bool = False) -> dict[str, np.ndarray]:
    extra = {"stl": det.stl_z(y)} if stl else {}
    return {**extra,
        "nb_seasonal": det.nb_seasonal(y),
        "robust_z": det.robust_z(y),
        "seasonal_z": det.seasonal_robust_z(y),
        "cusum_r": det.cusum_residuals(y),
    }


def calibrate_cusum(r: np.ndarray, alpha: float, valid: np.ndarray) -> float:
    lo, hi = 0.5, 60.0
    for _ in range(40):
        mid = (lo + hi) / 2
        a, _ = det.cusum_alarms(r, CUSUM_K, mid)
        rate = (a & valid).sum() / max(valid.sum(), 1)
        lo, hi = (mid, hi) if rate > alpha else (lo, mid)
    return hi


def series_alarms(Y: np.ndarray, Q: np.ndarray, levels: list, cal: np.ndarray, alpha: float, min_vol: int):
    """Scores, calibrated thresholds and nominal/calibrated alarm masks for every series."""
    i50, i99 = levels.index(0.5), levels.index(0.99)
    scores_all, thr, nom_all, calib_all = [], [], [], []
    for s in range(Y.shape[1]):
        y = Y[:, s]
        sc = baseline_scores(y, stl=True)
        sc["chronos2"] = det.chronos_score(y, Q[:, s, i50], Q[:, s, i99])
        th = {}
        for m in THRESHOLDED:
            v = sc[m][cal & (y >= min_vol)]
            v = v[np.isfinite(v)]
            # threshold such that alarm share over ALL calibration hours equals alpha
            n_allowed = int(np.floor(alpha * cal.sum()))
            th[m] = np.sort(v)[::-1][n_allowed] if len(v) > n_allowed else -np.inf
        th["cusum"] = calibrate_cusum(sc["cusum_r"], alpha, cal)
        nom = {
            "chronos2": (y > Q[:, s, i99]) & (y >= min_vol),
            "nb_seasonal": (sc["nb_seasonal"] > NOMINAL["nb_seasonal"]) & (y >= min_vol),
            "robust_z": (sc["robust_z"] > NOMINAL["robust_z"]) & (y >= min_vol),
            "seasonal_z": (sc["seasonal_z"] > NOMINAL["seasonal_z"]) & (y >= min_vol),
            "stl": (sc["stl"] > NOMINAL["stl"]) & (y >= min_vol),
            "cusum": det.cusum_alarms(sc["cusum_r"], CUSUM_K, NOMINAL["cusum"])[0] & (y >= min_vol),
        }
        calib = {m: (sc[m] > th[m]) & (y >= min_vol) for m in THRESHOLDED}
        calib["cusum"] = det.cusum_alarms(sc["cusum_r"], CUSUM_K, th["cusum"])[0] & (y >= min_vol)
        scores_all.append(sc); thr.append(th); nom_all.append(nom); calib_all.append(calib)
    return scores_all, thr, nom_all, calib_all


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forecasts", required=True)
    ap.add_argument("--calib-hours", type=int, default=720)
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--starts", type=int, default=18)
    ap.add_argument("--amps", default="1,2,3,5,8")
    ap.add_argument("--durs", default="1,3,6")
    ap.add_argument("--context", type=int, default=336)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--min-vol", type=int, default=3)
    ap.add_argument("--rates-only", action="store_true")
    ap.add_argument("--baselines-only", action="store_true", help="injections without Chronos re-forecasts (chronos columns dropped)")
    ap.add_argument("--sanitize", default="none", choices=["none", "median", "winsor", "budget"],
                    help="must match the rule used to produce --forecasts; applied to re-forecast contexts")
    ap.add_argument("--backend", default="chronos2", choices=["chronos2", "chronos1"])
    ap.add_argument("--model", default="amazon/chronos-2", help="model of --forecasts; used for re-forecasts")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    global MIN_VOL
    MIN_VOL = a.min_vol
    torch.set_num_threads(4)
    rng = np.random.default_rng(a.seed)
    amps = [float(x) for x in a.amps.split(",")]
    durs = [int(x) for x in a.durs.split(",")]

    z = np.load(a.forecasts, allow_pickle=False)
    Q, Y, levels, cols, first = z["q"], z["y"], list(z["levels"]), list(z["columns"]), int(z["first"])
    i50, i99 = levels.index(0.5), levels.index(0.99)
    T, S = Y.shape
    cal = np.zeros(T, bool); cal[first:first + a.calib_hours] = True
    ev = np.zeros(T, bool); ev[first + a.calib_hours:] = True

    # ---------- scores on the original series, thresholds ----------
    scores_all, thr, nom_all, calib_all = series_alarms(Y, Q, levels, cal, a.alpha, MIN_VOL)
    per_series = []
    for s in range(S):
        row = {"series": cols[s], "rate_per_hour": float(Y[ev, s].mean())}
        for m in nom_all[s]:
            row[f"nominal_{m}"] = float(nom_all[s][m][ev].mean())
            row[f"calib_{m}"] = float(calib_all[s][m][ev].mean())
        per_series.append(row)
    pd.DataFrame(per_series).to_csv(a.out + "_alarm_rates.csv", index=False)
    print("alarm rates written", flush=True)
    if a.rates_only:
        return 0

    # ---------- injections ----------
    ev_idx = np.where(ev)[0]
    if a.baselines_only:
        pass
    elif a.backend == "chronos1":
        from bursts.chronos1 import Chronos1Quantiles
        c1 = Chronos1Quantiles(a.model, levels)
    else:
        pipe = Chronos2Pipeline.from_pretrained(a.model, device_map="cpu")
    jobs = []  # (series, t0, A, D, extra counts)
    for s in range(S):
        y = Y[:, s]
        lo, hi = ev_idx[0] + 24, ev_idx[-1] - max(durs) - 1
        cand = rng.permutation(np.arange(lo, hi, 48))[:a.starts]
        mu_seas = np.nanmean(det.seasonal_lags(y, 7), axis=1)
        for t0 in cand:
            base = np.sqrt(mu_seas[t0] + 1.0)
            for A in amps:
                for D in durs:
                    tau = np.arange(D)
                    lam = A * base * np.exp(-tau / max(D / 2, 0.5))
                    jobs.append((s, int(t0), A, D, rng.poisson(lam).astype(float)))

    # Context source as seen by the rolling run: flagged hours already sanitised.
    ctx_src = Y.copy()
    if a.sanitize != "none":
        flags = np.zeros_like(Y, dtype=bool)
        for t in range(first, T):
            flags[t] = Y[t] > Q[t, :, i99]
            recent = flags[max(first, t - 23):t].sum(0)
            ctx_src[t] = sanitized_value(a.sanitize, Y[t], Q[t, :, i50], Q[t, :, i99], recent)

    # Chronos re-forecasts for hours t0+1..t0+D-1, level by level, so that injected hours enter
    # later contexts through the same sanitisation rule as in the rolling run.
    qre = {}
    inj_ctx = {}  # job -> sanitised values of injected hours seen so far
    B = 256
    for k in range(1, 1 if a.baselines_only else max(durs)):
        level = [j for j, job in enumerate(jobs) if job[3] > k]
        for j in level:
            s, t0, A, D, extra = jobs[j]
            yk = Y[t0 + k - 1, s] + extra[k - 1]
            q50k, q99k = (Q[t0, s, i50], Q[t0, s, i99]) if k == 1 else qre[(j, k - 1)]
            if a.sanitize == "none":
                v = yk
            else:
                prev = inj_ctx.get(j, [])
                recent = flags[max(first, t0 + k - 1 - 23):t0, s].sum() + sum(f for _, f in prev)
                v = float(sanitized_value(a.sanitize, np.array(yk), np.array(q50k), np.array(q99k), np.array(recent)))
            inj_ctx.setdefault(j, []).append((v, bool(yk > q99k)))
        for b in range(0, len(level), B):
            chunk = level[b:b + B]
            ctxs = []
            for j in chunk:
                s, t0, A, D, extra = jobs[j]
                t = t0 + k
                lo = max(0, t - a.context)
                yy = ctx_src[lo:t, s].copy()
                yy[t0 - lo:] = [v for v, _ in inj_ctx[j]]
                ctxs.append(yy)
            if a.backend == "chronos1":
                qs = c1.predict(np.stack(ctxs))
            else:
                qs = [p[0, :, 0].numpy() for p in pipe.predict(ctxs, prediction_length=1, batch_size=B)]
            for j, qv in zip(chunk, qs):
                qre[(j, k)] = (qv[i50], qv[i99])
        print(f"re-forecast level {k}: {len(level)} jobs", flush=True)

    rows = []
    for j, (s, t0, A, D, extra) in enumerate(jobs):
        y = Y[:, s].copy()
        y[t0:t0 + D] += extra
        win = slice(t0, t0 + D)
        res = {"series": cols[s], "t0": t0, "A": A, "D": D, "extra_total": float(extra.sum())}
        q50 = Q[:, s, i50].copy(); q99 = Q[:, s, i99].copy()
        for k in range(1, 1 if a.baselines_only else D):
            q50[t0 + k], q99[t0 + k] = qre[(j, k)]
        sc = baseline_scores(y[: t0 + D + 1])
        sc["stl"] = det.stl_z(y[: t0 + D + 1], idx=range(t0, t0 + D))
        sc["chronos2"] = det.chronos_score(y[: t0 + D + 1], q50[: t0 + D + 1], q99[: t0 + D + 1])
        yv = y[win]
        th = thr[s]
        flags = {
            "nominal_chronos2": (yv > q99[win]) & (yv >= MIN_VOL),
            "nominal_nb_seasonal": (sc["nb_seasonal"][win] > NOMINAL["nb_seasonal"]) & (yv >= MIN_VOL),
            "nominal_robust_z": (sc["robust_z"][win] > NOMINAL["robust_z"]) & (yv >= MIN_VOL),
            "nominal_seasonal_z": (sc["seasonal_z"][win] > NOMINAL["seasonal_z"]) & (yv >= MIN_VOL),
            "nominal_stl": (sc["stl"][win] > NOMINAL["stl"]) & (yv >= MIN_VOL),
        }
        for m in THRESHOLDED:
            flags[f"calib_{m}"] = (sc[m][win] > th[m]) & (yv >= MIN_VOL)
        r = sc["cusum_r"]
        for mode, h in (("nominal", NOMINAL["cusum"]), ("calib", th["cusum"])):
            _, s_state = det.cusum_alarms(r[:t0], CUSUM_K, h)
            al, _ = det.cusum_alarms(r[win], CUSUM_K, h, s0=s_state)
            flags[f"{mode}_cusum"] = al & (yv >= MIN_VOL)
        for name, f in flags.items():
            if a.baselines_only and "chronos2" in name:
                continue
            hit = np.flatnonzero(f)
            res[f"det_{name}"] = bool(len(hit))
            res[f"delay_{name}"] = float(hit[0]) if len(hit) else np.nan
        rows.append(res)
    inj = pd.DataFrame(rows)
    inj.to_csv(a.out + "_injections.csv", index=False)
    json.dump({"alpha": a.alpha, "sanitize": a.sanitize, "backend": a.backend, "model": a.model, "calib_hours": a.calib_hours, "n_series": S, "n_injections": len(jobs),
               "amps": amps, "durs": durs, "min_volume": MIN_VOL, "seed": a.seed},
              open(a.out + "_config.json", "w"), indent=1)
    print("done", len(jobs), "injections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
