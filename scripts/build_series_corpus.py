"""Hourly/daily message counts from the privacy-reduced corpus (export_corpus.py output).

Series: 8 districts + 'unassigned' + 'city' (sum). District = content/source district stored
in the corpus (dictionary geocoder of civic-monitor); an LLM geoparse file can override it.

Usage:
    python scripts/build_series_corpus.py data/raw/corpus_2026-11.csv.gz data/series_2026-11 [--geo geo.csv]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DISTRICTS = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky",
             "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("out")
    ap.add_argument("--geo", help="CSV msg_id,kind,district overriding the corpus district")
    a = ap.parse_args()
    df = pd.read_csv(a.corpus, usecols=["kind", "msg_id", "date_utc", "district_id"],
                     dtype={"district_id": "string"})
    if a.geo:
        g = pd.read_csv(a.geo, dtype={"district": "string"})
        df = df.merge(g, on=["kind", "msg_id"], how="left")
        df["district_id"] = df.district.fillna(df.district_id)
    df["ts"] = pd.to_datetime(df.date_utc, utc=True, format="mixed").dt.tz_convert("Europe/Moscow")
    df["district"] = df.district_id.where(df.district_id.isin(DISTRICTS), "unassigned")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for freq, name in (("h", "hourly"), ("D", "daily")):
        idx = pd.date_range(df.ts.min().floor(freq), df.ts.max().floor(freq), freq=freq)
        wide = (df.groupby([df.ts.dt.floor(freq), "district"]).size()
                  .unstack(fill_value=0).reindex(idx, fill_value=0))
        wide = wide.reindex(columns=DISTRICTS + ["unassigned"], fill_value=0)
        wide["city"] = wide.sum(axis=1)
        wide.index.name = "timestamp"
        wide.to_csv(out / f"counts_{name}_wide.csv.gz" if freq == "h" else out / f"counts_{name}_wide.csv")
        print(name, wide.shape, "mean/h" if freq == "h" else "mean/d", wide.mean().round(2).to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
