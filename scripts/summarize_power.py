"""Tables and figures for alarm-rate calibration (H1) and injected-burst power (H2)."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

prefix, rates0, outdir, figdir = sys.argv[1:5]
style = sys.argv[5] if len(sys.argv) > 5 else None
if style:
    plt.style.use(style)
MS = ["chronos2", "nb_seasonal", "robust_z", "seasonal_z", "cusum"]
LABEL = {"chronos2": "Chronos-2 (zero-shot)", "nb_seasonal": "Seasonal neg. binomial",
         "robust_z": "Robust z-score", "seasonal_z": "Seasonal robust z", "cusum": "CUSUM"}
COLOR = {"chronos2": "#0072B2", "nb_seasonal": "#009E73", "robust_z": "#D55E00", "seasonal_z": "#E69F00", "cusum": "#CC79A7"}
MARK = {"chronos2": "o", "nb_seasonal": "s", "robust_z": "^", "seasonal_z": "D", "cusum": "v"}

r0 = pd.read_csv(rates0)
inj = pd.read_csv(prefix + "_injections.csv").merge(r0[["series", "rate_per_hour"]], on="series")
strata = pd.cut(inj.rate_per_hour, [0, 0.3, 1, 5, 200], labels=["0.05-0.3", "0.3-1", "1-5", ">5"])

lines = ["# Exploratory results: alarm-rate calibration and injected-burst power", "",
         "Data: 43 hourly series (communities, districts, city), calibration 2026-03-15..04-14, evaluation 2026-04-15..05-31. Alpha = 1 %.", ""]
for mode in ("nominal", "calib"):
    t = pd.DataFrame({m: [((r0[f"{mode}_{m}"] >= .005) & (r0[f"{mode}_{m}"] <= .02)).mean(),
                          r0[f"{mode}_{m}"].median() * 100, r0[f"{mode}_{m}"].max() * 100] for m in MS},
                     index=["share of series in [0.5%, 2%]", "median alarm rate, %", "max alarm rate, %"]).round(2)
    lines += [f"## Alarm rate without volume floor, {mode} thresholds", "", t.to_markdown(), ""]
for mode in ("calib", "nominal"):
    t = (inj.groupby("A")[[f"det_{mode}_{m}" for m in MS]].mean() * 100).round(1)
    t.columns = MS
    lines += [f"## Detection probability (%) by amplitude, {mode} thresholds", "", t.to_markdown(), ""]
s = inj[inj.A.isin([2, 3, 5])]
for by, name in ((strata[s.index], "intensity stratum"), (s.D, "duration, h")):
    t = (s.groupby(by, observed=True)[[f"det_calib_{m}" for m in MS]].mean() * 100).round(1)
    t.columns = MS
    lines += [f"## Detection probability (%) by {name}, A in {{2,3,5}}, calibrated", "", t.to_markdown(), ""]
d6 = inj[inj.D == 6][[f"delay_calib_{m}" for m in MS]].mean().round(2)
d6.index = MS
lines += ["## Mean delay (h) among detected bursts, D = 6 h, calibrated", "", d6.to_frame("delay_h").to_markdown(), ""]
open(f"{outdir}/power_explore.md", "w").write("\n".join(lines))

fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.6))
x = r0.rate_per_hour
for m in MS:
    ax[0].scatter(x, np.clip(100 * r0[f"nominal_{m}"], 0.05, None), s=10, color=COLOR[m], marker=MARK[m], label=LABEL[m], alpha=.85, linewidths=0)
ax[0].axhspan(0.5, 2.0, color="0.88", zorder=0); ax[0].axhline(1, color="0.3", lw=.7, ls="--")
ax[0].set(xscale="log", yscale="log", xlabel="Series intensity, messages per hour", ylabel="Alarm rate, % of hours", ylim=(0.04, 20), title="(a) Nominal 1% level, no tuning")
ax[0].legend(fontsize=5.5, frameon=False, loc="upper left")
pd_a = inj.groupby("A")[[f"det_calib_{m}" for m in MS]].mean() * 100
for m in MS:
    ax[1].plot(pd_a.index, pd_a[f"det_calib_{m}"], color=COLOR[m], marker=MARK[m], ms=3, lw=1, label=LABEL[m])
ax[1].set(xlabel="Burst amplitude, Poisson standard deviations", ylabel="Detection probability, %", ylim=(0, 100), title="(b) Power at matched 1% alarm rate")
fig.tight_layout()
fig.savefig(f"{figdir}/fig_calibration_power.pdf"); fig.savefig(f"{figdir}/fig_calibration_power.png", dpi=300)
print("ok")
