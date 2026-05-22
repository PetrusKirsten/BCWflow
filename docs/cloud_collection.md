# Cloud Collection Plan

This document describes the planned path for moving ParkFlow Analytics from local collection on a personal machine to scheduled cloud collection.

## Why cloud collection?

Local collection is useful during development, but it depends on a personal computer staying on and connected. For a stronger data project, queue-time snapshots should be collected by a scheduled job that runs independently.

The goal is to make collection:

- more consistent;
- easier to monitor;
- independent from a personal laptop;
- compatible with future database storage.

## Collector modes

The project has two collection modes.

### Local loop collector

```bash
python -m parkflow.data.run_queue_times_collector --interval-minutes 30 --rebuild-after-each-run
```

Use this during development or short manual collection sessions.

This command keeps running until it reaches `--max-runs` or until it is stopped manually.

### Cloud-safe one-shot collector

```bash
python -m parkflow.data.collect_once
```

Use this for scheduled cloud jobs.

This command:

1. checks the nominal park operating-hours policy;
2. collects exactly one queue-time snapshot when appropriate;
3. saves the raw snapshot;
4. optionally rebuilds the processed queue-time dataset;
5. exits.

Cloud jobs should usually collect once and exit instead of running an infinite loop. The scheduler is responsible for calling the job repeatedly.

## Operating-hours guard

By default, the one-shot collector skips collection outside the nominal park operating window. This prevents after-hours snapshots from being interpreted as real zero-minute queue pressure.

To force a collection for debugging:

```bash
python -m parkflow.data.collect_once --force-outside-hours
```

or:

```bash
python -m parkflow.data.collect_once --collect-outside-hours
```

## Recommended cloud architecture

The preferred future architecture is:

```text
Scheduler / Cron
        ↓
python -m parkflow.data.collect_once
        ↓
Raw snapshot storage
        ↓
Postgres / Supabase storage
        ↓
Processed dataset / dashboard
```

## GitHub Actions plan

A first cloud implementation can use GitHub Actions with a scheduled workflow.

Important notes:

- GitHub Actions cron schedules run in UTC.
- Scheduled jobs may be delayed during high-load periods.
- Jobs should avoid running at exactly minute `00` when possible.
- The workflow should call `python -m parkflow.data.collect_once`.
- The workflow should not run a long-lived loop.

Example future schedule for a 15-minute cadence during the approximate park operating window:

```yaml
on:
  schedule:
    - cron: "7,22,37,52 13-23 * * *"
```

This is only a draft and must be adjusted for the intended UTC/local-time mapping.

## Supabase / Postgres plan

GitHub Actions can run the collector, but GitHub should not be used as the main database. A better future storage target is Postgres, for example through Supabase.

Future storage goals:

- insert one row per attraction per snapshot;
- enforce idempotency where possible;
- track ingestion time and source metadata;
- keep raw payloads or payload references for auditability;
- expose processed data to the dashboard.

## What is intentionally not implemented yet

This milestone does not implement:

- Postgres writes;
- Supabase schema creation;
- GitHub Actions workflow;
- dashboard reads from a remote database;
- alerting or bot notifications.

Those should be added in later, focused PRs.
