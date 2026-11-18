"""District geoparser backed by an OpenAI chat model with a JSON-schema answer and a disk cache.

The API key is read by the OpenAI client from OPENAI_API_KEY; in the cloud session a network
proxy injects the real key, so a placeholder value is enough there.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

CODES = ["avtozavodsky", "kanavinsky", "leninsky", "moskovsky",
         "nizhegorodsky", "priokskiy", "sovetsky", "sormovsky", "none"]
SCHEMA = {
    "name": "district_answer",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "district": {"type": "string", "enum": CODES},
            "evidence": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["district", "evidence", "confidence"],
    },
}


class LLMGeoparser:
    def __init__(self, model: str, prompt_path: str, cache_path: str, reasoning_effort: str | None = "low",
                 max_chars: int = 1500, gazetteer_hints: bool = False):
        self.hints = gazetteer_hints
        self.cache_only = False
        self.model, self.effort, self.max_chars = model, reasoning_effort, max_chars
        self.system = Path(prompt_path).read_text(encoding="utf-8")
        self.prompt_hash = hashlib.sha1(self.system.encode()).hexdigest()[:10]
        self.client = OpenAI(max_retries=5, timeout=120)
        self.db = sqlite3.connect(cache_path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, answer TEXT, usage TEXT)")
        self.lock = threading.Lock()

    def _key(self, text: str) -> str:
        return hashlib.sha1(f"{self.model}|{self.effort}|{self.prompt_hash}|{text}".encode()).hexdigest()

    def _with_hints(self, text: str) -> str:
        if not self.hints:
            return text
        from bursts.geoparse.gazetteer import hints_block
        return text + hints_block(text)

    def classify(self, text: str) -> dict:
        text = self._with_hints((text or "")[: self.max_chars])
        k = self._key(text)
        with self.lock:
            row = self.db.execute("SELECT answer FROM cache WHERE key=?", (k,)).fetchone()
        if row:
            return json.loads(row[0])
        if self.cache_only:
            raise RuntimeError("cache miss with cache_only=True; no API call made")
        kwargs = {}
        if self.effort:
            kwargs["reasoning_effort"] = self.effort
        for attempt in range(4):
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system},
                              {"role": "user", "content": f"Сообщение:\n{text}"}],
                    response_format={"type": "json_schema", "json_schema": SCHEMA},
                    **kwargs,
                )
                ans = json.loads(r.choices[0].message.content)
                break
            except Exception as e:  # noqa: BLE001 - network/parse errors are retried, then surfaced
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        usage = json.dumps(r.usage.model_dump() if r.usage else {})
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (k, json.dumps(ans, ensure_ascii=False), usage))
            self.db.commit()
        return ans

    def classify_many(self, texts: list[str], workers: int = 8) -> list[dict]:
        with ThreadPoolExecutor(workers) as ex:
            return list(ex.map(self.classify, texts))

    def usage_totals(self) -> dict:
        tot = {"prompt_tokens": 0, "completion_tokens": 0, "n": 0}
        for (u,) in self.db.execute("SELECT usage FROM cache"):
            u = json.loads(u or "{}")
            tot["prompt_tokens"] += u.get("prompt_tokens", 0)
            tot["completion_tokens"] += u.get("completion_tokens", 0)
            tot["n"] += 1
        return tot


BATCH_SCHEMA = {
    "name": "district_answers",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {"answers": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"id": {"type": "integer"},
                           "district": {"type": "string", "enum": CODES},
                           "evidence": {"type": "string"},
                           "confidence": {"type": "number"}},
            "required": ["id", "district", "evidence", "confidence"]}}},
        "required": ["answers"],
    },
}


class BatchedLLMGeoparser(LLMGeoparser):
    """Several messages per request (independent decisions), for low request-per-minute quotas."""

    def __init__(self, *args, batch_size: int = 20, rpm: int = 9, **kw):
        super().__init__(*args, **kw)
        self.batch_size, self.min_interval = batch_size, 60.0 / rpm
        self._last = 0.0

    def _key(self, text: str) -> str:
        return hashlib.sha1(f"batch{self.batch_size}|{self.model}|{self.effort}|{self.prompt_hash}|{text}".encode()).hexdigest()

    def _throttle(self):
        wait = self._last + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    def _call(self, texts: list[str]) -> list[dict]:
        body = "\n\n".join(f"### Сообщение {i + 1}\n{t}" for i, t in enumerate(texts))
        user = (f"Ниже {len(texts)} независимых сообщений. Реши для каждого отдельно по правилам и верни "
                f"массив answers, по одному элементу на сообщение, id = номер сообщения.\n\n{body}")
        kwargs = {"reasoning_effort": self.effort} if self.effort else {}
        for attempt in range(6):
            self._throttle()
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.system}, {"role": "user", "content": user}],
                    response_format={"type": "json_schema", "json_schema": BATCH_SCHEMA}, **kwargs)
                ans = {a["id"]: a for a in json.loads(r.choices[0].message.content)["answers"]}
                if all(i + 1 in ans for i in range(len(texts))):
                    usage = r.usage.model_dump() if r.usage else {}
                    return [dict(ans[i + 1], _usage=usage if i == 0 else {}) for i in range(len(texts))]
            except Exception:  # noqa: BLE001
                if attempt == 5:
                    raise
                time.sleep(10 * (attempt + 1))
        raise RuntimeError("incomplete batch answer")

    def classify_many(self, texts: list[str], workers: int = 1) -> list[dict]:
        texts = [(t or "")[: self.max_chars] for t in texts]
        keys = [self._key(t) for t in texts]
        out: dict[str, dict] = {}
        for k in set(keys):
            row = self.db.execute("SELECT answer FROM cache WHERE key=?", (k,)).fetchone()
            if row:
                out[k] = json.loads(row[0])
        todo = list(dict.fromkeys(k for k in keys if k not in out))
        text_of = dict(zip(keys, texts))
        for b in range(0, len(todo), self.batch_size):
            chunk = todo[b:b + self.batch_size]
            res = self._call([text_of[k] for k in chunk])
            for k, a in zip(chunk, res):
                usage = a.pop("_usage")
                a.pop("id", None)
                out[k] = a
                self.db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)",
                                (k, json.dumps(a, ensure_ascii=False), json.dumps(usage)))
            self.db.commit()
            print(f"llm batches {b // self.batch_size + 1}/{-(-len(todo) // self.batch_size)}", flush=True)
        return [out[k] for k in keys]
