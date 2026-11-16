"""Exploratory probe: alarm rate of a properly specified count model at the nominal 1% level.
Seasonal negative-binomial predictive: mean = average of the same hour over the previous 7 days,
dispersion = method of moments on the previous 336 hours of residuals."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson

series_csv, rates_csv, out_csv = sys.argv[1:4]
df = pd.read_csv(series_csv, parse_dates=["timestamp"])
df["key"] = df.district + "|" + df.topic_id.astype(str)
wide = df.pivot(index="timestamp", columns="key", values="n_messages").sort_index().astype(float)
keys = pd.read_csv(rates_csv).key.tolist()
start = pd.Timestamp("2026-04-14T00:00:00+03:00")
m = wide.index >= start

rows = []
for k in keys:
    y = wide[k]
    mu = pd.concat([y.shift(24 * j) for j in range(1, 8)], axis=1).mean(axis=1).clip(lower=0.05)
    resid_var = (y - mu).shift(1).rolling(336, min_periods=168).var()
    level = mu.shift(1).rolling(336, min_periods=168).mean()
    phi = ((resid_var - level) / level.pow(2)).clip(lower=0.0).fillna(0.0)
    q = np.where(phi > 1e-6,
                 nbinom.ppf(0.99, 1.0 / phi.clip(lower=1e-6), (1.0 / phi.clip(lower=1e-6)) / ((1.0 / phi.clip(lower=1e-6)) + mu)),
                 poisson.ppf(0.99, mu))
    flags = pd.Series(y.to_numpy() > q, index=y.index)[m]
    rows.append({"key": k, "nb_seasonal_q99": float(flags.mean())})
out = pd.read_csv(rates_csv).merge(pd.DataFrame(rows), on="key")
out.to_csv(out_csv, index=False)
from scipy.stats import spearmanr
for col in ["chronos2_q99", "nb_seasonal_q99", "robust_z_168h_3.5", "seasonal_z_7d_3.5", "cusum_k0.5_h5"]:
    rho, p = spearmanr(out.mean_per_hour, out[col])
    dev = np.mean(np.abs(np.log10((out[col] + 1e-3) / 0.01)))
    print(f"{col:20s} median={100*out[col].median():5.2f}%  p10-p90={100*out[col].quantile(.1):.2f}-{100*out[col].quantile(.9):.2f}%  max={100*out[col].max():5.1f}%  mean|log10(rate/1%)|={dev:.2f}  rho={rho:+.2f} (p={p:.1e})")
bins = pd.cut(out.mean_per_hour, [0, 0.3, 1, 5, 100], labels=["0.1-0.3", "0.3-1", "1-5", ">5"])
print((out.groupby(bins, observed=True)[["chronos2_q99", "nb_seasonal_q99", "robust_z_168h_3.5", "seasonal_z_7d_3.5", "cusum_k0.5_h5"]].mean() * 100).round(2).to_string())
