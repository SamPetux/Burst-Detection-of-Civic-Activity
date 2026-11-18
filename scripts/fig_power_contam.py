"""Figure 2: (a) detection probability by intensity stratum at matched alarm rate; (b) second-burst
detection after a strong first burst (context contamination)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

LAB = ["0.05–0.3", "0.3–1", "1–5", ">5"]
M = [("chronos2", "Chronos-2", "#0072B2", "o"), ("nb_seasonal", "Seasonal NB", "#009E73", "s"),
     ("seasonal_z", "Seasonal z", "#E69F00", "D"), ("stl", "STL", "#56B4E9", "P"),
     ("robust_z", "Robust z", "#D55E00", "^"), ("cusum", "CUSUM", "#CC79A7", "v")]

inj = pd.read_csv("results/confirm_h2_injections.csv")
stl = pd.read_csv("results/extra_stl_h2_injections.csv")[["series", "t0", "A", "D", "det_calib_stl"]]
inj = inj.merge(stl, on=["series", "t0", "A", "D"])
r = pd.read_csv("results/confirm_h1_alarm_rates.csv")[["series", "rate_per_hour"]]
inj = inj.merge(r, on="series")
inj["st"] = pd.cut(inj.rate_per_hour, [0, .3, 1, 5, np.inf], labels=LAB)

import sys
STACK = "--stack" in sys.argv
fig, (a1, a2) = plt.subplots(*((2, 1) if STACK else (1, 2)), figsize=(3.5, 5.6) if STACK else (7.2, 2.9), constrained_layout=True)
x = np.arange(4)
for m, lab, col, mk in M:
    v = inj.groupby("st", observed=True)[f"det_calib_{m}"].mean()
    a1.plot(x, v.values, marker=mk, color=col, label=lab, lw=1.4 if m == "chronos2" else 1, ms=4)
a1.set(xticks=x, xticklabels=LAB, xlabel="series intensity, messages/h", ylabel="detection probability",
       ylim=(0, 0.7), title="(a) injected bursts, alarm rate 1 %")
a1.grid(alpha=0.3, lw=0.4); a1.legend(fontsize=6.5, ncol=2, loc="lower left")

c = pd.read_csv("results/confirm_h3.csv")
gaps = [6, 12, 24]
S = [("chronos2_none_calib", "Chronos-2, no sanitisation", "#0072B2"), ("chronos2_winsor_calib", "Chronos-2, winsor", "#56B4E9"),
     ("chronos2_median_calib", "Chronos-2, median", "#999999"), ("nb_seasonal", "Seasonal NB", "#009E73")]
w = 0.2
for i, (col, lab, colr) in enumerate(S):
    with_ = [c[(c["first"]) & (c.gap == g)][col].mean() for g in gaps]
    a2.bar(np.arange(3) + (i - 1.5) * w, with_, w, color=colr, label=lab)
base = [c[(~c["first"]) & (c.gap == g)]["chronos2_none_calib"].mean() for g in gaps]
a2.plot(np.arange(3), base, "k_", ms=22, mew=1.5, label="Chronos-2, no first burst")
a2.set(xticks=range(3), xticklabels=[f"{g} h" for g in gaps], xlabel="gap after first burst (A=8, D=6 h)",
       ylabel="detection of second burst", ylim=(0, 0.9), title="(b) context contamination")
a2.grid(alpha=0.3, axis="y", lw=0.4); a2.legend(fontsize=6, loc="upper center", ncol=2, frameon=False)
for ext in ("pdf", "png"):
    fig.savefig(f"paper/figures/power_contamination{'_col' if STACK else ''}.{ext}", dpi=300)
print("ok")
