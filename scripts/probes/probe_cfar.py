"""Exploratory probe: does a fixed nominal alarm level give a constant alarm rate across series of
very different intensity (CFAR-like behaviour)? Compares zero-shot Chronos-2 quantile exceedance with
classical detectors at textbook thresholds. Alarm rate here includes real events, so it is an upper
bound on the false-alarm rate; what matters is how it varies with series intensity."""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline


def robust_z(y: pd.Series, w: int) -> pd.Series:
    med = y.shift(1).rolling(w, min_periods=w // 2).median()
    mad = (y.shift(1) - med).abs().rolling(w, min_periods=w // 2).median()
    return (y - med) / (1.4826 * mad + 1.0)


def seasonal_robust_z(y: pd.Series, days: int) -> pd.Series:
    # same hour of day over the previous `days` days
    lags = pd.concat([y.shift(24 * k) for k in range(1, days + 1)], axis=1)
    med = lags.median(axis=1)
    mad = lags.sub(med, axis=0).abs().median(axis=1)
    return (y - med) / (1.4826 * mad + 1.0)


def cusum(y: pd.Series, w: int, k: float, h: float) -> pd.Series:
    mu = y.shift(1).rolling(w, min_periods=w // 2).mean()
    sd = y.shift(1).rolling(w, min_periods=w // 2).std().clip(lower=1.0)
    r = ((y - mu) / sd).fillna(0).to_numpy()
    s, out = 0.0, np.zeros(len(r), bool)
    for i, v in enumerate(r):
        s = max(0.0, s + v - k)
        if s > h:
            out[i], s = True, 0.0
    return pd.Series(out, index=y.index)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", default="2026-04-14T00:00:00+03:00")
    ap.add_argument("--context", type=int, default=336)
    ap.add_argument("--stride", type=int, default=2)
    args = ap.parse_args()
    torch.set_num_threads(4)

    df = pd.read_csv(args.series, parse_dates=["timestamp"])
    df["key"] = df.district + "|" + df.topic_id.astype(str)
    wide = df.pivot(index="timestamp", columns="key", values="n_messages").sort_index().astype(float)
    start = pd.Timestamp(args.start)
    eval_mask = wide.index >= start
    mean_rate = wide[eval_mask].mean()
    keys = [k for k in wide.columns if mean_rate[k] >= 0.1]

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    i99 = pipe.quantiles.index(0.99)
    idx = np.where(eval_mask)[0][::args.stride]
    q99 = {k: np.full(len(wide), np.nan) for k in keys}
    for t in idx:
        lo = max(0, t - args.context)
        preds = pipe.predict([wide[k].to_numpy()[lo:t] for k in keys], prediction_length=1, batch_size=64)
        for k, p in zip(keys, preds):
            q99[k][t] = float(p[0, i99, 0])

    rows = []
    for k in keys:
        y = wide[k]
        m = pd.Series(eval_mask, index=wide.index)
        tsfm = pd.Series(y.to_numpy() > q99[k], index=y.index)[~np.isnan(q99[k])]
        dets = {
            "chronos2_q99": tsfm,
            "robust_z_168h_3.5": (robust_z(y, 168) > 3.5)[m],
            "seasonal_z_7d_3.5": (seasonal_robust_z(y, 7) > 3.5)[m],
            "cusum_k0.5_h5": cusum(y, 168, 0.5, 5.0)[m],
        }
        r = {"key": k, "mean_per_hour": mean_rate[k], "zero_share": float((y[m] == 0).mean())}
        for name, flags in dets.items():
            r[name] = float(flags.mean())
        rows.append(r)
    out = pd.DataFrame(rows).sort_values("mean_per_hour")
    out.to_csv(args.out, index=False)
    print(out.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
