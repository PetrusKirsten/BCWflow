# Storage Plan

This document describes the storage direction for BCWflow / ParkFlow Analytics.

## Current state

The project currently stores queue-time data as local files:

- raw Queue-Times payloads under `data/raw/queue_times/`;
- processed tabular datasets under `data/processed/`.

This is a good development setup because it is simple, inspectable and easy to version locally.

## Why add a storage layer?

The next project milestone is scheduled cloud collection. Cloud jobs should not depend on a personal computer or on long-running local loops.

A storage layer helps because it separates two responsibilities:

1. collecting a queue-time snapshot;
2. deciding where that snapshot is persisted.

The one-shot collector can keep the same interface while the backend evolves from local files to Postgres/Supabase.

## Current implementation

The first storage implementation is local-only:

```python
from parkflow.data.storage import LocalQueueSnapshotStorage
```

It preserves the current file layout and returns metadata about what was saved.

The one-shot collector now delegates persistence to this layer instead of writing files directly.

## Future Postgres/Supabase backend

A future PR can add a database-backed implementation, for example:

```text
PostgresQueueSnapshotStorage
```

Planned responsibilities:

- insert one row per attraction per snapshot;
- store ingestion metadata;
- avoid duplicate inserts when the same snapshot is retried;
- keep raw payload references or raw payload archive paths;
- support dashboard reads from processed database views or exported files.

## What is not included yet

This milestone does not implement:

- database schema migrations;
- Supabase connection handling;
- GitHub Actions secrets;
- remote dashboard reads;
- alerting or monitoring.

Those should be added in focused follow-up PRs.
