<!-- English version of paper/ru/paper_ru.md (6 pages IEEE A4). Numbers: docs/07_confirmatory_results.md.
     Reference keys ⟨…⟩ map to docs/03_sources.md. -->

# Zero-Shot Burst Detection of Civic Activity in Social Media Streams Using Time-Series Foundation Models

Mira B. Rotanova (Linguistics University of Nizhny Novgorod, Nizhny Novgorod, Russia, miraborisovna@gmail.com),
Oleg V. Frolov (HSE University, Nizhny Novgorod, Russia, olegfr101@gmail.com),
Alexey S. Shimichev (Minin Nizhny Novgorod State Pedagogical University, Nizhny Novgorod, Russia, Alexshim@list.ru)

**Abstract.** Social media have become a primary source of real-time signals about urban incidents, yet their streams are non-stationary, sparse and unevenly distributed across a city. Classical statistical anomaly detectors require a threshold tuned to every series. We treat burst detection of civic activity as anomaly detection in a multichannel geo-referenced count signal under a constant false alarm rate requirement. Messages are assigned to districts by a geoparser based on a large language model and aggregated into hourly series; an alarm is raised when an observation exceeds an upper quantile of the probabilistic forecast of the Chronos-2 time-series foundation model applied without training on the target data. On 41 community, district and city series of Nizhny Novgorod, under a pre-registered protocol, the model detected injected bursts at least as often as the best statistical method and more often than the others (53.7% vs 52.9% for a seasonal negative binomial model and 29–41% for the robust z-score, CUSUM and STL decomposition), and earlier: within the first burst hour in 48.5% vs 43.7% of cases ($p < 10^{-50}$). Without context sanitization the false alarm rate stayed within the target band on 95% of series with no parameter tuning. We quantify the cost of a past burst contaminating the model context. On real events the model never alarmed later than the statistical methods, and in some cases it alarmed before the news media reported the event.

**Keywords:** anomaly detection; time-series foundation models; social media; geoparsing; signal processing; smart city.

## I. Introduction

Residents report a burst pipe, a power outage or a traffic jam after an accident in city communities on social networks, and such events appear as a burst in the number of posts and comments in a district community, a city-wide public page or the city as a whole [1], [2]. Newsrooms routinely take eyewitness reports, photos and videos from social networks, especially for breaking news [3]. City communities act as a broadcasting network in which residents are both sources and recipients of messages, and the stream intensity at each network node is a signal of the state of the territory. Civic activity monitoring therefore reduces to burst detection in a set of count time series, and situation centers and services that communicate with residents need such signals at a known false alarm rate and with minimal delay.

The series of a single city differ in intensity by three orders of magnitude, from one message per day to dozens per hour. Many consist mostly of zeros, all have daily seasonality, and their level drifts with community audiences. The thresholds of a robust z-score, cumulative sum (CUSUM) [4] or seasonal-trend decomposition using Loess (STL) [5] mean different things on different series: the same threshold gives one alarm per month on a sparse series and several per day on a dense one.

In radar, this problem is solved by the constant false alarm rate (CFAR) requirement: the threshold is set from a local estimate of clutter so that the false alarm rate does not depend on the background level [6]. We carry this requirement over to message streams and use the probabilistic forecast of a time-series foundation model (TSFM) as the clutter estimate. Such models are trained on large collections of heterogeneous series and forecast a new series without fine-tuning (zero-shot) [7], [8]. If the forecast quantiles are calibrated [9], the rule "alarm when the observation exceeds the $1-\alpha$ quantile" is a CFAR detector with false alarm rate $\alpha$.

Our contributions are as follows:
1) we formulate the task as CFAR detection in a geo-referenced count signal and propose a pipeline "large language model (LLM) geoparser — hourly series — Chronos-2 quantile forecast" with no per-series tuning;
2) under a pre-registered protocol we show that, at an equal false alarm rate, the zero-shot model detects bursts at least as often as the best statistical method, more often than z-scores, CUSUM and STL, and earlier than all of them;
3) we show that the model's own uncalibrated quantiles keep the false alarm rate within $[0.5\alpha, 2\alpha]$ on 95% of series, and we measure the cost of sanitizing the context after a burst;
4) we evaluate the detectors on a chronicle of real events, verifying alarms against message content.

## II. Related Work

Event detection in social networks builds on the model of a burst as a transition of the stream to a high-intensity state [10] and on users as "social sensors" [1]; methods are surveyed in [2]. These works measure recall over events but do not control the false alarm rate across series of different intensity. In epidemiological surveillance the threshold is the upper prediction limit of a quasi-Poisson regression [11], a direct predecessor of our rule, but with a model tuned manually to each series.

TSFMs are applied to anomaly detection through point-forecast error, internal representations or specialized models [12]; on multivariate data the model is known to adapt to an anomaly and stop seeing it [13]. The closest work [14] calibrates alarms over a TSFM forecast with a conformal method based on the error history. Our setting differs in three respects: we test the calibration of the model's own predictive distribution without estimating it from the series history; our data are sparse count series rather than dense sensor signals; and we measure the cost of context contamination for the false alarm rate.

LLMs resolve toponyms more accurately than gazetteer-based systems without training on the target region [15]. District assignment of VKontakte messages has been used to study territorial differences in social well-being [16]. City and district VKontakte communities are an established form of hyperlocal media that shapes the local agenda [17]. We therefore use this platform: a community wall is open for comments with a reply tree and exact timestamps, and its history is available through a public API.

## III. Problem Statement and Method

*Signal.* Each message has a timestamp and possibly a district $d \in \mathcal{D}$. For a series $s$ (community, district or city) and hour $t$, the count $y_{s,t}$ is the number of messages of the series in that hour. This yields a multichannel count signal $\mathbf{y}_t = (y_{1,t},\dots,y_{S,t})$.

*Task.* The detector is causal: the decision for hour $t$ uses $y_{s,1},\dots,y_{s,t}$. The CFAR requirement: at level $\alpha$, the alarm rate must be close to $\alpha$ for every series without threshold tuning. At this rate the detector should find as many bursts as possible, as early as possible.

*Detector.* Chronos-2 [8] receives a context of the last $L = 336$ hours and returns 21 quantiles of the one-step forecast $\hat q^{(\gamma)}_{s,t}$, $\gamma \in [0.01, 0.99]$. The nominal rule is $a_{s,t} = \mathbb{1}[\,y_{s,t} > \hat q^{(1-\alpha)}_{s,t}\,]$, $\alpha = 0.01$. For ranking and the calibrated mode we use the score $z_{s,t} = (y_{s,t} - \hat q^{(0.5)}_{s,t}) / (\hat q^{(0.99)}_{s,t} - \hat q^{(0.5)}_{s,t} + 1)$. In the power analysis and on real events, an alarm of any method requires $y_{s,t} \ge 3$. The model runs on a CPU; forecasting 42 series takes about 0.6 s per hour.

*Context sanitization.* A burst in the context shifts the forecast upward, and the next burst is detected worse [13]. An alarm hour can be replaced in subsequent contexts by the forecast median (median) or by its 0.99 quantile (winsor). On exploratory data winsor was selected as the only variant that changed the alarm rate by less than $0.5\alpha$.

*District assignment.* Messages of district communities inherit the community district. Posts of city-wide communities are labelled by an LLM (gpt-5.5) following an instruction that lists the city districts and hints from a street gazetteer; the model returns a district or abstains. Comments inherit the district of their post. On a held-out set of 400 manually labelled messages, macro-F1 was 0.73 [0.58, 0.84] vs 0.51 for the gazetteer.

*Baselines.* A robust z-score on the median and median absolute deviation over 168 h and its seasonal variant (same hour over 7 days); CUSUM of standardized residuals [4]; STL with a daily period, refitted once a day on 336 h, with a robust z-score of the residual [5]; a seasonal negative binomial (SNB) model with the mean over the same hours of 7 days. Nominal thresholds: $z > 3.5$ (z-scores, STL), tail probability 0.01 (SNB), $h = 5$ (CUSUM). Calibrated thresholds are set per series so that the alarm rate over the calibration month equals $\alpha$; this compares detection power at an equal alarm rate.

## IV. Experiments

*Data.* The corpus covers 51 open VKontakte communities of Nizhny Novgorod (43 district and 8 city-wide) from March 1 to November 17, 2026: 46,346 posts and 370,291 comments. Message texts are not released; hourly counts and code are available at https://github.com/SamPetux/Burst-Detection-of-Civic-Activity. The analysis is split into an exploratory part (March–May) and a confirmatory part (June to November 15); hypotheses, criteria and the method variant were fixed before the confirmatory data were accessed. The confirmatory part contains 41 series with intensity from 0.06 to 59 messages per hour; the calibration month is June, and evaluation runs from July 1 to November 15 (3,288 h).

*Synthetic bursts.* At a random hour $t_0$ we add $\Delta_{t_0+k} \sim \mathrm{Poisson}(A\sqrt{\mu+1}\,e^{-k/\max(D/2,\,0.5)})$ to the series, where $\mu$ is the mean of the same hour over the previous 7 days, $A \in \{1,2,3,5,8\}$ and $D \in \{1,3,6\}$ h; 18 onsets per series, 11,340 injections in total. Forecasts for hours inside a burst are recomputed with a context that already contains the injected hours. For context contamination, a first burst ($A=8$, $D=6$) precedes a second one ($A \in \{2,3,5\}$, $D=1$) by 6, 12 or 24 h.

*Real events.* A chronicle of 96 events from June to November (accidents, fires, outages, drone attacks, transport disruptions, government decisions) was compiled from city news sites independently of the alarms; scope and district were verified by the authors. A district event is matched to the district series and a city-wide event to the city series. The event window runs from its start (or midnight of the day) to publication plus 12 h. An alarm counts only if the messages of the alarm hour relate to the event; this was checked against message texts blind to the detector.

*Metrics.* Alarm rate and share of series within $[0.5\alpha, 2\alpha]$ by intensity stratum; detection probability (Pd) and first-hour detection at the calibrated threshold; paired comparisons with McNemar's test [18], Holm correction over three hypotheses; 95% intervals by bootstrap over series.

## V. Results

*False-alarm rate.* Table I shows the share of series within the band at nominal thresholds. Chronos-2 without sanitization stays within the band on 95% of series [88, 100], with a median alarm rate of 1.36%. For the statistical methods the alarm rate grows with series intensity (Spearman ρ from +0.35 to +0.94), and STL, seasonal z and CUSUM keep only 29–44% of series within the band. Fig. 1 shows that on dense series the observed exceedance frequency matches the nominal one across the whole range, while on sparse series the 0.99 tail deviates by at most a factor of 1.6. The pre-selected winsor variant failed the protocol criterion (61% of series, 31–33% in the sparse strata): replacing an outlier by the 0.99 quantile distorts the context of a mostly-zero series, and alarms come in runs.

**Table I.** Share of series with alarm rate in $[0.5%, 2%]$, nominal thresholds.

| Stratum, msg/h | n | Chronos-2 none | Chronos-2 winsor | SNB | Robust z | Seasonal z | STL | CUSUM |
|---|---|---|---|---|---|---|---|---|
| 0.05–0.3 | 9 | 1.00 | 0.33 | 0.78 | 0.22 | 0.22 | 0.22 | 0.00 |
| 0.3–1 | 13 | 0.85 | 0.31 | 0.92 | 0.62 | 0.69 | 0.69 | 0.85 |
| 1–5 | 12 | 1.00 | 0.92 | 0.67 | 0.42 | 0.08 | 0.08 | 0.50 |
| > 5 | 7 | 1.00 | 1.00 | 0.86 | 0.71 | 0.00 | 0.00 | 0.14 |
| All | 41 | 0.95 | 0.61 | 0.80 | 0.49 | 0.29 | 0.29 | 0.44 |

*Power and speed.* At calibrated thresholds Chronos-2 detected 53.7% of injected bursts [49.6, 57.8], SNB 52.9%, seasonal z 41.2%, STL 36.8%, robust z 29.8% and CUSUM 29.2% (Fig. 2a). The gap to the best method does not exceed 2 pp in any stratum; McNemar's test shows a significant advantage over SNB (706 vs 610, $p = 0.009$), but another seed of the injection generator gives parity (54.5% vs 54.6%). Over STL, z-scores and CUSUM the advantage is several-fold on series above 1 message per hour (45% vs 7–29%). The model detects earlier: within the first burst hour in 48.5% of injections vs 43.7% for SNB (877 vs 333, $p < 10^{-50}$; with another seed 49.2% vs 45.0%), 35.1% for seasonal z, 33.2% for STL and 22.9% for CUSUM. For 6-hour bursts the mean delay among detected ones is 0.30 h vs 0.56 h for SNB and 0.58 h for CUSUM.

*Context contamination.* A strong first burst cuts detection of a second burst 6 h later threefold, from 48% to 16% (Fig. 2b; 507 vs 1 pairs, $p \approx 10^{-150}$). Winsor partly restores sensitivity (21 / 44 / 36% at gaps of 6 / 12 / 24 h) and median replacement almost fully (42 / 50 / 52%), but both raise the false alarm rate on sparse series: winsor by 0.55 pp, median up to 8.2% on exploratory data. A causal detector cannot tell the onset of a short burst from a level shift, so the trade-off between sensitivity after an event and a constant alarm rate is set by the operator. SNB loses sensitivity more strongly and for longer (40 / 30 / 15%), since the first burst enters its seasonal history.

*Real events.* The evaluation period contains 67 event–series pairs. A coincidence of an alarm with an event window is often accidental: without content verification Chronos-2 "detected" 40% of events against a chance level of 20%, and with verification against message texts 12% [4.5, 19]; the statistical methods reach 7–16% with verification, and the differences are not significant. The chronicle includes only incidents covered by the media, and many of them are barely discussed in district communities in the first hours. Speed matters more: among events found by both Chronos-2 and a statistical method, the model never alarmed later, being earlier than CUSUM in 5 of 5 cases, earlier than SNB and STL in one case each, and simultaneous otherwise. In 3 of the 8 events found by the model the alarm preceded the media publication by 0.1–4.1 h: for example, queues at petrol stations on November 1 were discussed in the communities 4 h before the publication included in the chronicle. In a random sample of 150 alarm episodes, the share of episodes with a concrete cause was 57% [46, 67] for Chronos-2, 78% for SNB and 87% for CUSUM (labels checked by the authors, 18 of 150 corrected): the model fires more often on short bursts of sparse district series, some of which are caused by advertising and recurring columns.

**Table II.** Real events (67 event–series pairs), calibrated thresholds, %.

| Method | Alarm in window | Chance level | Content-verified | Before publication, events |
|---|---|---|---|---|
| Chronos-2 winsor | 40 | 20 | 12 | 3 |
| Chronos-2 none | 39 | 20 | 13 | 3 |
| SNB | 28 | 15 | 9 | 1 |
| Robust z | 27 | 13 | 12 | 2 |
| Seasonal z | 28 | 14 | 7 | 0 |
| STL | 33 | 16 | 16 | 3 |
| CUSUM | 36 | 16 | 15 | 1 |

*District assignment.* The LLM geoparser raised the share of messages with a district from 37.8% to 45.1%; most messages of city-wide communities contain no toponyms.

## VI. Discussion and Conclusions

The predictive distribution of a zero-shot TSFM serves as the threshold of a CFAR detector for sparse count series: with no per-series tuning it keeps the target false alarm rate on 95% of series whose intensity spans three orders of magnitude, detects bursts at least as often as the best statistical method, and earlier than all statistical methods. The price is a loss of sensitivity after a major event; context sanitization restores it only at the expense of a constant alarm rate, so the unsanitized mode should be the default and sanitization a high-sensitivity mode.

*Application.* For a situation center the detector yields a stream of district-referenced alarms with a known operator workload (at $\alpha = 1%$, about one alarm per series every four days) and needs no retuning when community activity grows or declines. Such alarms complement official feedback channels and media monitoring: they show where and when discussion departed from the norm, while reading the messages remains the operator's task.

*Transferability.* We did not test transfer across cities and platforms, but the pipeline has no parameters fitted to a series, city or platform. The detector uses a single parameter $\alpha$; the calibration month is needed only to compare methods. A new city requires a list of communities, a list of districts and a street gazetteer (e.g. from OpenStreetMap), which are inserted into the LLM instruction without training; LLMs resolve toponyms across regions without fine-tuning [15], and Chronos-2 shows zero-shot accuracy on series from many domains [7], [8]. Another platform only needs a message stream with publication times. Indirect evidence is the stability of the result over 41 series whose intensity differs by three orders of magnitude: to the detector each series is a new source with its own scale and seasonality.

*Limitations.* One city and one platform; power was measured on synthetic bursts of a fixed shape; the chronicle has 67 events in the evaluation window, and content verification used the top posts of each hour; the model context is 336 h. A second model of the same family, Chronos-1 (T5-small), retains the first-hour advantage (45.2% vs 43.7% for SNB, $p < 10^{-6}$) but falls behind SNB in overall detection probability (50.1% vs 52.9%) and keeps the alarm rate within the band on only 54% of series: the calibration of the upper quantile must be checked for each model. The pipeline is applicable in situation centers and urban monitoring systems as a tool for localizing events and confirming them early.

## References

[1] T. Sakaki, M. Okazaki, Y. Matsuo, "Earthquake shakes Twitter users: real-time event detection by social sensors," in Proc. WWW, 2010, pp. 851–860. ⟨K1⟩
[2] Q. Li et al., "Event detection from social media stream: methods, datasets and opportunities," arXiv:2306.16495, 2023. ⟨B2⟩
[3] C. Wardle, S. Dubberley, P. Brown, "Amateur footage: a global study of user-generated content in TV and online news output," Tow Center for Digital Journalism, 2014. ⟨P7⟩
[4] E. S. Page, "Continuous inspection schemes," Biometrika, vol. 41, 1954. ⟨B5⟩
[5] R. B. Cleveland et al., "STL: a seasonal-trend decomposition procedure based on Loess," J. Official Statistics, vol. 6, 1990. ⟨B6⟩
[6] M. A. Richards, Fundamentals of Radar Signal Processing, 2nd ed. McGraw-Hill, 2014. ⟨K6⟩
[7] A. F. Ansari et al., "Chronos: learning the language of time series," TMLR, 2024. ⟨S1⟩
[8] A. F. Ansari et al., "Chronos-2: from univariate to universal forecasting," arXiv:2510.15821, 2025. ⟨S2⟩
[9] T. Gneiting, F. Balabdaoui, A. E. Raftery, "Probabilistic forecasts, calibration and sharpness," JRSS B, vol. 69, 2007. ⟨K2⟩
[10] J. Kleinberg, "Bursty and hierarchical structure in streams," DMKD, vol. 7, 2003. ⟨B1⟩
[11] C. P. Farrington et al., "A statistical algorithm for the early detection of outbreaks of infectious disease," JRSS A, vol. 159, 1996. ⟨K7⟩
[12] M. Park, K. Yoon, "A comparative study of adaptation strategies for time series foundation models in anomaly detection," arXiv:2601.00446, 2026. ⟨A1⟩
[13] M. Uray, S. Messineo, R. Kwitt, S. Huber, "Exploring zero-shot foundation models for multivariate time series anomaly detection," arXiv:2607.12454, 2026. ⟨A2⟩
[14] N. Martinez Gil et al., "Adaptive conformal anomaly detection with time series foundation models for signal monitoring," in Proc. International Conference on Learning Representations (ICLR), 2026. ⟨A11⟩
[15] X. Hu, J. Kersten, F. Klan, and S. M. Farzana, "Toponym resolution leveraging lightweight and open-source large language models and geo-knowledge," International Journal of Geographical Information Science, vol. 40, no. 3, pp. 670–697, 2026, doi: 10.1080/13658816.2024.2405182. ⟨G1⟩
[16] L. A. Vidiasova et al., "Machine learning and NLP in assessing territorial differences in social well-being: a combined analysis of survey data and VKontakte digital traces," The Journal of Social Policy Studies, vol. 23, no. 4, pp. 725–750, 2025 (in Russian), doi: 10.17323/727-0634-2025-23-4-725-750. ⟨R1⟩
[17] O. Dovbysh, "New gatekeepers in town: how groups in social networking sites influence information flows in Russia's provinces," Social Media + Society, 2021. ⟨P1⟩
[18] Q. McNemar, "Note on the sampling error of the difference between correlated proportions or percentages," Psychometrika, vol. 12, 1947. ⟨K8⟩
