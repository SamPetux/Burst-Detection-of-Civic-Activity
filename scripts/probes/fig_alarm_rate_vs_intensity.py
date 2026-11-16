"""Draft of the key figure: alarm rate at nominal 1% versus series intensity (exploratory window)."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

src, out = sys.argv[1], sys.argv[2]
style = sys.argv[3] if len(sys.argv) > 3 else None
if style:
    plt.style.use(style)
d = pd.read_csv(src)
methods = [
    ("chronos2_q99", "Chronos-2, zero-shot $q_{0.99}$", "#0072B2", "o"),
    ("nb_seasonal_q99", "Seasonal negative binomial $q_{0.99}$", "#009E73", "s"),
    ("robust_z_168h_3.5", "Robust z-score, 3.5", "#D55E00", "^"),
    ("cusum_k0.5_h5", "CUSUM, k=0.5, h=5", "#CC79A7", "v"),
]
fig, ax = plt.subplots(figsize=(3.5, 2.6))
x = d.mean_per_hour.to_numpy()
for col, label, color, marker in methods:
    y = 100 * d[col].to_numpy()
    ax.scatter(x, np.clip(y, 0.05, None), s=12, color=color, marker=marker, label=label, alpha=0.85, linewidths=0)
ax.axhline(1.0, color="0.3", lw=0.8, ls="--")
ax.axhspan(0.5, 2.0, color="0.85", zorder=0)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Mean messages per hour (series intensity)")
ax.set_ylabel("Alarm rate, % of hours")
ax.set_ylim(0.04, 40)
ax.text(0.105, 1.08, "nominal 1%", fontsize=6, color="0.3")
ax.legend(fontsize=5.5, frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=300)
print("saved", out)
