"""Context sanitisation rules for rolling forecasts: what a flagged hour contributes to later contexts."""
from __future__ import annotations

import numpy as np

MODES = ("none", "median", "winsor", "budget")


def sanitized_value(mode: str, y_t: np.ndarray, q50: np.ndarray, q99: np.ndarray,
                    recent_flags: np.ndarray, budget: int = 6) -> np.ndarray:
    """Value stored in the context for hour t. `recent_flags` = flags in the previous 23 hours.

    median: flagged hours -> forecast median (strongest protection, cannot follow level shifts)
    winsor: flagged hours -> upper forecast bound q99 (partial protection, adapts gradually)
    budget: median replacement only while the last 24 h hold at most `budget` flagged hours;
            beyond that the stream is treated as a regime change and kept as observed
    """
    hit = y_t > q99
    if mode == "none":
        return y_t
    if mode == "median":
        return np.where(hit, q50, y_t)
    if mode == "winsor":
        return np.where(hit, q99, y_t)
    if mode == "budget":
        return np.where(hit & (recent_flags + hit <= budget), q50, y_t)
    raise ValueError(mode)
