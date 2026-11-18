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
| A2 | Uray M., Messineo S., Kwitt R., Huber S. Exploring Zero-Shot Foundation Models for Multivariate Time Series Anomaly Detection. arXiv:2607.12454, 2026 (полный текст; расширенные тезисы — EUROCAST 2026, с. 265–266) | arXiv:2607.12454 | ✅ проверено автором | отрицательный результат TimesFM на SWaT (F1 0.48 против 0.83 у PCA); модель «слишком хорошо» следует за аномалией; пики ошибки на границах → полезно для change-point |
| A3 | Khan U., Capogrosso L. et al. ChronosAD. IEEE INDIN 2026 | arXiv:2606.01300 | ✅ abs | TSFM как экстрактор признаков + BiLSTM/attention, 11 бенчмарков, +4.7 % AUC |
| A4 | Lan T. et al. Towards Foundation Models for Zero-Shot TSAD: Relative Context Discrepancy (TimeRCD). 2025 | arXiv:2509.21190 | ✅ abs | специализированная zero-shot AD модель |
| A5 | Hassan A. et al. Forecast2Anomaly (F2A). 2025 | arXiv:2511.03149 | ✅ abs | anomaly prediction, дообучение TSFM |
| A6 | THEMIS: ... Foundation Model Embeddings for Anomaly Detection in Time Series. 2025 | arXiv:2510.03911 | ✅ (abs title) | эмбеддинги TSFM |
| A7 | Leveraging Intermediate Representations of TSFM for Anomaly Detection. 2025 | arXiv:2509.12650 | ✅ (abs title) | эмбеддинги TSFM |
| A8 | Karami M., Jalali M., Ghassemi F. A Comprehensive Forecasting-Based Framework for TSAD: Benchmarking on NAB. 2025 | arXiv:2510.11141 | ✅ abs | качество прогноза важнее метода порога (F1 0.62–0.69 между порогами, 0.34–0.69 между моделями); STL в препроцессинге |
| A9 | Time Series Foundational Models: Their Role in Anomaly Detection and Prediction. 2024 | arXiv:2412.19286 | 🔎 | ранняя оценка: zero-shot AD только у TimeGPT/FPT |
| A11 | Martinez Gil N., O'Donncha F., Gifford W.M., Zhou N., Patel D.C., Vaculin R. Adaptive Conformal Anomaly Detection with Time Series Foundation Models for Signal Monitoring. Proc. ICLR 2026 | arXiv:2604.20122 | ✅ проверено автором | **ближайшая работа**: конформная калибровка тревог над TSFM (Chronos-Bolt и др.), p-значение как доля ложных тревог; многомерный случай через независимые p-значения и метод Фишера; промышленные сенсоры, не счётные ряды |
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
| G1 | Hu X., Kersten J., Klan F., Farzana S.M. Toponym resolution leveraging lightweight and open-source large language models and geo-knowledge. IJGIS, 2026, vol. 40, no. 3, pp. 670–697 | doi 10.1080/13658816.2024.2405182 | ✅ проверено автором |
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
| R1 | Видясова Л.А. и др. Machine learning and NLP in assessing territorial differences in social well-being: a combined analysis of survey data and VKontakte digital traces // The Journal of Social Policy Studies (ЖИСП). 2025. Т. 23, № 4. С. 725–750. DOI 10.17323/727-0634-2025-23-4-725-750 | ✅ проверено автором |
| R2 | Филатова О.Г., Чугунов А.В. Развитие экосистемы электронного участия в России в начале 2020-х // ПОЛИТЭКС. 2022. Т. 18, № 2 | ⚠️ |
| R3 | Чугунов А.В., Кабанов Ю.А. ... ЖИСП 2021. Т. 19, № 1 | ⚠️ |
| R4 | Володенков С.В., Федорченко С.Н. ... Анализ и прогноз. 2019. № 2 | ⚠️ |
| R5 | Smetanin S. The Applications of Sentiment Analysis for Russian Language Texts. IEEE Access 2020 | ⚠️ (нужен только если тональность остаётся) |
| R6 | Rusnachenko N., Golubev A., Loukachevitch N. LLM in Targeted Sentiment Analysis for Russian. Lobachevskii J. Math 2024 | ⚠️ |

Поиск по русскоязычным публикациям о TSFM (ноябрь 2026) оригинальных статей не дал: только машинные переводы arXiv на alphaxiv. Для русской терминологии используем «фундаментальные модели временных рядов» (устоявшийся перевод в этих переводах), при первом употреблении с английским оригиналом и аббревиатурой TSFM.

## Сверка ноября 2026 (ключи K… используются в paper/ru)

Статус 🔎+ — метаданные совпадают в нескольких результатах поиска, первичная запись (Crossref, издатель) не открыта: прокси её не пропускает. Перед подачей автору сверить по doi.org или библиотеке.

| # | Источник | Идентификатор | Статус |
|---|---|---|---|
| K1 | Sakaki T., Okazaki M., Matsuo Y. Earthquake shakes Twitter users: real-time event detection by social sensors. Proc. WWW 2010, pp. 851–860 | doi 10.1145/1772690.1772777 | 🔎+ |
| K2 | Gneiting T., Balabdaoui F., Raftery A.E. Probabilistic forecasts, calibration and sharpness. JRSS B 69(2), 243–268, 2007 | doi 10.1111/j.1467-9868.2007.00587.x | 🔎+ |
| K3 | Czado C., Gneiting T., Held L. Predictive model assessment for count data. Biometrics 65(4), 1254–1261, 2009 | doi 10.1111/j.1541-0420.2009.01191.x | 🔎+ |
| K4 | Angelopoulos A.N., Bates S. A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification. 2021 | arXiv:2107.07511 | ✅ abs |
| K5 | Finn H.M., Johnson R.S. Adaptive detection mode with threshold control as a function of spatially sampled clutter-level estimates. RCA Review 29, 414–464, 1968 | — | 🔎+ (страницы расходятся: 414–464/465) |
| K6 | Richards M.A. Fundamentals of Radar Signal Processing, 2nd ed. McGraw-Hill, 2014 | ISBN 978-0-07-179832-7 | 🔎+ (проверить ISBN) |
| K7 | Farrington C.P., Andrews N.J., Beale A.D., Catchpole M.A. A statistical algorithm for the early detection of outbreaks of infectious disease. JRSS A 159(3), 547–563, 1996 | doi 10.2307/2983331 | 🔎+ (инициалы 3–4 авторов проверить) |
| K8 | McNemar Q. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12(2), 153–157, 1947 | doi 10.1007/BF02295996 | 🔎+ |
| K9 | Holm S. A simple sequentially rejective multiple test procedure. Scand. J. Statistics 6(2), 65–70, 1979 | JSTOR | 🔎+ |

Уточнения к записям выше по той же сверке:
- B1: DMKD 7(4), 373–397, 2003 — 🔎+. B5: Biometrika 41(1–2), 100–115, doi 10.1093/biomet/41.1-2.100 — 🔎+. B6: J. Official Statistics 6(1), 3–73 — 🔎+. B7: ASQC Quality Press, 1993, ISBN 0-87389-247-X — 🔎+.
- B3: точное название arXiv «Learning to Discover Key Moments in Social Media Streams» (Buntain, Lin, Golbeck); LABurst — имя метода. ✅ abs.
- M2: Tatbul, Lee, Zdonik, Alam, Gottschlich, NeurIPS 2018 — ✅ abs.
- A10: NeurIPS 2024 Datasets and Benchmarks Track, без arXiv-идентификатора — 🔎+.
- A11: полное название заканчивается «…for Signal Monitoring»; площадка — ICLR 2026 (проверено автором).
- G1: Hu X., Kersten J., Klan F., Farzana S.M., IJGIS 2024, pp. 1–28 (том не найден) — 🔎+. G4: Cafferata G. et al., 2026 — ✅ abs.

## Обоснование выбора платформы (ноябрь 2026)

Статусы как выше: 🔎+ — найдено поиском, первичный текст не открыт; 📄 — источник из ВКР, не перепроверен.

| Ключ | Источник | Что подтверждает | Статус |
|---|---|---|---|
| P1 | Dovbysh O. New Gatekeepers in Town: How Groups in Social Networking Sites Influence Information Flows in Russia's Provinces. Social Media + Society, 2021. doi:10.1177/20563051211013253 | городские паблики ВКонтакте — гиперлокальные медиа с влиянием на местный дискурс (28 интервью с владельцами и модераторами) | 🔎+ |
| P2 | Статья в Journalism, doi:10.1177/1464884920941966 (гиперлокальные медиа российской провинции) | сотрудничество редакций местных СМИ и владельцев пабликов | 🔎+, автор и название уточнить |
| P3 | ВЦИОМ. Социальные сети и мессенджеры: вовлечённость и предпочтения, 10.08.2023 | охват соцсетей, время в ВКонтакте | 📄 [19] ВКР |
| P4 | Mediascope (через РБК, 15.01.2025; 3dnews 2026) | месячный охват ВКонтакте и Telegram сопоставим; Telegram 90,6 млн в янв. 2025 | 📄/🔎+, только как контекст |
| P5 | Шмелева О.Ю., Каминченко Д.И. Социальные медиа как инструмент формирования политической картины мира… (Нижегородский регион), Изв. Саратовского ун-та | ВКонтакте — приоритетный источник городских новостей для нижегородской молодёжи | 📄 [3] ВКР, проверить формулировку |
| P6 | Сочи, Вестник МГУ. Журналистика, 2025, № 1 «Новые медиа в городской системе создания и распространения новостного контента» | сравнение ВКонтакте и Telegram на городском уровне (1 644 поста) | 🔎+ |
| R1 | Видясова и др., ЖИСП 2025 | районные сообщества ВКонтакте как источник территориальных данных | уже в списке |

Аргументы для статьи (не по охвату, а по устройству данных):
1. Районные и «подслушано»-сообщества — форма гиперлокальных медиа, которая сложилась именно в ВКонтакте [P1, P6]; у районов Нижнего Новгорода есть такие сообщества, у Telegram — в основном каналы СМИ и администраций.
2. В ВКонтакте стена сообщества открыта для комментариев с деревом ответов и точным временем; в Telegram комментарии к каналам необязательны и привязаны к отдельной группе обсуждения.
3. Публичный API отдаёт посты и комментарии сообществ ретроспективно, что позволяет собрать непрерывные часовые ряды за 8,5 месяца.
4. Национальный охват Telegram сопоставим с ВКонтакте или выше [P4], поэтому перенос на Telegram и Max — ограничение и направление дальнейшей работы, а не довод против выбора.

Опрос из ВКР (612 респондентов, 67,4 % называют ВКонтакте основным источником новостей о городе) можно цитировать, только если данные опроса реально существуют и описаны (анкета, даты, квоты); иначе не использовать.

## Пользовательский контент в новостях и переносимость (ноябрь 2026)

| Ключ | Источник | Что подтверждает | Статус |
|---|---|---|---|
| P7 | Wardle C., Dubberley S., Brown P. Amateur Footage: A Global Study of User-Generated Content in TV and Online News Output. Tow Center for Digital Journalism, Columbia University, 2014 | большинство из 40 изученных редакций используют пользовательский контент, крупные — почти ежедневно; особенно в срочных новостях | 🔎+ (towcenter.gitbooks.io, firstdraftnews.org) |
| P8 | Reuters Institute: How newsrooms use user-generated content (Tubman K., fellowship paper, 2019) | стандарты работы редакций с UGC | 🔎+, по желанию |
