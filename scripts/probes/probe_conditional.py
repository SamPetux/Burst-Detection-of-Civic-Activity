"""Exploratory probe: unconditional vs conditional zero-shot Chronos-2 forecasts for district series.

U (unconditional): district history only.
C (conditional):   district history + "rest of city" as a covariate, including its value at the
                   forecast hour (all districts are observed simultaneously, so it is known at test time).

Output: per (origin, district) quantiles for both modes. Exploratory only: this window was already
inspected, so nothing computed here is a confirmatory result.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
import torch
from chronos import Chronos2Pipeline

DISTRICTS = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky",
             "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky"]
QUANTILES = [0.5, 0.9, 0.95, 0.99]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", default="2026-04-14T00:00:00+03:00")
    ap.add_argument("--context", type=int, default=336)
    ap.add_argument("--stride", type=int, default=1)
    args = ap.parse_args()

    torch.set_num_threads(4)
    df = pd.read_csv(args.series, parse_dates=["timestamp"])
    df = df[df.topic_id == "all"]
    wide = df.pivot(index="timestamp", columns="district", values="n_messages").sort_index()
    city = wide["city"].to_numpy(float)
    ts = wide.index

    pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
    qidx = {q: i for i, q in enumerate(pipe.quantiles)}
    for q in QUANTILES:
        assert q in qidx, q

    origins = [i for i, t in enumerate(ts) if t >= pd.Timestamp(args.start)][::args.stride]
    rows = []
    for t in origins:
        lo = max(0, t - args.context)
        uncond, cond = [], []
        for d in DISTRICTS:
            y = wide[d].to_numpy(float)
            rest = city - y
            uncond.append(y[lo:t])
            cond.append({
                "target": y[lo:t],
                "past_covariates": {"rest": rest[lo:t]},
                "future_covariates": {"rest": rest[t:t + 1]},
            })
        pu = pipe.predict(uncond, prediction_length=1)
        pc = pipe.predict(cond, prediction_length=1)
        for k, d in enumerate(DISTRICTS):
            r = {"timestamp": ts[t], "district": d, "y": wide[d].iloc[t], "rest": city[t] - wide[d].iloc[t]}
            for tag, p in (("u", pu[k]), ("c", pc[k])):
                qs = p[0, :, 0].numpy()  # (n_quantiles,) for the single target variate, step 0
                for q in QUANTILES:
                    r[f"{tag}_q{int(q * 100)}"] = float(qs[qidx[q]])
            rows.append(r)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print("origins", len(origins), "rows", len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
