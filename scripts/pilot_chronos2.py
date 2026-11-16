"""Pilot: zero-shot Chronos-2 one-step-ahead quantile forecast on hourly civic series.
Flags hour t as anomalous if observed > q99 of the forecast made at t-1 (context = up to 336 h)."""
import sys, time, pandas as pd, numpy as np, torch
from chronos import Chronos2Pipeline
torch.set_num_threads(4)
csv = sys.argv[1]
df = pd.read_csv(csv, parse_dates=["timestamp"])
df = df[df.topic_id == "all"]
series = {d: g.sort_values("timestamp").reset_index(drop=True) for d, g in df.groupby("district")}
ids = ["city", "sormovsky", "avtozavodsky", "nizhegorodsky", "unassigned"]
t0 = time.time()
pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
print("load s", round(time.time() - t0, 1))
start = pd.Timestamp("2026-04-14T00:00:00+03:00"); CTX = 336; H = 1
ts_all = series["city"].timestamp
origins = [i for i, t in enumerate(ts_all) if t >= start][:-1]
origins = origins[::3]  # every 3rd hour to keep pilot short
rows = []
t0 = time.time()
for i in origins:
    ctx = pd.concat([series[d].iloc[max(0, i - CTX):i + 1][["timestamp", "n_messages"]].assign(id=d) for d in ids])
    ctx["timestamp"] = ctx["timestamp"].dt.tz_localize(None)
    pred = pipe.predict_df(ctx, prediction_length=H, quantile_levels=[0.5, 0.9, 0.99, 0.995],
                           id_column="id", timestamp_column="timestamp", target="n_messages")
    for d in ids:
        p = pred[pred.id == d].iloc[0]
        y = int(series[d].n_messages.iloc[i + 1])
        rows.append(dict(district=d, ts=series[d].timestamp.iloc[i + 1], y=y, q50=p["0.5"], q90=p["0.9"], q99=p["0.99"], q995=p["0.995"]))
print("origins", len(origins), "sec", round(time.time() - t0, 1), "sec/origin", round((time.time() - t0) / len(origins), 2))
out = pd.DataFrame(rows)
out["flag99"] = out.y > out.q99
out.to_csv(sys.argv[2], index=False)
for d in ids:
    o = out[out.district == d]
    print(d, "n", len(o), "flag99 rate", round(o.flag99.mean(), 3), "cover90", round((o.y <= o.q90).mean(), 3))
print(out[out.flag99].sort_values("ts").to_string())
