"""Rolling one-step-ahead zero-shot Chronos-2 quantile forecasts for every series of a matrix.

Writes an .npz with quantile levels and an array (n_hours, n_series, n_quantiles); rows before
`--from` stay NaN. Strictly causal: the forecast for hour t sees hours < t only.
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline

from bursts.chronos1 import Chronos1Quantiles
from bursts.data import hourly_matrix, load_messages
from bursts.sanitize import sanitized_value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--start", required=True, help="matrix start (context begins here)")
    ap.add_argument("--end", required=True, help="matrix end, exclusive")
    ap.add_argument("--from", dest="from_", required=True, help="first forecast hour")
    ap.add_argument("--min-rate", type=float, default=0.05)
    ap.add_argument("--context", type=int, default=336)
    ap.add_argument("--model", default="amazon/chronos-2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--geo", help="LLM district override CSV (kind, msg_id, district)")
    ap.add_argument("--sanitize", default="none", choices=["none", "median", "winsor", "budget"],
                    help="what a flagged hour (y > q99) contributes to later contexts, see bursts/sanitize.py")
    ap.add_argument("--backend", default="chronos2", choices=["chronos2", "chronos1"],
                    help="chronos1: exact quantiles from a Chronos-1 (T5) model, see bursts/chronos1.py")
    a = ap.parse_args()
    torch.set_num_threads(4)

    wide = hourly_matrix(load_messages(a.corpus, a.geo), a.start, a.end)
    first = wide.index.get_loc(pd.Timestamp(a.from_, tz="Europe/Moscow"))
    rate = wide.iloc[first:].mean()
    wide = wide.loc[:, rate >= a.min_rate]
    y = wide.to_numpy()

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2" if a.backend == "chronos1" else a.model, device_map="cpu")
    levels = list(pipe.quantiles)
    if a.backend == "chronos1":
        c1 = Chronos1Quantiles(a.model, levels)
        del pipe
    q = np.full((len(wide), y.shape[1], len(levels)), np.nan, dtype=np.float32)
    t0 = time.time()
    ctx_src = y.copy()  # context source; differs from y only when --sanitize
    flags = np.zeros_like(y, dtype=bool)
    i50, i99 = levels.index(0.5), levels.index(0.99)
    ckpt = a.out + ".ckpt.npz"
    start = first
    if os.path.exists(ckpt):  # resume after an interrupted run
        c = np.load(ckpt)
        q, ctx_src, flags, start = c["q"], c["ctx_src"], c["flags"], int(c["next_t"])
        print(f"resumed at {start - first}", flush=True)
    for t in range(start, len(wide)):
        ctx = ctx_src[max(0, t - a.context):t].T
        if a.backend == "chronos1":
            q[t] = c1.predict(ctx)
        else:
            preds = pipe.predict([c for c in ctx], prediction_length=1, batch_size=256)
            q[t] = np.stack([p[0, :, 0].numpy() for p in preds])
        if a.sanitize != "none":
            flags[t] = y[t] > q[t, :, i99]
            recent = flags[max(first, t - 23):t].sum(0)
            ctx_src[t] = sanitized_value(a.sanitize, y[t], q[t, :, i50], q[t, :, i99], recent)
        if (t - first) % 200 == 0:
            print(f"{t - first}/{len(wide) - first} hours, {time.time() - t0:.0f}s", flush=True)
            np.savez(ckpt + ".tmp.npz", q=q, ctx_src=ctx_src, flags=flags, next_t=t + 1)
            os.replace(ckpt + ".tmp.npz", ckpt)
    np.savez_compressed(a.out, q=q, y=y, levels=np.array(levels), columns=np.array(wide.columns, dtype=str),
                        timestamps=np.array(wide.index.astype(str), dtype=str), first=first)
    if os.path.exists(ckpt):
        os.remove(ckpt)
    print("saved", a.out, q.shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
