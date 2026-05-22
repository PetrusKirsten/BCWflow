# Database Storage Setup

This document explains how to move BCWflow from artifact-only collection to persistent database collection.

## Why this matters

GitHub Actions artifacts are useful for testing automation, but they expire and are not a durable analytics database.

For collection that can run while a personal computer is turned off, the recommended setup is:

```text
GitHub Actions
        ↓
python -m parkflow.data.collect_once --storage-backend auto
        ↓
PostgreSQL-compatible database
        ↓
future dashboard / processed export
```

## Current implementation

The project now includes:

```text
src/parkflow/data/db_storage.py
```

It adds:

- database URL loading from `DATABASE_URL`;
- URL normalization for `postgres://` and `postgresql://` schemes;
- automatic schema creation for queue-time snapshots;
- one row per attraction observation;
- idempotent inserts based on snapshot id and ride id.

The one-shot collector now supports:

```bash
python -m parkflow.data.collect_once --storage-backend auto
python -m parkflow.data.collect_once --storage-backend local
python -m parkflow.data.collect_once --storage-backend database
```

Behavior:

- `local`: always saves to local files;
- `database`: requires `DATABASE_URL` and writes to the database;
- `auto`: writes to the database when `DATABASE_URL` exists, otherwise falls back to local files.

## Required environment variable

Set:

```text
DATABASE_URL=<your database connection string>
```

For GitHub Actions, add it as a repository secret:

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

Secret name:

```text
DATABASE_URL
```

Secret value: your database connection string.

## Tables created automatically

The collector creates two tables if they do not exist:

```text
queue_time_snapshots
queue_time_observations
```

`queue_time_snapshots` stores one row per collection event, including raw payload JSON.

`queue_time_observations` stores one row per attraction/ride observation inside each snapshot.

## Manual local test

After setting `DATABASE_URL` locally:

```bash
python -m parkflow.data.collect_once --storage-backend database --force-outside-hours
```

Expected output:

```text
saved queue snapshot: db://queue_time_snapshots/...
rides collected: ...
```

## GitHub Actions note

The scheduled workflow must expose the repository secret to the collector as an environment variable named `DATABASE_URL`.

If the workflow does not pass the secret into the job environment, `--storage-backend auto` will fall back to local/artifact storage.

## When can the local PC be turned off?

The local collector can be stopped when all of these are true:

1. `DATABASE_URL` is configured as a GitHub Actions secret;
2. the workflow runs manually with `force_outside_hours=true`;
3. the log shows `saved queue snapshot: db://queue_time_snapshots/...`;
4. the database has new rows in `queue_time_snapshots` and `queue_time_observations`;
5. at least two scheduled runs complete successfully.

After that, GitHub Actions + database storage can be treated as the official collector.
