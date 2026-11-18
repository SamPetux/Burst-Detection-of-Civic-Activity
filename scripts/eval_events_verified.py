"""Content-verified event detection: an alarm counts only if the messages of that hour are about the event.

Relevance labels per alarm hour: data/raw/labels/event_alarm_relevance_*.csv (blind to detector).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binomtest

KEYS = ["chronos2_winsor", "chronos2_none", "nb_seasonal", "robust_z", "seasonal_z", "stl", "cusum"]
L = "data/raw/labels/"


def main() -> None:
    d = pd.read_csv("results/confirm/events_calib_per_event.csv", parse_dates=["t_pub", "t_start"])
    z = np.load("results/chronos2_confirm_winsor.npz")
    ts = pd.DatetimeIndex(pd.to_datetime(z["timestamps"])).tz_convert("Europe/Moscow")
    rel = pd.concat([pd.read_csv(L + "event_alarm_relevance_claude.csv"), pd.read_csv(L + "event_alarm_relevance_stl_extra.csv")])
    rel[["pair", "h"]] = rel.hid.str.extract(r"P(\d+)-H(\d+)").astype(int)
    h = pd.read_csv(L + "event_alarm_hours.csv")[["pair", "h"] + KEYS[:-2] + ["cusum"]]
    s = pd.read_csv(L + "stl_event_hours.csv")[["pair", "h"]].assign(stl=True)
    h = h.merge(s, on=["pair", "h"], how="outer").fillna(False)
    h = h.merge(rel[["pair", "h", "relevance"]], on=["pair", "h"], how="left")
    h["ts"] = ts[h.h.to_numpy()]
    ok = h[h.relevance == "related"]
    rng = np.random.default_rng(0)
    rows, first = [], {}
    for k in KEYS:
        f = ok[ok[k].astype(bool)].groupby("pair").ts.min(); first[k] = f
        hit = d.index.isin(f.index)
        lead = (d.loc[f.index, "t_pub"] - f).dt.total_seconds() / 3600
        boot = [hit[rng.integers(0, len(hit), len(hit))].mean() for _ in range(4000)]
        rows.append({"detector": k, "verified_hits": int(hit.sum()), "recall": hit.mean(),
                     "ci": tuple(np.percentile(boot, [2.5, 97.5]).round(3)),
                     "before_publication": int((lead > 0).sum()), "median_lead_h": lead.median()})
    res = pd.DataFrame(rows)
    res.to_csv("results/confirm/events_verified_summary.csv", index=False)
    print(res.round(3).to_string())
    for b in KEYS[2:]:
        j = first["chronos2_winsor"].index.intersection(first[b].index)
        dt = (first[b][j] - first["chronos2_winsor"][j]).dt.total_seconds() / 3600
        print(f"vs {b}: both {len(j)}, chronos earlier {(dt > 0).sum()}, same {(dt == 0).sum()}, later {(dt < 0).sum()}")
    f = first["chronos2_winsor"]
    print(d.loc[f.index, ["id", "series", "type"]].assign(alarm=f.dt.tz_convert("Europe/Moscow").values,
          lead_h=((d.loc[f.index, "t_pub"] - f).dt.total_seconds() / 3600).round(1).values).to_string())


if __name__ == "__main__":
    main()
