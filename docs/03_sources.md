# Реестр источников (source ledger)

Правило для всех исполнителей: в статью попадают только источники из этого реестра со статусом «проверено». Источник со статусом «проверить» нельзя цитировать, пока кто-то не открыл первоисточник и не сверил авторов, год, название и идентификатор. Новые источники добавлять сюда с датой и тем, что именно проверено.

Статус: ✅ проверено в этой сессии по первоисточнику (arXiv abs/HTML, карточка модели) · 🔎 найдено поиском, первоисточник не открыт · ⚠️ из памяти, обязательно проверить.

## Фундаментальные модели временных рядов

| # | Источник | Идентификатор | Статус | Для чего |
|---|---|---|---|---|
| S1 | Ansari A.F. et al. Chronos: Learning the Language of Time Series. TMLR, 2024 | arXiv:2403.07815 | ✅ (abs) | базовая модель, токенизация |
| S2 | Ansari A.F., Shchur O., Küken J. et al. Chronos-2: From Univariate to Universal Forecasting. 2025 | arXiv:2510.15821 | ✅ abs + карточка HF | основная модель статьи: 120M, квантили 0.01–0.99 (21 уровень), контекст 8192, горизонт 1024, group attention, ковариаты, CPU, Apache-2.0 |
| S3 | Das A. et al. A decoder-only foundation model for time-series forecasting. ICML 2024 | arXiv:2310.10688 | ✅ (abs title) | TimesFM |
| S4 | TimesFM 2.5 (карточка google/timesfm-2.5-200m-pytorch) | HF card, Apache-2.0 | ✅ карточка | 200M, квантильная голова (continuous quantile head), max_context 1024/горизонт 256 в примере; README GitHub заявляет 16k контекст (🔎 не сверено) |
| S5 | Woo G. et al. Unified Training of Universal Time Series Forecasting Transformers (Moirai). ICML 2024 | arXiv:2402.02592 | ✅ (abs title) | Moirai 1.0 |
| S6 | Liu C. et al. Moirai 2.0: When Less Is More for Time Series Forecasting. 2025 | arXiv:2511.11698 | ✅ abs + карточка | decoder-only, квантили 0.1–0.9, лицензия CC-BY-NC-4.0 (только исследования) |
| S7 | Liu X. et al. Moirai-MoE. 2024 | arXiv:2410.10469 | 🔎 | упоминание |
| S8 | Goswami M. et al. MOMENT: A Family of Open Time-series Foundation Models. ICML 2024 | arXiv:2402.03885 | ✅ (abs title) | TSFM с задачей AD |
| S9 | Garza A., Mergenthaler-Canseco M. TimeGPT-1. 2023 | arXiv:2310.03589 | ✅ (abs title) | закрытая TSFM с AD |
| S10 | Aksu T. et al. GIFT-Eval: A Benchmark for General Time Series Forecasting Model Evaluation. 2024 | arXiv:2410.10393 | ✅ (abs title) | бенчмарк |
| S11 | Foundation models for time series: a survey. 2025 | arXiv:2504.04011 | 🔎 | обзор |

## TSFM и обнаружение аномалий

| # | Источник | Идентификатор | Статус | Ключевой факт |
|---|---|---|---|---|
| A1 | Park M., Yoon K. A Comparative Study of Adaptation Strategies for Time Series Foundation Models in Anomaly Detection. 2026 | arXiv:2601.00446 (1 Jan 2026) | ✅ abs + HTML | zero-shot: ошибки прогноза (MSE) как anomaly score; TSB-AD-U (23 датасета); Chronos-Bolt лучшие по AUC-PR/VUS-PR, Moirai по ROC; LSTMAD остаётся лучшим по AUC-ROC; PEFT (LoRA/OFT/HRA) ≥ full fine-tuning |
| A2 | Uray M., Messineo S., Kwitt R., Huber S. Exploring Zero-Shot Foundation Models for Multivariate Time Series Anomaly Detection. EUROCAST 2026 (LNCS) | arXiv:2607.12454 | ✅ abs | отрицательный результат TimesFM на SWaT (F1 0.48 против 0.83 у PCA); модель «слишком хорошо» следует за аномалией; пики ошибки на границах → полезно для change-point |
| A3 | Khan U., Capogrosso L. et al. ChronosAD. IEEE INDIN 2026 | arXiv:2606.01300 | ✅ abs | TSFM как экстрактор признаков + BiLSTM/attention, 11 бенчмарков, +4.7 % AUC |
| A4 | Lan T. et al. Towards Foundation Models for Zero-Shot TSAD: Relative Context Discrepancy (TimeRCD). 2025 | arXiv:2509.21190 | ✅ abs | специализированная zero-shot AD модель |
| A5 | Hassan A. et al. Forecast2Anomaly (F2A). 2025 | arXiv:2511.03149 | ✅ abs | anomaly prediction, дообучение TSFM |
| A6 | THEMIS: ... Foundation Model Embeddings for Anomaly Detection in Time Series. 2025 | arXiv:2510.03911 | ✅ (abs title) | эмбеддинги TSFM |
| A7 | Leveraging Intermediate Representations of TSFM for Anomaly Detection. 2025 | arXiv:2509.12650 | ✅ (abs title) | эмбеддинги TSFM |
| A8 | Karami M., Jalali M., Ghassemi F. A Comprehensive Forecasting-Based Framework for TSAD: Benchmarking on NAB. 2025 | arXiv:2510.11141 | ✅ abs | качество прогноза важнее метода порога (F1 0.62–0.69 между порогами, 0.34–0.69 между моделями); STL в препроцессинге |
| A9 | Time Series Foundational Models: Their Role in Anomaly Detection and Prediction. 2024 | arXiv:2412.19286 | 🔎 | ранняя оценка: zero-shot AD только у TimeGPT/FPT |
| A11 | Martinez Gil N., O'Donncha F., Gifford W.M., Zhou N., Patel D.C., Vaculin R. Adaptive Conformal Anomaly Detection with Time Series Foundation Models for Signal Monitoring. 2026 (по данным поиска, ICLR 2026; проверить площадку) | arXiv:2604.20122 | ✅ abs + HTML | **ближайшая работа**: конформная калибровка тревог над TSFM (Chronos-Bolt и др.), p-значение как доля ложных тревог; многомерный случай через независимые p-значения и метод Фишера; промышленные сенсоры, не счётные ряды |
| A10 | Liu Q., Paparrizos J. The Elephant in the Room: Towards a Reliable Time-Series Anomaly Detection Benchmark (TSB-AD). NeurIPS 2024 D&B | ⚠️ id не найден | ⚠️ | бенчмарк, на который опирается A1 |

## Метрики и оценка

| # | Источник | Идентификатор | Статус |
|---|---|---|---|
| M1 | Lavin A., Ahmad S. Evaluating Real-time Anomaly Detection Algorithms: the Numenta Anomaly Benchmark. ICMLA 2015 | arXiv:1510.03336 | ✅ (abs title) |
| M2 | Tatbul N. et al. Precision and Recall for Time Series. NeurIPS 2018 | arXiv:1803.03639 | 🔎 (критика NAB: магические числа, нет нижней границы) |
| M3 | SoftED: Metrics for Soft Evaluation of Time Series Event Detection. 2023 | arXiv:2304.00439 | ✅ (abs title) |
| M4 | A Problem-Oriented Taxonomy of Evaluation Metrics for TSAD. 2025 | arXiv:2511.18739 | ✅ (abs title) |
| M5 | Gritta M. et al. A Pragmatic Guide to Geoparsing Evaluation. 2018/2020 | arXiv:1810.12368 | 🔎 |

## Всплески и события в социальных медиа

| # | Источник | Идентификатор | Статус |
|---|---|---|---|
| B1 | Kleinberg J. Bursty and Hierarchical Structure in Streams. DMKD 2003 | doi 10.1023/A:1024940629314 | ⚠️ (из ВКР, не проверялось здесь) |
| B2 | Li Q. et al. Event Detection from Social Media Stream: Methods, Datasets and Opportunities. 2023 | arXiv:2306.16495 | ✅ (abs title) |
| B3 | Buntain C. et al. Learning to Discover Key Moments in Social Media Streams (LABurst). 2015 | arXiv:1508.00488 | 🔎 (явный параметр задержки, окно допуска) |
| B4 | Hochenbaum J., Vallis O., Kejariwal A. Automatic Anomaly Detection in the Cloud via Statistical Learning (S-H-ESD). 2017 | arXiv:1704.07706 | ✅ (abs title) |
| B5 | Page E.S. Continuous Inspection Schemes. Biometrika 1954 (CUSUM) | — | ⚠️ классика, проверить выходные данные |
| B6 | Cleveland R.B. et al. STL: A Seasonal-Trend Decomposition Procedure Based on Loess. J. Official Statistics 1990 | — | ⚠️ классика |
| B7 | Iglewicz B., Hoaglin D. How to Detect and Handle Outliers. ASQC 1993 (modified z-score, MAD) | — | ⚠️ |
| B8 | Chandola V., Banerjee A., Kumar V. Anomaly detection: a survey. ACM CSUR 2009 | — | ⚠️ (из ВКР) |

## Геопарсинг и LLM

| # | Источник | Идентификатор | Статус |
|---|---|---|---|
| G1 | Toponym resolution leveraging lightweight and open-source LLMs and geo-knowledge. IJGIS 2024 | doi 10.1080/13658816.2024.2405182 | 🔎 |
| G2 | Scalable Toponym Resolution with LLMs: Accuracy and Speed Optimizations. CEUR-WS Vol. 3969, paper 6 | ceur-ws.org/Vol-3969/paper6.pdf | 🔎 (0.90→0.93, 83 365 топонимов) |
| G3 | Towards efficient and accessible geoparsing of U.K. local media: a benchmark dataset and LLM-based approach. Computational Humanities Research (Cambridge) | — | 🔎 (разрешение до административного района) |
| G4 | Large Language Models for Geolocation Extraction in Humanitarian Crisis Response. 2026 | arXiv:2602.08872 | 🔎 |
| G5 | Manvi R. et al. GeoLLM: Extracting Geospatial Knowledge from LLMs. ICLR 2024 | arXiv:2310.06213 | 🔎 |
| G6 | Mapping Natural Disasters Using Social Media Posts (ISPRS 2026, Flan-T5 на твитах) | isprs-archives XLIX-B4-2026-637 | 🔎 |

## Разреженные/счётные ряды и TSFM

| # | Источник | Идентификатор | Статус |
|---|---|---|---|
| C1 | When Time-Series Foundation Models Work for Quick-Commerce Demand Forecasting. J. Industrial Distribution & Business, 2026 | koreascience JAKO202622236048788 | 🔎 (Chronos-Bolt недооценивает прерывистый спрос) |
| C2 | Foundation or Formula? Simulation-based comparison of TimesFM-3 and classical models. 2026 | arXiv:2610.00589 | 🔎 |
| C3 | How Good Are TSFMs for Pedestrian Crowd Count Forecasting? 2026 | arXiv:2609.16415 | 🔎 |
| C4 | Assessing the Operational Viability of Foundation Models for Time Series Forecasting. 2026 | arXiv:2605.24381 | 🔎 |
| C5 | Do TSFMs pay off for industrial monitoring? cost-aware study. 2026 | arXiv:2608.22968 | 🔎 |

## Российский контекст (из списка ВКР; библиографические данные взяты из ВКР, перепроверить перед сдачей)

| # | Источник | Статус |
|---|---|---|
| R1 | Видясова Л.А., Чижик А.В., Жеребцова Ю.С., Чокрлич К., Егоров М.Ю. Машинное обучение и NLP в оценке территориальных различий социального самочувствия: комбинированный анализ опросов и данных ВКонтакте // ЖИСП. 2025. Т. 23, № 4. С. 725–750. DOI 10.17323/727-0634-2025-23-4-725-750 | ⚠️ |
| R2 | Филатова О.Г., Чугунов А.В. Развитие экосистемы электронного участия в России в начале 2020-х // ПОЛИТЭКС. 2022. Т. 18, № 2 | ⚠️ |
| R3 | Чугунов А.В., Кабанов Ю.А. ... ЖИСП 2021. Т. 19, № 1 | ⚠️ |
| R4 | Володенков С.В., Федорченко С.Н. ... Анализ и прогноз. 2019. № 2 | ⚠️ |
| R5 | Smetanin S. The Applications of Sentiment Analysis for Russian Language Texts. IEEE Access 2020 | ⚠️ (нужен только если тональность остаётся) |
| R6 | Rusnachenko N., Golubev A., Loukachevitch N. LLM in Targeted Sentiment Analysis for Russian. Lobachevskii J. Math 2024 | ⚠️ |

Поиск по русскоязычным публикациям о TSFM (ноябрь 2026) оригинальных статей не дал: только машинные переводы arXiv на alphaxiv. Для русской терминологии используем «фундаментальные модели временных рядов» (устоявшийся перевод в этих переводах), при первом употреблении с английским оригиналом и аббревиатурой TSFM.
