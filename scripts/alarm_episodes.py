"""Alarm episodes on district and city series, matched to the chronicle (for precision labelling)."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("eval_events", Path(__file__).with_name("eval_events.py"))
ee = importlib.util.module_from_spec(spec); spec.loader.exec_module(ee)


def episodes(mask: np.ndarray, gap: int = 2) -> list[tuple[int, int]]:
    idx = np.where(mask)[0]
    out = []
    for i in idx:
        if out and i - out[-1][1] <= gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [tuple(x) for x in out]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forecasts", default="results/chronos2_confirm_winsor.npz")
    ap.add_argument("--detector", default="chronos2")
    ap.add_argument("--out", default="results/confirm/episodes_chronos2_winsor.csv")
    a = ap.parse_args()
    z = np.load(a.forecasts)
    Y, Q, levels, first = z["y"], z["q"], list(z["levels"]), int(z["first"])
    cols = list(z["columns"]); ts = pd.DatetimeIndex(pd.to_datetime(z["timestamps"])).tz_convert(ee.TZ)
    cal = np.zeros(len(Y), bool); cal[first:first + 720] = True
    _, _, _, calib = ee.ep.series_alarms(Y, Q, levels, cal, 0.01, 3)
    ev = ee.load_events("docs/chronicle/events_review_author.xlsx")
    rows = []
    for s, c in enumerate(cols):
        if not (c.startswith("dst:") or c == "city") or c == "dst:unassigned":
            continue
        m = calib[s][a.detector].copy(); m[:first + 720] = False
        for i0, i1 in episodes(m):
            t0, t1 = ts[i0], ts[i1] + pd.Timedelta(hours=1)
            e = ev[(ev.series == c) & (ev.t_lo <= t1) & (ev.t_hi >= t0)]
            rows.append({"series": c, "start": t0, "end": t1, "hours": i1 - i0 + 1,
                         "peak": float(Y[i0:i1 + 1, s].max()), "events": ",".join(e.id)})
    d = pd.DataFrame(rows)
    d.to_csv(a.out, index=False)
    print(len(d), "episodes; matched", (d.events != "").sum(), d.groupby("series").size().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
