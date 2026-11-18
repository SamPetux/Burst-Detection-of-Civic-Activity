"""Detectors against the independent event chronicle (descriptive, docs/06 §4).

Event reference: precise start time when the chronicle has one, otherwise the media publication.
Window: from the start (or 00:00 of the start date) to max(start, publication) + 12 h, capped at 48 h.
District events are scored on their district series, city and region events on the city series.
Chance level: the same windows shifted to random positions of the evaluation period.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("exp_power", Path(__file__).with_name("exp_power.py"))
ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)

MS = ["chronos2", "nb_seasonal", "robust_z", "seasonal_z", "stl", "cusum"]
TZ = "Europe/Moscow"


def load_events(path: str) -> pd.DataFrame:
    d = pd.read_excel(path, sheet_name="events")
    d["scope"] = d.scope_author.fillna(d.scope_claude)
    d["dist"] = d.district_author.fillna(d.district_claude).astype(str).str.replace("?", "", regex=False)
    d = d[d.scope.isin(["district", "city", "region"])].copy()
    day = pd.to_datetime(d.start_date)

    def hhmm(v):
        m = re.match(r"(\d{1,2}):(\d{2})(:\d{2})?(\s|$)", str(v).strip())
        return pd.Timedelta(hours=int(m[1]), minutes=int(m[2])) if m else pd.NaT

    d["t_start"] = (day + d.start_time_msk.map(hhmm)).dt.tz_localize(TZ)
    url_day = pd.to_datetime(d.source_url.str.extract(r"/(20\d\d/\d\d/\d\d)/")[0], format="%Y/%m/%d")
    pub_day = url_day.fillna(day)
    d["t_pub"] = (pub_day + d.publication_time.map(hhmm)).dt.tz_localize(TZ)
    d["precise"] = d.t_start.notna()
    lo = d.t_start.fillna(day.dt.tz_localize(TZ))
    hi = pd.concat([lo, d.t_pub.fillna(lo)], axis=1).max(axis=1) + pd.Timedelta(hours=12)
    d["t_lo"], d["t_hi"] = lo, hi.clip(upper=lo + pd.Timedelta(hours=48))
    rows = []
    for _, r in d.iterrows():
        targets = [f"dst:{x.strip()}" for x in r.dist.split(",")] if r.scope == "district" else ["city"]
        rows += [dict(r, series=t) for t in targets]
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="docs/chronicle/events_review_author.xlsx")
    ap.add_argument("--forecasts", nargs="+", default=["winsor=results/chronos2_confirm_winsor.npz",
                                                         "none=results/chronos2_confirm.npz"])
    ap.add_argument("--mode", default="calib", choices=["calib", "nominal"])
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out", default="results/confirm/events")
    a = ap.parse_args()
    rng = np.random.default_rng(3)
    ev = load_events(a.events)

    alarms, ts, cols = {}, None, None
    for spec_ in a.forecasts:
        name, path = spec_.split("=")
        z = np.load(path)
        Y, Q, levels, first = z["y"], z["q"], list(z["levels"]), int(z["first"])
        cols = list(z["columns"]); ts = pd.DatetimeIndex(pd.to_datetime(z["timestamps"])).tz_convert(TZ)
        cal = np.zeros(len(Y), bool); cal[first:first + 720] = True
        _, _, nom, calib = ep.series_alarms(Y, Q, levels, cal, 0.01, 3)
        src = calib if a.mode == "calib" else nom
        ms = MS if name == "winsor" else ["chronos2"]
        for m in ms:
            key = f"chronos2_{name}" if m == "chronos2" else m
            alarms[key] = np.stack([src[s][m] for s in range(len(cols))], 1)
        eval_start = first + 720
    T = len(ts)
    ev = ev[(ev.t_lo >= ts[eval_start]) & (ev.t_hi <= ts[-1]) & ev.series.isin(cols)].reset_index(drop=True)
    idx = lambda t: int(ts.searchsorted(t))
    ev["i_lo"], ev["i_hi"] = ev.t_lo.map(idx), ev.t_hi.map(idx)
    ev["s"] = ev.series.map(cols.index)

    out = []
    for key, A in alarms.items():
        hit, delay, lead = [], [], []
        for _, r in ev.iterrows():
            w = np.where(A[r.i_lo:r.i_hi + 1, r.s])[0]
            hit.append(len(w) > 0)
            t_first = ts[r.i_lo + w[0]] if len(w) else pd.NaT
            delay.append((t_first - r.t_start).total_seconds() / 3600 if len(w) and r.precise else np.nan)
            lead.append((r.t_pub - t_first).total_seconds() / 3600 if len(w) and pd.notna(r.t_pub) else np.nan)
        ev[f"hit_{key}"], ev[f"delay_{key}"], ev[f"lead_{key}"] = hit, delay, lead
        # chance: each window moved to a random position in the evaluation period
        L = (ev.i_hi - ev.i_lo).to_numpy()
        chance = np.empty(a.draws)
        for b in range(a.draws):
            st = rng.integers(eval_start, T - L - 1)
            chance[b] = np.mean([A[st[i]:st[i] + L[i] + 1, ev.s[i]].any() for i in range(len(ev))])
        h = np.array(hit)
        boot = [h[rng.integers(0, len(h), len(h))].mean() for _ in range(2000)]
        out.append({"detector": key, "n_events": len(ev), "recall": h.mean(),
                    "recall_ci": tuple(np.percentile(boot, [2.5, 97.5]).round(3)),
                    "chance": chance.mean(), "p_vs_chance": (chance >= h.mean()).mean(),
                    "median_delay_h_precise": np.nanmedian(delay), "n_delay": int(np.isfinite(delay).sum()),
                    "median_lead_vs_media_h": np.nanmedian(lead)})
    res = pd.DataFrame(out)
    ev.drop(columns=["summary_ru"], errors="ignore").to_csv(a.out + f"_{a.mode}_per_event.csv", index=False)
    res.to_csv(a.out + f"_{a.mode}_summary.csv", index=False)
    print(len(ev), "event-series pairs;", ev.precise.sum(), "with precise start;", ev.scope.value_counts().to_dict())
    print(res.round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
