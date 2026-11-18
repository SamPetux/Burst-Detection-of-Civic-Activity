"""Label a training sample for the student geoparser with the LLM teacher (prompt v2 + gazetteer hints)."""
from __future__ import annotations

import argparse

import pandas as pd

from bursts.geoparse.llm import LLMGeoparser


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/raw/corpus_2026-11.csv.gz")
    ap.add_argument("--gold", default="data/raw/geo_gold_final.csv")
    ap.add_argument("--n-posts", type=int, default=2250)
    ap.add_argument("--n-comments", type=int, default=2250)
    ap.add_argument("--until", default="2026-06-01")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--seed", type=int, default=20261119)
    ap.add_argument("--out", default="data/raw/teacher_labels.csv")
    a = ap.parse_args()
    df = pd.read_csv(a.corpus, dtype={"district_id": "string", "group_district": "string", "msg_id": "string"})
    df["ts"] = pd.to_datetime(df.date_utc, utc=True, format="mixed").dt.tz_convert("Europe/Moscow")
    gold = pd.read_csv(a.gold, dtype=str)
    gold_keys = set(zip(gold.kind, gold.msg_id))
    df = df[(df.ts < a.until) & (df.text.fillna("").str.len() >= 20)]
    df = df[[(k, m) not in gold_keys for k, m in zip(df.kind, df.msg_id)]]
    s = pd.concat([df[df.kind == "post"].sample(a.n_posts, random_state=a.seed),
                   df[df.kind == "comment"].sample(a.n_comments, random_state=a.seed + 1)])
    p = LLMGeoparser(a.model, "configs/geoparse_prompt_ru_v2.txt", "data/raw/llm_cache.sqlite",
                     reasoning_effort="low", gazetteer_hints=True)
    ans = p.classify_many(s.text.tolist(), workers=16)
    s = s.assign(teacher=[x["district"] for x in ans], teacher_conf=[x["confidence"] for x in ans])
    s[["kind", "msg_id", "group", "group_district", "text", "teacher", "teacher_conf"]].to_csv(a.out, index=False)
    print(s.teacher.value_counts().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
