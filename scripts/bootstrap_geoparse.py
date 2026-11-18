"""Bootstrap 95% intervals for geoparser metrics on a gold set (resampling messages)."""
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

CODES = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky", "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky"]
rng = np.random.default_rng(0)
rows = []
for path in sys.argv[1:]:
    d = pd.read_csv(path, dtype=str)
    g, p = d.label.to_numpy(), d.pred.to_numpy()

    def stats(idx):
        gg, pp = g[idx], p[idx]
        has, said = gg != "none", pp != "none"
        return (f1_score(gg, pp, labels=CODES, average="macro", zero_division=0),
                (pp[has] == gg[has]).mean() if has.any() else np.nan,
                (pp[said] == gg[said]).mean() if said.any() else np.nan)
    point = stats(np.arange(len(d)))
    boots = np.array([stats(rng.integers(0, len(d), len(d))) for _ in range(2000)])
    lo, hi = np.nanpercentile(boots, 2.5, axis=0), np.nanpercentile(boots, 97.5, axis=0)
    name = path.split("/")[-1].replace("_pred.csv", "")
    for k, m in enumerate(("macro_f1", "recall_located", "precision_assigned")):
        rows.append({"method": name, "metric": m, "value": round(point[k], 3), "ci_low": round(lo[k], 3), "ci_high": round(hi[k], 3)})
out = pd.DataFrame(rows)
print(out.pivot(index="method", columns="metric", values="value").to_string())
print(out.to_string(index=False))
out.to_csv("docs/results/geoparse_test_bootstrap.csv", index=False)
