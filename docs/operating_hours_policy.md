# Operating-hours policy

ParkFlow keeps all collected snapshots in `data/raw/`, but queue-pressure analysis should not treat after-hours records as true zero-minute waits.

## Current rule

The project uses a conservative nominal park window:

```text
10:00-20:00 America/Sao_Paulo
```

Records collected outside this window are:

- preserved in the raw and processed datasets;
- visible in the Data Coverage page;
- excluded from queue-pressure charts by default.

This protects the analysis from a common artifact: when the park is closed, sources may still return attractions as closed or with 0-minute waits. Those records are useful for audit, but they should not be interpreted as visitor demand.

## Why nominal hours?

Specific operating hours may vary by date, event or season. For the first portfolio version, a stable nominal filter is safer than pretending we know the official schedule for every historical day.

The next improvement is to use the public crowd-calendar operating hours when available and fall back to nominal hours otherwise.

## Collector behavior

The continuous collector skips snapshots outside nominal hours by default.

Use this when building the main dataset:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30 --rebuild-after-each-run
```

Use this only for debugging/audit:

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30 --collect-outside-hours
```
