# Exploratory results: alarm-rate calibration and injected-burst power

Data: 43 hourly series (communities, districts, city), calibration 2026-03-15..04-14, evaluation 2026-04-15..05-31. Alpha = 1 %.

## Alarm rate without volume floor, nominal thresholds

|                               |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|:------------------------------|-----------:|--------------:|-----------:|-------------:|--------:|
| share of series in [0.5%, 2%] |       0.98 |          0.6  |       0.33 |         0.26 |    0.47 |
| median alarm rate, %          |       1.3  |          1.65 |       1.65 |         1.82 |    1.65 |
| max alarm rate, %             |       1.91 |          3.04 |       7.81 |         6.25 |    3.04 |

## Alarm rate without volume floor, calib thresholds

|                               |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|:------------------------------|-----------:|--------------:|-----------:|-------------:|--------:|
| share of series in [0.5%, 2%] |       0.88 |          0.74 |       0.26 |         0.49 |    0.84 |
| median alarm rate, %          |       1.04 |          1.13 |       0.52 |         0.61 |    1.04 |
| max alarm rate, %             |       2.52 |          3.65 |       4.08 |         3.47 |    6.16 |

## Detection probability (%) by amplitude, calib thresholds

|   A |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|----:|-----------:|--------------:|-----------:|-------------:|--------:|
|   1 |       10.6 |          12   |        4.6 |          6.5 |     4.9 |
|   2 |       28.3 |          29.8 |       11.2 |         15.9 |    11.6 |
|   3 |       46.3 |          46.8 |       21.2 |         30.7 |    22.2 |
|   5 |       71.6 |          68.4 |       39.8 |         54.6 |    40.1 |
|   8 |       89.8 |          81.8 |       63.1 |         73.6 |    56.8 |

## Detection probability (%) by amplitude, nominal thresholds

|   A |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|----:|-----------:|--------------:|-----------:|-------------:|--------:|
|   1 |       10.3 |          13   |        6.4 |         13.5 |     3.8 |
|   2 |       27.6 |          32.7 |       17.5 |         30.6 |     8.5 |
|   3 |       45   |          51.3 |       31.6 |         48.3 |    19.5 |
|   5 |       70.8 |          74.3 |       57.8 |         78.6 |    45   |
|   8 |       89.6 |          88.1 |       76.7 |         93.4 |    68.7 |

## Detection probability (%) by intensity stratum, A in {2,3,5}, calibrated

| rate_per_hour   |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|:----------------|-----------:|--------------:|-----------:|-------------:|--------:|
| 0.05-0.3        |       66.4 |          64.9 |       56.1 |         61.7 |    60.8 |
| 0.3-1           |       62.8 |          62.7 |       30.1 |         38   |    28.3 |
| 1-5             |       40   |          37.1 |        5.2 |         20   |     7.3 |
| >5              |       20.4 |          24.9 |       12   |         20.4 |    10.1 |

## Detection probability (%) by duration, h, A in {2,3,5}, calibrated

|   D |   chronos2 |   nb_seasonal |   robust_z |   seasonal_z |   cusum |
|----:|-----------:|--------------:|-----------:|-------------:|--------:|
|   1 |       44.1 |          37.2 |       21.4 |         27.4 |    17.1 |
|   3 |       47   |          46.6 |       23.2 |         32.4 |    23.9 |
|   6 |       55.1 |          61.2 |       27.6 |         41.4 |    32.9 |

## Mean delay (h) among detected bursts, D = 6 h, calibrated

|             |   delay_h |
|:------------|----------:|
| chronos2    |      0.27 |
| nb_seasonal |      0.66 |
| robust_z    |      0.25 |
| seasonal_z  |      0.5  |
| cusum       |      0.7  |
