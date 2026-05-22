# ParkFlow Analytics v1.0 Scope

This document defines what it means for the first portfolio-ready version of ParkFlow Analytics to be complete.

The goal of v1.0 is not to be a perfect theme-park operations platform. The goal is to publish a clear, reproducible and well-documented data science case study built from public/proxy data.

## v1.0 goal

ParkFlow Analytics v1.0 should demonstrate how queue-time snapshots, weather data and calendar features can be transformed into an operational intelligence dashboard for a theme park visitor-experience problem.

The version should communicate three things clearly:

1. a real-world problem was observed and translated into analytical questions;
2. imperfect public/proxy data was collected, cleaned and documented responsibly;
3. exploratory analysis and visualization can support operational reasoning.

## Included in v1.0

### Data collection

- Queue-time snapshots from Queue-Times public data sources.
- Weather data from a public weather API.
- Calendar-derived features such as hour, day of week, month and weekend flag.
- Nominal operating-hour filtering to avoid treating after-hours records as real zero-minute queue pressure.
- Explicit handling of attractions that do not behave like regular queue-based rides.

### Data processing

- Raw snapshots preserved under `data/raw/`.
- Processed tabular files under `data/processed/`.
- A documented distinction between:
  - positive queue-time records;
  - zero-minute records;
  - missing wait-time records;
  - off-hours records;
  - likely non-queue experiences.

### Exploratory analysis

- Data coverage overview.
- Attraction-level queue-time summary.
- Rankings by mean, median and p90 wait time.
- Operational heatmap by attraction and hour.
- Weather-impact exploration, clearly framed as exploratory rather than causal.

### Dashboard

The Streamlit dashboard should include at least:

1. Data Coverage
2. Attraction Explorer
3. Operational Heatmap
4. Weather Impact
5. Historical Context, when aggregate context files are available

### Documentation

- A strong README suitable for a GitHub portfolio project.
- Data-source documentation.
- Ethics and limitations.
- Operating-hours policy.
- Attraction classification / wait-time interpretation policy.
- Cloud collection plan.

## Out of scope for v1.0

The following items are intentionally postponed:

- Production-grade data warehouse design.
- Full NLP pipeline for visitor reviews.
- Automated scraping of review platforms without clear permission.
- Claims based on official park attendance or internal operations data.
- Complex ML models such as XGBoost or LightGBM as primary results.
- Real-time public production deployment with uptime guarantees.
- A FastAPI service layer.

## Minimum data coverage criteria

A portfolio-ready v1.0 should ideally include:

- at least 7 days of in-hours queue-time snapshots;
- preferably 14+ days for stronger analysis;
- at least one weekend;
- multiple snapshots per operating day;
- clear reporting of gaps and collection limitations.

The project can be published earlier as an in-progress case study, but the README should label the results as preliminary.

## ML criteria for v1.0

Machine learning is optional for v1.0.

If included, it should be deliberately simple and transparent:

- baseline model: historical mean or median by attraction/hour;
- first supervised model: linear regression, random forest or another interpretable baseline;
- metric: MAE as the main business-facing metric;
- clear warning that the model is experimental and data-limited.

A weak but honest baseline is preferable to an over-engineered model trained on insufficient data.

## v1.0 completion checklist

- [ ] Queue-time collection runs reliably.
- [ ] Off-hours records are excluded from queue-pressure charts by default.
- [ ] Non-queue attractions are handled transparently.
- [ ] Weather data is joined to queue-time observations.
- [ ] Dashboard pages run without errors.
- [ ] Data Coverage page explains the dataset limitations.
- [ ] README tells the project story clearly.
- [ ] Limitations and ethics are documented.
- [ ] At least 3 initial insights are written from the collected data.
- [ ] The repository can be installed and run from a clean environment.

## Definition of done

ParkFlow Analytics v1.0 is done when a reviewer can open the repository, understand the motivation, reproduce the data-processing workflow, run the dashboard, inspect the limitations and see meaningful initial insights without needing private data or manual context from the author.
