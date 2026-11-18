"""Send uncached geoparse requests through the OpenAI Batch API (half price, same request bodies).

Requests are byte-identical to LLMGeoparser.classify, so answers land in the same cache and
geoparse_corpus.py then runs entirely from the cache.

    python scripts/geoparse_batch.py submit   # writes results/geo_batch_id.txt
    python scripts/geoparse_batch.py collect  # when the batch is completed
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import pandas as pd

from bursts.geoparse.llm import SCHEMA, LLMGeoparser

ID_FILE = Path("results/geo_batch_id.txt")


def parser() -> LLMGeoparser:
    return LLMGeoparser("gpt-5.5", "configs/geoparse_prompt_ru_v2.txt", "data/raw/llm_cache.sqlite",
                        reasoning_effort="low", gazetteer_hints=True)


def submit(p: LLMGeoparser, corpus: str) -> None:
    df = pd.read_csv(corpus, dtype={"msg_id": str, "group_district": "string"})
    posts = df[(df.kind == "post") & df.group_district.isna()]
    lines, seen = [], set()
    for t in posts.text.fillna(""):
        text = p._with_hints(t[: p.max_chars])
        k = p._key(text)
        if k in seen or p.db.execute("SELECT 1 FROM cache WHERE key=?", (k,)).fetchone():
            continue
        seen.add(k)
        body = {"model": p.model,
                "messages": [{"role": "system", "content": p.system},
                             {"role": "user", "content": f"Сообщение:\n{text}"}],
                "response_format": {"type": "json_schema", "json_schema": SCHEMA},
                "reasoning_effort": p.effort}
        lines.append(json.dumps({"custom_id": k, "method": "POST", "url": "/v1/chat/completions", "body": body},
                                ensure_ascii=False))
    print(f"{len(lines)} requests")
    if not lines:
        return
    f = p.client.files.create(file=("geo_batch.jsonl", io.BytesIO("\n".join(lines).encode())), purpose="batch")
    b = p.client.batches.create(input_file_id=f.id, endpoint="/v1/chat/completions", completion_window="24h")
    ID_FILE.write_text(b.id)
    print("batch", b.id, b.status)


def collect(p: LLMGeoparser) -> int:
    b = p.client.batches.retrieve(ID_FILE.read_text().strip())
    print(b.status, b.request_counts)
    if b.status != "completed":
        return 1
    n = 0
    for line in p.client.files.content(b.output_file_id).text.splitlines():
        r = json.loads(line)
        resp = r.get("response") or {}
        if resp.get("status_code") != 200:
            continue
        body = resp["body"]
        ans = json.loads(body["choices"][0]["message"]["content"])
        p.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)",
                     (r["custom_id"], json.dumps(ans, ensure_ascii=False), json.dumps(body.get("usage", {}))))
        n += 1
    p.db.commit()
    print(f"cached {n} answers")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["submit", "collect"])
    ap.add_argument("--corpus", default="data/raw/corpus_2026-11.csv.gz")
    a = ap.parse_args()
    p = parser()
    if a.action == "submit":
        submit(p, a.corpus)
        return 0
    return collect(p)


if __name__ == "__main__":
    sys.exit(main())
