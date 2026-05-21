# Data sources

## Queue-Times live API

Used for row-level queue snapshots. This is the main analytical dataset for EDA and future modeling.

Output path:

```text
data/raw/queue_times/
data/processed/queue_times.csv
```

Attribution to display in the dashboard:

```text
Powered by Queue-Times.com
```

## Queue-Times public aggregate pages

Used for historical context only:

- all-time statistics;
- year-specific statistics;
- attendance history;
- day-level crowd calendar.

Output path:

```text
data/processed/historical_context/
```

These files should not be treated as row-level queue history.

## Open-Meteo historical weather

Used for weather enrichment. Weather variables are joined to queue snapshots by local date/hour.

Output path:

```text
data/raw/weather/
data/processed/weather.csv
```

## Locally generated calendar features

Generated from timestamps:

- local hour;
- day of week;
- weekend flag;
- month;
- time period.

## Ethical notes

- Use public sources respectfully and at low frequency.
- Preserve attribution.
- Do not publish raw third-party data if terms do not allow redistribution.
- Document uncertainty and limitations in the README/dashboard.
