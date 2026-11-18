"""Split a gzip CSV corpus into N parts (each with header), roughly equal by rows.

Usage:
    python split_corpus.py corpus_2026-11.csv.gz 2
"""
import csv
import gzip
import sys
from pathlib import Path

src, n = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 2
csv.field_size_limit(10**8)
with gzip.open(src, "rt", encoding="utf-8", newline="") as f:
    rows = list(csv.reader(f))
header, body = rows[0], rows[1:]
size = -(-len(body) // n)
stem = src.name.removesuffix(".csv.gz")
for i in range(n):
    out = src.with_name(f"{stem}_part{i + 1}.csv.gz")
    with gzip.open(out, "wt", encoding="utf-8", newline="") as g:
        w = csv.writer(g)
        w.writerow(header)
        w.writerows(body[i * size:(i + 1) * size])
    print(f"{out.name}: {out.stat().st_size / 1e6:.1f} MB")
