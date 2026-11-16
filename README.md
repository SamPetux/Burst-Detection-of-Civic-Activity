# Burst Detection of Civic Activity

Code, aggregated data and working documents for the paper
**"Zero-Shot Burst Detection of Civic Activity in Social Media Streams Using Time-Series Foundation Models"**
(paper text is in Russian; code, comments and this README are in English).

The study treats burst detection in geo-referenced social-media streams as anomaly detection in a
multivariate count signal: messages are mapped to city districts (dictionary and LLM geoparsers),
aggregated into hourly series, and a burst is declared when the observation leaves the predictive
interval of a zero-shot time-series foundation model (Chronos-2 and others). The approach is compared
with robust z-score, CUSUM and STL-residual detectors on a set of labeled civic events.

The empirical base comes from the author's earlier platform
[civic-monitor-nn](https://github.com/SamPetux/civic-monitor-nn) (VK communities of Nizhny Novgorod).

## Repository layout

| Path | Content |
|---|---|
| `docs/01_analysis.md` | Critical analysis of the prior work and the data (ru) |
| `docs/02_plan.md` | Work plan with full inputs for executors (ru) |
| `docs/03_sources.md` | Source ledger with verification status (ru) |
| `docs/pilot/` | Pilot run of Chronos-2 on hourly series (CPU) |
| `scripts/build_series.py` | Builds hourly/daily count series from the civic-monitor PostgreSQL dump |
| `scripts/pilot_chronos2.py` | Rolling one-step quantile forecasts with Chronos-2, exceedance flags |
| `data/series/` | Aggregated count series (no texts, no user ids) |

Raw data (the SQL dump with message texts and author ids) is never committed; keep it under `data/raw/`.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -I scripts/build_series.py --dump data/raw/civic_monitor_dump.sql --out data/series --topic-min-size 150
python scripts/pilot_chronos2.py data/series/counts_hourly.csv results/pilot.csv
```

CPU is sufficient: the pilot forecasts 5 series per origin in about 0.12 s with a 336-hour context.

## Data note

`data/series/counts_*.csv` contain message counts per district, topic and time bucket
(Moscow time), built from a dump collected 27 Mar - 6 May 2026. Collection density changes
sharply on 14 Apr 2026 (see `docs/01_analysis.md`, section 3.1); treat the earlier part accordingly.

## License

Code: MIT. Aggregated data: CC BY 4.0.
