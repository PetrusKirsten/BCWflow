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
