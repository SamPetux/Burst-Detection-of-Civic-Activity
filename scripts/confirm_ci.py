"""Series-cluster bootstrap intervals for the confirmatory H1-H3 estimates."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

MS = ["chronos2", "nb_seasonal", "robust_z", "seasonal_z", "cusum"]
B = 4000
rng = np.random.default_rng(11)


def ci(f, groups: list[pd.DataFrame]) -> list[float]:
    vals = [f(pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])) for _ in range(B)]
    return list(np.round(np.percentile(vals, [2.5, 97.5]), 3))


def main() -> None:
    out = {}
    for tag, path in [("winsor", "results/confirm_h1_alarm_rates.csv"), ("none", "results/confirm_h1_none_alarm_rates.csv")]:
        r = pd.read_csv(path); r = r[r.rate_per_hour >= 0.05]
        g = [x for _, x in r.groupby("series")]
        out[f"H1_{tag}"] = {m: {"in_band": round(r[f"nominal_{m}"].between(.005, .02).mean(), 3),
                                "ci": ci(lambda d, m=m: d[f"nominal_{m}"].between(.005, .02).mean(), g)}
                            for m in (MS if tag == "winsor" else ["chronos2"])}
    inj = pd.read_csv("results/confirm_h2_injections.csv")
    g = [x for _, x in inj.groupby("series")]
    out["H2"] = {m: {"pd": round(inj[f"det_calib_{m}"].mean(), 3), "ci": ci(lambda d, m=m: d[f"det_calib_{m}"].mean(), g)}
                 for m in MS}
    out["H2"]["diff_chronos_minus_nb"] = {
        "est": round(inj.det_calib_chronos2.mean() - inj.det_calib_nb_seasonal.mean(), 4),
        "ci": ci(lambda d: d.det_calib_chronos2.mean() - d.det_calib_nb_seasonal.mean(), g)}
    c = pd.read_csv("results/confirm_h3.csv")
    g = [x for _, x in c.groupby("series")]
    out["H3"] = {}
    for first in (False, True):
        for gap in (6, 12, 24):
            for col in ("chronos2_none_calib", "chronos2_winsor_calib", "chronos2_median_calib", "nb_seasonal"):
                f = lambda d, col=col, first=first, gap=gap: d[(d["first"] == first) & (d.gap == gap)][col].mean()
                out["H3"][f"{col}|first={first}|gap={gap}"] = {"pd": round(f(c), 3), "ci": ci(f, g)}
    json.dump(out, open("results/confirm/ci.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "H3"}, indent=1))


if __name__ == "__main__":
    main()
