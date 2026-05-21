# ParkFlow Analytics

Queue time, visitor flow and weather intelligence for theme park operations.

This project turns a real theme park visit into a data science case study: how can public/proxy data help us understand queues, peak hours, attraction pressure, weather effects and operational bottlenecks?

> Case study: Beto Carrero World. This is an independent portfolio project and is not affiliated with, sponsored by, or endorsed by Beto Carrero World.

## Project goals

- Collect public/proxy queue-time data.
- Combine queue records with weather and calendar features.
- Explore operational patterns: attractions, hours, weekdays, weekends and weather.
- Build a simple, interpretable wait-time prediction model.
- Present the results in a narrative Streamlit dashboard.

## Data sources

Initial sources:

- Queue-Times public API for live wait times.
- Queue-Times public pages for aggregated crowd/statistical context.
- Open-Meteo Historical Weather API for weather variables.
- Calendar features generated locally; holidays can be added later.

## Repository structure

```text
parkflow-analytics/
  data/
    raw/
    interim/
    processed/
  notebooks/
  src/parkflow/
    data/
    features/
    visualization/
    models/
  dashboard/
  reports/
  docs/
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
```

Collect one live queue-time snapshot:

```bash
python -m parkflow.data.collect_queue_times
```

Collect aggregated historical context tables, when permitted:

```bash
python -m parkflow.data.historical_context
```

Build a processed snapshot table from all raw snapshots:

```bash
python -m parkflow.data.build_queue_times_dataset
```

Run the dashboard:

```bash
streamlit run dashboard/app.py
```


## Current workflow

The project now starts with a small but complete data pipeline:

1. collect live queue-time snapshots;
2. rebuild the processed queue dataset;
3. audit data coverage and quality;
4. enrich with weather data;
5. explore the dashboard.

Collect one live snapshot:

```bash
python -m parkflow.data.collect_queue_times
```

Build the processed queue table:

```bash
python -m parkflow.data.build_queue_times_dataset
```

Audit the current processed dataset:

```bash
python -m parkflow.data.audit_processed_data
```

Run a continuous collector to build your own local history:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30
```

For a short test run with three snapshots:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 15 --max-runs 3 --rebuild-after-each-run
```

A 15–30 minute interval is recommended to be respectful with public data sources. The raw snapshots are saved under `data/raw/queue_times/`, and the processed table is rebuilt into `data/processed/queue_times.csv`.

## Exploratory analysis v0

After collecting a few snapshots, build or refresh the processed datasets and open the first EDA layer:

```bash
python -m parkflow.data.build_queue_times_dataset
python -m parkflow.data.make_modeling_dataset
streamlit run dashboard/app.py
```

New dashboard pages:

- **Data Coverage** — validates snapshot volume, missing values and attraction coverage.
- **Attraction Explorer** — compares average, median, p90 and maximum waits by attraction.
- **Operational Heatmap** — maps attraction × local hour queue pressure.
- **Weather Impact** — checks whether weather variables are joined and ready for exploratory analysis.

The notebook `notebooks/02_exploratory_analysis.ipynb` mirrors the dashboard logic and should be used to write the first portfolio insights. With only a few snapshots, use the charts as pipeline validation rather than stable operational conclusions.

## Wait-time reporting policy

Some attractions may appear without a reported `wait_time`. The project now treats those values as missing/non-reported instead of converting them to zero. Queue-pressure charts exclude them by default, while the **Data Coverage** page keeps them visible through wait-time reporting metrics. See `docs/wait_time_policy.md` for the interpretation rules.

## Ethics and limitations

- Queue times are treated as proxy data, not official park attendance.
- Public pages and APIs must be used respectfully, with proper attribution.
- Raw data from third-party sources should not be redistributed if terms do not allow it.
- Any scraping-like collection must respect terms of use, robots.txt and rate limits.
- The project does not claim operational truth about the park; it demonstrates a reproducible analytical workflow.
- See `docs/collection_plan.md` for the recommended snapshot collection cadence and interpretation rules.

## Attribution

When using Queue-Times data in the app or dashboard, show the required attribution:

> Powered by Queue-Times.com


## Attraction classification policy

The project keeps all attractions returned by Queue-Times, but queue-pressure charts do not treat every record as a regular ride queue. Likely shows/photo spots/non-queue experiences and attractions that only report 0-minute waits in the current sample are hidden from pressure visuals by default. They remain available in Data Coverage and audit tables. See `docs/attraction_classification_policy.md` for details.
