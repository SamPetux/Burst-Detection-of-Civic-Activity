"""Geoparse every post of the city-wide communities with the LLM teacher; comments inherit the
district of their post unless the dictionary geocoder finds an explicit district in the comment.

Output CSV (kind, msg_id, district, source) feeds build_series_corpus.py --geo.
"""
from __future__ import annotations

import argparse

import pandas as pd

from bursts.geoparse.llm import LLMGeoparser
from bursts.thesis_geocoder.geocoder import classify_district


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/raw/corpus_2026-11.csv.gz")
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--out", default="data/raw/geo_llm_corpus.csv")
    ap.add_argument("--cache-only", action="store_true", help="fail on a cache miss instead of calling the API")
    a = ap.parse_args()
    df = pd.read_csv(a.corpus, dtype={"msg_id": str, "post_id": str, "group_district": "string", "district_id": "string"})
    posts = df[(df.kind == "post") & df.group_district.isna()]
    p = LLMGeoparser(a.model, "configs/geoparse_prompt_ru_v2.txt", "data/raw/llm_cache.sqlite",
                     reasoning_effort="low", gazetteer_hints=True)
    p.cache_only = a.cache_only
    ans = p.classify_many(posts.text.fillna("").tolist(), workers=24)
    post_d = dict(zip(posts.msg_id, [x["district"] for x in ans]))

    rows = [("post", m, d, "llm_post") for m, d in post_d.items()]
    com = df[(df.kind == "comment") & df.post_id.isin(post_d)]
    for m, pid, text in zip(com.msg_id, com.post_id, com.text.fillna("")):
        own = classify_district(text).district_id
        if own:
            rows.append(("comment", m, own, "dictionary_comment"))
        elif post_d[pid] != "none":
            rows.append(("comment", m, post_d[pid], "inherited_post"))
        else:
            rows.append(("comment", m, "none", "none"))
    out = pd.DataFrame(rows, columns=["kind", "msg_id", "district", "source"])
    out.to_csv(a.out, index=False)
    print(out.groupby(["kind", "source"]).size().to_string())
    print(p.usage_totals())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
