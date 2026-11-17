"""Causal anomaly scores for hourly count series. Score at t uses y[:t] as history plus y[t].

All functions take a 1-d float array and return an array of the same length (NaN where the
history is too short). Higher score = more anomalous.
"""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.stats import nbinom, poisson

MAD_K = 1.4826


def _lagged_windows(y: np.ndarray, w: int) -> np.ndarray:
    """Row t holds y[t-w:t]; rows t < w are NaN."""
    out = np.full((len(y), w), np.nan)
    if len(y) > w:
        out[w:] = sliding_window_view(y, w)[:-1]
    return out


def robust_z(y: np.ndarray, w: int = 168, eps: float = 1.0) -> np.ndarray:
    win = _lagged_windows(y, w)
    med = np.median(win, axis=1)
    mad = np.median(np.abs(win - med[:, None]), axis=1)
    return (y - med) / (MAD_K * mad + eps)


def seasonal_lags(y: np.ndarray, days: int) -> np.ndarray:
    out = np.full((len(y), days), np.nan)
    for k in range(1, days + 1):
        out[24 * k:, k - 1] = y[:-24 * k]
    return out


def seasonal_robust_z(y: np.ndarray, days: int = 7, eps: float = 1.0) -> np.ndarray:
    lags = seasonal_lags(y, days)
    med = np.median(lags, axis=1)
    mad = np.median(np.abs(lags - med[:, None]), axis=1)
    return (y - med) / (MAD_K * mad + eps)


def nb_seasonal(y: np.ndarray, days: int = 7, w: int = 336) -> np.ndarray:
    """-log10 upper-tail probability under a seasonal negative binomial predictive."""
    mu = np.clip(np.mean(seasonal_lags(y, days), axis=1), 0.05, None)
    resid = y - mu
    rv = _lagged_windows(resid, w)
    lv = _lagged_windows(mu, w)
    var = np.nanvar(rv, axis=1)
    level = np.nanmean(lv, axis=1)
    phi = np.clip((var - level) / level ** 2, 0.0, None)
    phi = np.where(np.isfinite(phi), phi, 0.0)
    p_tail = np.where(
        phi > 1e-6,
        nbinom.sf(y - 1, 1 / np.maximum(phi, 1e-6), (1 / np.maximum(phi, 1e-6)) / (1 / np.maximum(phi, 1e-6) + mu)),
        poisson.sf(y - 1, mu),
    )
    s = -np.log10(np.clip(p_tail, 1e-300, 1.0))
    s[np.isnan(mu) | np.isnan(level)] = np.nan
    return s


def cusum_residuals(y: np.ndarray, w: int = 168) -> np.ndarray:
    win = _lagged_windows(y, w)
    mu = np.mean(win, axis=1)
    sd = np.clip(np.std(win, axis=1, ddof=1), 1.0, None)
    return (y - mu) / sd


def cusum_alarms(r: np.ndarray, k: float, h: float, s0: float = 0.0) -> tuple[np.ndarray, float]:
    """One-sided CUSUM with reset after alarm. Returns alarms and final state."""
    s, out = s0, np.zeros(len(r), bool)
    for i, v in enumerate(r):
        if np.isnan(v):
            continue
        s = max(0.0, s + v - k)
        if s > h:
            out[i], s = True, 0.0
    return out, s


def chronos_score(y: np.ndarray, q50: np.ndarray, q99: np.ndarray) -> np.ndarray:
    return (y - q50) / (q99 - q50 + 1.0)
