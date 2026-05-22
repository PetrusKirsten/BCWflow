# GitHub Actions Scheduled Collection

This document explains the first cloud-based collection workflow for BCWflow.

## What this workflow does

The workflow in `.github/workflows/collect_queue_times.yml` runs the cloud-safe one-shot collector:

```bash
python -m parkflow.data.collect_once
```

It is designed to collect one Queue-Times snapshot and exit.

## Trigger modes

The workflow can run in two ways.

### Manual trigger

Use the GitHub UI:

```text
Actions -> Collect queue-time snapshot -> Run workflow
```

Manual inputs:

- `force_outside_hours`: collect even outside the nominal operating-hours window;
- `rebuild_processed`: rebuild `data/processed/queue_times.csv` after collecting.

### Scheduled trigger

The workflow is scheduled with UTC cron:

```yaml
- cron: "7,22,37,52 13-23 * * *"
```

This roughly targets the Beto Carrero World operating window in `America/Sao_Paulo` while avoiding the exact `00` minute.

The collector still checks the operating-hours policy. If GitHub runs it outside the nominal window, it skips safely.

## Where collected data goes

This first workflow does not commit data back to the repository.

Instead, it uploads files as GitHub Actions artifacts:

- raw snapshots from `data/raw/queue_times/`;
- `data/processed/queue_times.csv`, when generated.

Artifacts are kept for 14 days.

This is intentional. GitHub should not become the long-term data warehouse.

## Limitations

This workflow is a first automation milestone, not the final data platform.

Important limitations:

- GitHub scheduled workflows may be delayed.
- GitHub scheduled workflows can be disabled after long repository inactivity.
- Artifacts expire.
- Artifacts are not ideal for long-term analytics storage.
- The dashboard does not read from artifacts automatically.

## Future direction

The next stronger architecture should persist snapshots to a database, likely Postgres/Supabase.

Planned next steps:

1. create a remote Postgres/Supabase database;
2. add database credentials as GitHub Actions secrets;
3. implement a Postgres storage backend;
4. make the scheduled workflow write directly to the database;
5. update the dashboard/data pipeline to read from the remote source or exported processed dataset.

## Recommended validation

After this workflow is merged:

1. go to the repository Actions tab;
2. run the workflow manually with `force_outside_hours=true`;
3. confirm the workflow completes;
4. download the raw snapshot artifact;
5. inspect whether the snapshot has the expected Queue-Times JSON layout.
