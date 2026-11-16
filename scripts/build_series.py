"""Aggregate the civic-monitor PostgreSQL dump into hourly/daily count series.

Input : a plain-SQL pg_dump of the civic-monitor-nn database (COPY ... FROM stdin blocks).
Output: tidy CSV files with message counts (posts + comments) per
        (district | city) x (topic | all) x time bucket, plus negative-share columns.

Only aggregated counts leave this script: raw texts and author ids never reach the output,
so the result can be committed to the public repository.

Usage:
    python scripts/build_series.py --dump path/to/civic_monitor_dump.sql --out data/series
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

MSK = timezone(timedelta(hours=3))  # VK timestamps are UTC; bucket in local (Moscow) time


def read_copy_blocks(path: Path) -> dict[str, tuple[list[str], list[list[str]]]]:
    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    cur = None
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("COPY public."):
                name = line.split()[1].split(".")[1]
                cols = line[line.index("(") + 1:line.index(")")].split(", ")
                cur = name
                tables[name] = (cols, [])
                continue
            if cur is None:
                continue
            if line.startswith("\\."):
                cur = None
                continue
            tables[cur][1].append(line.rstrip("\n").split("\t"))
    return tables


def parse_ts(s: str) -> datetime | None:
    if s == "\\N":
        return None
    # pg_dump format: 2026-04-14 12:34:56+00 or with fractional seconds
    base = s[:19]
    dt = datetime.fromisoformat(base).replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--start", default=None, help="ISO date, inclusive (local time)")
    ap.add_argument("--end", default=None, help="ISO date, inclusive (local time)")
    ap.add_argument("--topic-min-size", type=int, default=0,
                    help="keep per-topic series only for topics with at least this many messages "
                         "(0 = keep all; geo x all-topics series are always kept)")
    args = ap.parse_args()

    tables = read_copy_blocks(args.dump)
    pcols, posts = tables["posts"]
    ccols, comments = tables["comments"]
    topics = {r[0]: r[1] for r in tables["topics"][1]}

    # message stream: (ts, district, topic, is_negative, kind)
    stream: list[tuple[datetime, str, str, int, str]] = []
    pi = {c: i for i, c in enumerate(pcols)}
    ci = {c: i for i, c in enumerate(ccols)}
    for r in posts:
        ts = parse_ts(r[pi["date"]])
        if ts is None:
            continue
        stream.append((ts, r[pi["district_id"]], r[pi["topic_id"]],
                       int(r[pi["sentiment"]] == "negative"), "post"))
    for r in comments:
        ts = parse_ts(r[ci["date"]])
        if ts is None:
            continue
        stream.append((ts, r[ci["district_id"]], r[ci["topic_id"]],
                       int(r[ci["sentiment"]] == "negative"), "comment"))

    topic_size: dict[str, int] = defaultdict(int)
    for _ts, _d, topic, _neg, _k in stream:
        topic_size[topic] += 1
    keep_topic = {t for t, n in topic_size.items() if n >= args.topic_min_size and t != "\\N"}

    lo = min(s[0] for s in stream).date()
    hi = max(s[0] for s in stream).date()
    if args.start:
        lo = max(lo, datetime.fromisoformat(args.start).date())
    if args.end:
        hi = min(hi, datetime.fromisoformat(args.end).date())

    args.out.mkdir(parents=True, exist_ok=True)

    for freq, key in (("hourly", lambda t: t.replace(minute=0, second=0, microsecond=0)),
                      ("daily", lambda t: t.replace(hour=0, minute=0, second=0, microsecond=0))):
        agg: dict[tuple[str, str, datetime], list[int]] = defaultdict(lambda: [0, 0])
        for ts, district, topic, neg, _kind in stream:
            if not (lo <= ts.date() <= hi):
                continue
            b = key(ts)
            d = district if district != "\\N" else "unassigned"
            t = topic if topic in keep_topic else None
            for dk in (d, "city"):
                for tk in ((t, "all") if t is not None else ("all",)):
                    agg[(dk, tk, b)][0] += 1
                    agg[(dk, tk, b)][1] += neg
        # dense grid: every (district, topic) series gets every bucket, zeros included
        step = timedelta(hours=1) if freq == "hourly" else timedelta(days=1)
        first = key(datetime.combine(lo, datetime.min.time(), MSK))
        last = key(datetime.combine(hi, datetime.max.time(), MSK).replace(microsecond=0))
        buckets = []
        cur = first
        while cur <= last:
            buckets.append(cur)
            cur += step
        series_keys = sorted({(d, t) for d, t, _ in agg})
        out = args.out / f"counts_{freq}.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["district", "topic_id", "topic_label", "timestamp", "n_messages", "n_negative"])
            for d, t in series_keys:
                label = "all" if t == "all" else ("none" if t == "none" else topics.get(t, ""))
                for b in buckets:
                    n, neg = agg.get((d, t, b), (0, 0))
                    w.writerow([d, t, label, b.isoformat(), n, neg])
        print(f"{out}: {len(series_keys)} series x {len(buckets)} buckets", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
