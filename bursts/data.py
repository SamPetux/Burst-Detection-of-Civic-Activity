"""Hourly count matrices built from the privacy-reduced corpus."""
from __future__ import annotations

import pandas as pd

DISTRICTS = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky",
             "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky"]
TZ = "Europe/Moscow"


def load_messages(corpus_path: str) -> pd.DataFrame:
    df = pd.read_csv(corpus_path, usecols=["kind", "msg_id", "group", "date_utc", "district_id"],
                     dtype={"district_id": "string", "group": "string"})
    df["ts"] = pd.to_datetime(df.date_utc, utc=True, format="mixed").dt.tz_convert(TZ)
    df["district"] = df.district_id.where(df.district_id.isin(DISTRICTS), "unassigned")
    return df


def hourly_matrix(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Columns: grp:<screen_name>, dst:<district>, city. Dense hourly index [start, end)."""
    idx = pd.date_range(pd.Timestamp(start, tz=TZ), pd.Timestamp(end, tz=TZ), freq="h", inclusive="left")
    h = df.ts.dt.floor("h")
    by_group = df.groupby([h, "group"]).size().unstack(fill_value=0).add_prefix("grp:")
    by_dist = df.groupby([h, "district"]).size().unstack(fill_value=0).add_prefix("dst:")
    wide = pd.concat([by_group, by_dist], axis=1).reindex(idx, fill_value=0).fillna(0)
    wide["city"] = by_dist.reindex(idx, fill_value=0).sum(axis=1)
    wide.index.name = "timestamp"
    return wide.astype(float)
