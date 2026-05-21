# 🎢 ParkFlow Analytics

**Queue time, visitor flow and weather intelligence for theme park operations.**

ParkFlow Analytics is an independent data science portfolio project inspired by a real visit to **Beto Carrero World**, in Penha/SC, Brazil. The goal is to transform a common visitor experience — queues, peak hours, crowded attractions and weather uncertainty — into a reproducible case study in operational intelligence.

> This project is not affiliated with, sponsored by, or endorsed by Beto Carrero World. Queue-time data is treated as public/proxy data and must be interpreted with care.

---

## 1. Why this project exists

Theme parks are rich operational systems. A visitor sees only the visible symptoms: long lines, closed rides, crowded shows, weather changes and uneven demand across attractions.

A data scientist can frame those symptoms as measurable questions:

- Which attractions concentrate the highest queue pressure?
- At what time of day do waits tend to peak?
- Which records are useful queue signals and which ones are shows/photo spots/non-queue experiences?
- How much data coverage do we actually have before making conclusions?
- Can weather and calendar features help explain or predict wait times?
- How can imperfect public data still support a transparent operational analysis?

The project is designed to show not only dashboards, but also **data acquisition, data quality, feature engineering, exploratory analysis, modeling readiness and documentation discipline**.

---

## 2. Project status

Current version: **EDA-ready MVP**

Already implemented:

- Live queue-time snapshot collection.
- Local historical dataset built from repeated snapshots.
- Data quality and coverage audit.
- Operating-hours guard to avoid treating after-hours records as real zero-minute waits.
- Attraction classification policy for shows, photo spots and non-queue experiences.
- Weather data integration.
- Exploratory dashboard in Streamlit.
- Historical aggregate context collector.

Next planned steps:

- Collect more snapshots over multiple days.
- Stabilize EDA insights.
- Add a simple baseline wait-time model.
- Compare baseline vs machine learning model.
- Add model interpretation and portfolio screenshots.

---

## 3. Data sources

| Layer | Source | Purpose | Notes |
|---|---|---|---|
| Queue snapshots | Queue-Times public API | Live wait-time records by attraction | Main row-level dataset; collected incrementally |
| Historical context | Queue-Times public stats/calendar pages | Aggregate context by ride, month, weekday and day | Not row-level queue history |
| Weather | Open-Meteo Historical Weather API | Temperature, precipitation and related variables | Joined by local date/hour |
| Calendar | Local feature engineering | Hour, day of week, weekend, seasonality | Can later include holidays/events |

Important interpretation rule:

> Row-level queue snapshots are the main dataset for EDA and modeling. Historical aggregate pages are useful context, but they are not treated as raw hourly wait-time observations.

---

## 4. Repository structure

```text
parkflow-analytics/
  data/
    raw/                  # raw snapshots and raw public context
    interim/              # optional intermediate datasets
    processed/            # processed analytical tables
  notebooks/
    01_data_audit.ipynb
    02_exploratory_analysis.ipynb
  src/parkflow/
    analysis/             # reusable EDA logic
    data/                 # collectors and dataset builders
    features/             # calendar/time features
    models/               # modeling scripts
    visualization/        # reusable Plotly figures
  dashboard/
    app.py
    pages/
  reports/
    figures/
    model_metrics/
  docs/
    collection_plan.md
    wait_time_policy.md
    operating_hours_policy.md
    historical_data_strategy.md
    attraction_classification_policy.md
```

---

## 5. Quick start

Create an environment and install the project:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

Collect one live queue-time snapshot:

```bash
python -m parkflow.data.collect_queue_times
```

Build the processed queue dataset:

```bash
python -m parkflow.data.build_queue_times_dataset
```

Audit the current dataset:

```bash
python -m parkflow.data.audit_processed_data
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```

---

## 6. Building local queue history

The project builds its strongest row-level dataset by collecting repeated live snapshots.

Recommended command:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30 --rebuild-after-each-run
```

For a short test run:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 15 --max-runs 3 --rebuild-after-each-run
```

The continuous collector skips snapshots outside the nominal park window by default:

```text
10:00-20:00 America/Sao_Paulo
```

This avoids a common analytical artifact: after the park closes, queue sources may return closed attractions or 0-minute waits, which should not be interpreted as real visitor demand.

For debugging only, outside-hours collection can be forced:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30 --collect-outside-hours
```

---

## 7. Collecting historical context

ParkFlow can also collect public aggregate historical context.

Example for current-year context:

```bash
python -m parkflow.data.historical_context --year 2026 --collect-calendar --start-date 2026-01-01 --end-date 2026-05-21
```

This attempts to collect:

- all-time aggregate Queue-Times statistics;
- selected-year aggregate Queue-Times statistics;
- attendance history;
- day-level crowd calendar with crowd level and operating hours.

These files are saved under:

```text
data/processed/historical_context/
```

They are used for context and documentation, not as substitutes for row-level queue snapshots.

---

## 8. Dashboard pages

The Streamlit dashboard currently contains:

### 📊 Data Coverage

Shows whether the dataset is ready for analysis:

- rows;
- snapshots;
- attractions;
- days covered;
- missing wait-time values;
- records collected outside nominal operating hours;
- wait-time reporting rate by attraction.

### 🎡 Attraction Explorer

Compares attraction-level queue pressure:

- mean wait;
- median wait;
- p90 wait;
- maximum wait;
- wait-time distribution;
- time series by attraction.

### 🔥 Operational Heatmap

Maps queue pressure by:

```text
attraction × local hour
```

The heatmap uses a semantic scale:

- green: lower wait;
- yellow/orange: moderate wait;
- red: higher wait.

### 🌦️ Weather Impact

Explores relationships between queue records and weather variables such as temperature and precipitation.

### 🗓️ Historical Context

Displays aggregate historical/context files collected from public pages.

---

## 9. Wait-time and attraction policies

Some attractions returned by public queue sources are not regular queue-based rides. They may be shows, scheduled presentations, photo spots or non-queue experiences.

ParkFlow therefore separates three cases:

1. **missing wait time** — no value was reported;
2. **reported zero wait** — source returned `0`;
3. **positive wait time** — source returned a value above zero.

A reported `0` is not automatically treated as a meaningful queue signal. Queue-pressure charts hide likely shows/photo/non-queue experiences and zero-only attractions by default, while keeping them visible in audit tables.

See:

- `docs/wait_time_policy.md`
- `docs/attraction_classification_policy.md`
- `docs/operating_hours_policy.md`

---

## 10. Modeling plan

The modeling layer should come after enough snapshot coverage has been collected.

Planned approach:

1. baseline model: historical mean by attraction/hour;
2. simple regression model;
3. tree-based model such as Random Forest;
4. comparison using MAE, RMSE and R²;
5. error analysis by attraction and hour.

The goal is not to build an artificially complex model. The goal is to build an interpretable forecasting workflow and document limitations clearly.

---

## 11. Ethics and limitations

This project is intentionally conservative about claims.

Limitations:

- Queue-time data is public/proxy data, not official attendance.
- Public sources may change structure, availability or terms.
- A small number of snapshots is useful for pipeline validation, not final conclusions.
- Weather correlations are exploratory and should not be interpreted as causal without stronger design.
- Historical aggregate context is not the same as row-level queue history.
- The project does not represent an official partnership with the park.

Data-use principles:

- keep attribution visible;
- avoid aggressive scraping;
- preserve raw data for audit;
- document assumptions;
- do not overclaim insights from limited coverage.

Queue-Times attribution:

> Powered by Queue-Times.com

---

## 12. Portfolio positioning

This project demonstrates:

- data engineering with public/proxy data;
- robust data cleaning and feature engineering;
- explicit data quality auditing;
- exploratory analysis and operational visualization;
- responsible treatment of missing/ambiguous records;
- dashboard development with Streamlit;
- a clear path toward predictive modeling.

The central portfolio message is:

> I transformed a real visitor experience into a reproducible operational intelligence case study using data science, visualization and careful documentation.
