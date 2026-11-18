"""Exact one-step quantiles from Chronos-1 (T5) token distributions.

Chronos-1 samples tokens; for horizon 1 the full categorical distribution is available from a
single decoder step, so quantiles are read from its CDF instead of from sample paths
(no top-k truncation, temperature 1).
"""
from __future__ import annotations

import numpy as np
import torch
from chronos import ChronosPipeline


class Chronos1Quantiles:
    def __init__(self, model: str, levels: list[float]):
        self.pipe = ChronosPipeline.from_pretrained(model, device_map="cpu", dtype=torch.float32)
        self.tok, self.net = self.pipe.tokenizer, self.pipe.model.model
        cfg = self.pipe.model.config
        self.first_value_token = cfg.n_special_tokens + 1
        self.levels = torch.tensor(levels)

    @torch.no_grad()
    def predict(self, contexts: np.ndarray) -> np.ndarray:
        """contexts (n_series, length) -> quantiles (n_series, n_levels)."""
        ids, mask, scale = self.tok.context_input_transform(torch.as_tensor(contexts, dtype=torch.float32))
        start = torch.full((ids.shape[0], 1), self.net.config.decoder_start_token_id)
        logits = self.net(input_ids=ids, attention_mask=mask, decoder_input_ids=start).logits[:, -1, :]
        p = torch.softmax(logits[:, self.first_value_token:self.first_value_token + len(self.tok.centers)], -1)
        cdf = p.cumsum(-1) / p.sum(-1, keepdim=True)
        idx = torch.searchsorted(cdf.contiguous(), self.levels.expand(len(cdf), -1).contiguous())
        idx = idx.clamp(max=len(self.tok.centers) - 1)
        return (self.tok.centers[idx] * scale[:, None]).numpy()
