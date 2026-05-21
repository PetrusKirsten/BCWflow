# Queue-time collection plan

The project starts with live queue-time snapshots and grows its own local historical dataset over time.

## Recommended cadence

Use a respectful interval between requests:

- Minimum recommended interval: 15 minutes
- Preferred interval: 30 minutes
- Avoid very frequent polling unless a source explicitly allows it

## First collection target

A useful first target is:

- 7 days of collection
- 15–30 minute intervals
- at least one weekend day
- at least one rainy or cloudy day if possible

This should be enough to make the first EDA more meaningful without overclaiming operational conclusions.

## Commands

Collect a single snapshot:

```bash
python -m parkflow.data.collect_queue_times
```

Run continuous collection:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30
```

Run a short test:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 15 --max-runs 3 --rebuild-after-each-run
```

Rebuild the processed queue dataset:

```bash
python -m parkflow.data.build_queue_times_dataset
```

Audit the processed dataset:

```bash
python -m parkflow.data.audit_processed_data
```

## Interpreting early data

With only a few snapshots, the project should focus on data coverage and pipeline quality rather than strong analytical conclusions.

Early dashboard claims should be phrased carefully:

- "In the collected snapshots..."
- "During the observed period..."
- "This is a proxy for attraction pressure, not official demand."

Avoid strong claims such as:

- "This attraction is always the most crowded."
- "Rain causes lower wait times."
- "This predicts real park attendance."

Those claims require broader, longer-term data coverage.
