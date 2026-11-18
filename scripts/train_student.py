"""Distil the LLM teacher into a small Russian encoder (rubert-tiny2) for district geoparsing on CPU."""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from bursts.geoparse.gazetteer import hints_block
from bursts.geoparse.llm import CODES

LAB = {c: i for i, c in enumerate(CODES)}


def encode(tok, texts, max_len):
    return tok([(t or "")[:1500] + hints_block(t or "") for t in texts], truncation=True,
               max_length=max_len, padding=True, return_tensors="pt")


@torch.inference_mode()
def predict(model, tok, texts, max_len=256, bs=64):
    model.eval()
    out = []
    for b in range(0, len(texts), bs):
        enc = encode(tok, texts[b:b + bs], max_len)
        out.append(model(**enc).logits.softmax(-1).numpy())
    return np.concatenate(out) if out else np.zeros((0, len(CODES)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="data/raw/teacher_labels.csv")
    ap.add_argument("--base", default="cointegrated/rubert-tiny2")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out", default="results/student")
    a = ap.parse_args()
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    torch.set_num_threads(4)
    d = pd.read_csv(a.train, dtype=str).dropna(subset=["teacher"])
    d = d.sample(frac=1, random_state=a.seed).reset_index(drop=True)
    n_val = len(d) // 10
    val, tr = d.iloc[:n_val], d.iloc[n_val:]
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForSequenceClassification.from_pretrained(a.base, num_labels=len(CODES))
    y = torch.tensor([LAB[c] for c in tr.teacher])
    counts = np.bincount(y.numpy(), minlength=len(CODES)).astype(float)
    w = torch.tensor((counts.sum() / (len(CODES) * np.maximum(counts, 1))) ** 0.5, dtype=torch.float)
    loss_fn = torch.nn.CrossEntropyLoss(weight=w)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    best, hist = -1.0, []
    t0 = time.time()
    for ep in range(a.epochs):
        model.train()
        perm = np.random.permutation(len(tr))
        for b in range(0, len(perm), a.bs):
            idx = perm[b:b + a.bs]
            enc = encode(tok, tr.text.iloc[idx].tolist(), a.max_len)
            loss = loss_fn(model(**enc).logits, y[idx])
            opt.zero_grad(); loss.backward(); opt.step()
        pv = predict(model, tok, val.text.tolist(), a.max_len).argmax(1)
        f1 = f1_score([LAB[c] for c in val.teacher], pv, labels=list(range(8)), average="macro", zero_division=0)
        hist.append({"epoch": ep + 1, "val_macro_f1_vs_teacher": round(float(f1), 4), "sec": round(time.time() - t0)})
        print(hist[-1], flush=True)
        if f1 > best:
            best = f1
            model.save_pretrained(a.out); tok.save_pretrained(a.out)
    json.dump({"history": hist, "n_train": len(tr), "n_val": n_val, "base": a.base}, open(a.out + "_train.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
