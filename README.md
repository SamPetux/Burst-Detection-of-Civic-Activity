# Burst Detection of Civic Activity

Code, aggregated data and working documents for the paper
**"Zero-Shot Burst Detection of Civic Activity in Social Media Streams Using Time-Series Foundation Models"**
(M. B. Rotanova, O. V. Frolov, A. S. Shimichev; IEEE ElCon-CN 2027).

Burst detection in geo-referenced social-media streams is treated as constant-false-alarm-rate (CFAR)
detection in a multichannel count signal. Messages of 51 open VKontakte communities of Nizhny Novgorod
are assigned to city districts (community district or an LLM geoparser), aggregated into hourly series,
and an alarm is raised when an observation exceeds the 0.99 quantile of a zero-shot Chronos-2 forecast.
Baselines: seasonal negative binomial, robust z-score, seasonal z-score, CUSUM and STL residuals.

## Repository layout

| Path | Content |
|---|---|
| `paper/` | Manuscript (`ru/`, `en/`), figures and the IEEE layout script `build_docx.py` |
| `bursts/` | Library: series matrix, detectors, Chronos-1 quantiles, context sanitization, geoparsers |
| `scripts/` | Experiments (`exp_*`), analyses (`analyze_confirm`, `confirm_ci`, `eval_events*`), figures (`fig_*`) |
| `configs/` | LLM geoparser prompts |
| `data/series_2026-11/` | Hourly and daily message counts (no texts, no user ids) |
| `docs/06_confirmatory_protocol.md` | Pre-registered confirmatory protocol (hypotheses H1–H4) |
| `docs/07_confirmatory_results.md` | Confirmatory results and post-protocol analyses |
| `docs/05_contribution_design.md` | Decision log |
| `docs/03_sources.md` | Source ledger with verification status |
| `docs/chronicle/` | Chronicle of 96 city events (June–November 2026) from news sites, checked by the authors |

Documents in `docs/` are in Russian.

## Data

`data/series_2026-11/counts_hourly_series.csv.gz` holds hourly counts (posts + comments, Moscow time,
1 March – 17 November 2026) for every community (`grp:<screen_name>`), district (`dst:<district>`) and the
city (`city`). The confirmatory analysis uses the 41 series with at least 0.05 messages per hour from
1 June 2026.

Message texts and author ids are not published. The experiment scripts build the same matrix from the
local corpus (`data/raw/`, not in git) with `bursts.data.hourly_matrix`.

## Reproduction

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
python scripts/exp_rolling_chronos.py --corpus data/raw/corpus_2026-11.csv.gz --geo data/raw/geo_llm_corpus.csv \
  --start 2026-05-18 --end 2026-11-16 --from 2026-06-01 --sanitize none --out results/chronos2_confirm.npz
python scripts/exp_power.py --forecasts results/chronos2_confirm.npz --sanitize none --out results/confirm_h2
```

The full command list of the confirmatory run (H1–H3) is in `docs/06_confirmatory_protocol.md`, section 5.
A CPU is sufficient: Chronos-2 forecasts 42 series in about 0.6 s per hour. Long runs checkpoint and
resume after interruption.

## License

Code: MIT. Aggregated data: CC BY 4.0.
