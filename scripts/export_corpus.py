"""Export a privacy-reduced message corpus from a civic-monitor PostgreSQL dump.

Keeps what the study needs (time, community, district, text) and drops author ids,
the users table, likes and VK mention links. Output is a gzip-compressed CSV.

Usage:
    python export_corpus.py civic_monitor_dump_2026-11.sql corpus_2026-11.csv.gz
"""
from __future__ import annotations

import csv
import gzip
import re
import sys
from pathlib import Path

MENTION = re.compile(r"\[(?:id|club|public)\d+\|([^\]]*)\]")
PROFILE_LINK = re.compile(r"(?:https?://)?(?:m\.)?vk\.com/(?:id\d+|[A-Za-z0-9_.]+)")


def read_copy_blocks(path: Path, wanted: set[str]) -> dict[str, tuple[list[str], list[list[str]]]]:
    tables: dict[str, tuple[list[str], list[list[str]]]] = {}
    cur = None
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("COPY public."):
                name = line.split()[1].split(".")[1]
                cur = name if name in wanted else None
                if cur:
                    cols = line[line.index("(") + 1:line.index(")")].split(", ")
                    tables[cur] = (cols, [])
                continue
            if cur is None:
                continue
            if line.startswith("\\."):
                cur = None
                continue
            tables[cur][1].append(line.rstrip("\n").split("\t"))
    return tables


def unescape_copy(s: str) -> str:
    if s == "\\N":
        return ""
    return s.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ").replace("\\\\", "\\")


def scrub(text: str) -> str:
    text = MENTION.sub(r"\1", text)
    return PROFILE_LINK.sub("[link]", text)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    t = read_copy_blocks(src, {"groups", "posts", "comments"})
    gcols, groups = t["groups"]
    gi = {c: i for i, c in enumerate(gcols)}
    group = {r[gi["id"]]: (r[gi["screen_name"]], unescape_copy(r[gi["district_id"]])) for r in groups}

    pcols, posts = t["posts"]
    pi = {c: i for i, c in enumerate(pcols)}
    post_group = {r[pi["id"]]: r[pi["group_id"]] for r in posts}

    ccols, comments = t["comments"]
    ci = {c: i for i, c in enumerate(ccols)}

    n = 0
    with gzip.open(dst, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "msg_id", "post_id", "group", "group_district", "date_utc",
                    "district_id", "district_confidence", "text"])
        for r in posts:
            g, gd = group.get(r[pi["group_id"]], ("", ""))
            w.writerow(["post", r[pi["id"]], r[pi["id"]], g, gd, unescape_copy(r[pi["date"]]),
                        unescape_copy(r[pi["district_id"]]), unescape_copy(r[pi["district_confidence"]]),
                        scrub(unescape_copy(r[pi["text"]]))])
            n += 1
        for r in comments:
            g, gd = group.get(post_group.get(r[ci["post_id"]], ""), ("", ""))
            w.writerow(["comment", r[ci["id"]], r[ci["post_id"]], g, gd, unescape_copy(r[ci["date"]]),
                        unescape_copy(r[ci["district_id"]]), unescape_copy(r[ci["district_confidence"]]),
                        scrub(unescape_copy(r[ci["text"]]))])
            n += 1
    print(f"{dst}: {n} messages, {dst.stat().st_size / 1e6:.1f} MB "
          f"({len(posts)} posts, {len(comments)} comments, {len(groups)} groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
