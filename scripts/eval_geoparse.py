"""Evaluate a district geoparser on the expert-verified gold set (9 classes incl. 'none')."""
from __future__ import annotations

import argparse
import json

import pandas as pd
from sklearn.metrics import classification_report, f1_score

CODES = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky",
         "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky"]


def metrics(gold: pd.Series, pred: pd.Series) -> dict:
    has = gold != "none"
    said = pred != "none"
    return {
        "n": int(len(gold)),
        "accuracy_9class": round(float((gold == pred).mean()), 3),
        "macro_f1_districts": round(float(f1_score(gold, pred, labels=CODES, average="macro", zero_division=0)), 3),
        "recall_located": round(float((pred[has] == gold[has]).mean()), 3),
        "precision_assigned": round(float((pred[said] == gold[said]).mean()), 3) if said.any() else None,
        "assigned_share": round(float(said.mean()), 3),
        "false_assign_on_none": round(float(said[~has].mean()), 3),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/raw/geo_gold_final.csv")
    ap.add_argument("--method", choices=["dictionary", "llm", "student"], required=True)
    ap.add_argument("--model", default="gpt-5.4-mini")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--prompt", default="configs/geoparse_prompt_ru.txt")
    ap.add_argument("--hints", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    g = pd.read_csv(a.gold, dtype=str).fillna("")
    if a.method == "dictionary":
        from bursts.thesis_geocoder.geocoder import classify_district
        g["pred"] = [classify_district(t).district_id or "none" for t in g.text]
    elif a.method == "student":
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location("ts", pathlib.Path(__file__).with_name("train_student.py"))
        ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)
        tok = AutoTokenizer.from_pretrained(a.model); mdl = AutoModelForSequenceClassification.from_pretrained(a.model)
        from bursts.geoparse.llm import CODES as _C
        g["pred"] = [_C[i] for i in ts.predict(mdl, tok, g.text.tolist()).argmax(1)]
    else:
        from bursts.geoparse.llm import BatchedLLMGeoparser, LLMGeoparser
        if a.batch_size > 1:
            p = BatchedLLMGeoparser(a.model, "configs/geoparse_prompt_ru.txt", "data/raw/llm_cache.sqlite",
                                    reasoning_effort=a.effort or None, batch_size=a.batch_size)
            g["pred"] = [r["district"] for r in p.classify_many(g.text.tolist())]
        else:
            p = LLMGeoparser(a.model, a.prompt, "data/raw/llm_cache.sqlite",
                             reasoning_effort=a.effort or None, gazetteer_hints=a.hints)
            g["pred"] = [r["district"] for r in p.classify_many(g.text.tolist(), workers=16)]
    res = {"method": a.method, "model": a.model if a.method != "dictionary" else None,
           "all": metrics(g.label, g.pred)}
    for s, part in g.groupby("set"):
        res[s] = metrics(part.label, part.pred)
    if a.method == "llm":
        res["usage"] = p.usage_totals()
    json.dump(res, open(a.out + ".json", "w"), ensure_ascii=False, indent=1)
    g[["id", "set", "label", "pred"]].to_csv(a.out + "_pred.csv", index=False)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(classification_report(g.label, g.pred, zero_division=0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
