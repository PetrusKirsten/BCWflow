# Historical data strategy

The project separates historical information into two levels.

## 1. Row-level queue snapshots

These are the best data for EDA and modeling: one row per attraction per collection time.

For the public Queue-Times API, ParkFlow currently collects live snapshots and builds a local historical dataset over time. This is the main analytical dataset.

## 2. Historical aggregate context

Queue-Times also exposes public aggregate pages, such as yearly attraction averages, crowd levels by month/day/week and crowd-calendar day pages.

These are useful for context, but they are not equivalent to row-level queue snapshots. ParkFlow stores them separately under:

```text
data/processed/historical_context/
```

Recommended command for current-year context:

```bash
python -m parkflow.data.historical_context --year 2026 --collect-calendar --start-date 2026-01-01 --end-date 2026-05-21
```

This tries to collect:

- all-time aggregate stats;
- current-year aggregate stats;
- attendance history;
- day-level crowd calendar with crowd level and operating hours.


## What the historical command actually does

The historical command does **not** download a hidden row-level queue history. It reads public HTML pages and converts what can be parsed into small CSV files. This is why the source format is HTML, not JSON.

Recommended commands:

```bash
# Aggregate context: all-time stats, selected-year stats and attendance history
python -m parkflow.data.historical_context --year 2026

# Day-level context only: crowd level and operating hours by date
python -m parkflow.data.historical_context --calendar-only --start-date 2026-01-01 --end-date 2026-05-21

# Full context: aggregate pages + day-level calendar
python -m parkflow.data.historical_context --year 2026 --collect-calendar --start-date 2026-01-01 --end-date 2026-05-21
```

Expected outputs:

```text
data/raw/historical_context/*.html
data/processed/historical_context/*.csv
```

If a giant HTML page appears in the terminal, that is not useful output. It usually means a parser/warning/error exposed the raw webpage instead of the summary. The collector now wraps literal HTML safely, saves raw pages to disk, and prints only compact status messages.

## Interpretation

Use historical context to answer questions such as:

- Which attractions are historically more queue-intensive?
- Which months or weekdays tend to be busier?
- Which days of the current year were marked as quiet/busy/packed?
- What operating-hours metadata can help filter live snapshots?

Do not use these aggregate files as if they were raw hourly wait-time observations.
