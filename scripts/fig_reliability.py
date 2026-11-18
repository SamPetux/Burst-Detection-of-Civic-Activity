"""Exceedance reliability of upper forecast quantiles by intensity stratum (evaluation window)."""
from __future__ import annotations

import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BINS, LABELS = [0.05, 0.3, 1, 5, np.inf], ["0.05–0.3", "0.3–1", "1–5", ">5"]
COLORS = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]


def exceedance(path: str, calib_hours: int = 720) -> pd.DataFrame:
    z = np.load(path)
    Y, Q, lv, first = z["y"], z["q"], np.array(z["levels"]), int(z["first"])
    ev = slice(first + calib_hours, None)
    rate = Y[ev].mean(0)
    keep = rate >= 0.05
    up = lv >= 0.5
    exc = (Y[ev][:, :, None] > Q[ev][:, :, up]).mean(0)[keep]  # (series, levels)
    d = pd.DataFrame(exc, columns=1 - lv[up])
    d["stratum"] = pd.cut(rate[keep], BINS, labels=LABELS)
    return d


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", nargs="+", required=True, help="title=path.npz")
    ap.add_argument("--out", default="paper/figures/reliability")
    ap.add_argument("--stack", action="store_true", help="panels in one column (single-column layout)")
    a = ap.parse_args()
    n = len(a.panel)
    shape, size = ((n, 1), (3.5, 2.6 * n)) if a.stack else ((1, n), (3.5 * n, 3.1))
    fig, axes = plt.subplots(*shape, figsize=size, sharey=True, constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, spec in zip(axes, a.panel):
        title, path = spec.split("=")
        d = exceedance(path)
        nom = np.array([c for c in d.columns if c != "stratum"], float)
        for lab, col in zip(LABELS, COLORS):
            g = d[d.stratum == lab].drop(columns="stratum").to_numpy()
            med, lo, hi = np.median(g, 0), np.percentile(g, 25, 0), np.percentile(g, 75, 0)
            ax.plot(nom, med, "o-", ms=3, color=col, label=f"{lab} msg/h (n={len(g)})")
            ax.fill_between(nom, lo, hi, color=col, alpha=0.15, lw=0)
        ax.plot([0.005, 0.6], [0.005, 0.6], "k--", lw=0.8, label="ideal")
        ax.axhspan(0.005, 0.02, xmin=0, xmax=1, color="0.85", zorder=0)
        ax.set(xscale="log", yscale="log", xlim=(0.007, 0.6), ylim=(0.002, 0.7), title=title,
               xlabel="nominal exceedance 1 − τ")
        ax.grid(alpha=0.3, which="both", lw=0.4)
    for ax in axes if a.stack else axes[:1]:
        ax.set_ylabel("observed P(y > q_τ)")
    axes[0].legend(fontsize=7, loc="upper left")
    for ext in ("pdf", "png"):
        fig.savefig(f"{a.out}.{ext}", dpi=200)
    print("saved", a.out)


if __name__ == "__main__":
    main()
