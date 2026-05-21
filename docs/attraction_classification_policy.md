# Attraction classification policy

This project keeps all attractions returned by the source in the dataset, but it does not treat every attraction as a queue-pressure signal by default.

Some records may represent shows, photo spots, scheduled experiences, walkthroughs, restaurants, exhibits or other non-ride experiences. These can appear with `wait_time = 0`, which is not the same thing as a measured 0-minute ride queue.

## Default dashboard behavior

Queue-pressure charts default to:

1. open records only;
2. records with a reported `wait_time`;
3. excluding configured/keyword non-queue candidates;
4. excluding attractions that have only reported 0-minute wait values in the current sample.

This is a visualization policy, not a data deletion policy. Hidden records remain visible in Data Coverage and in audit expanders.

## Why zero-only attractions are hidden by default

Early in the project, the dataset may contain only a few snapshots. At this stage, a ride that has only shown `0` so far could be a valid ride with no line, but it could also be a non-queue experience. Hiding zero-only attractions reduces visual clutter and prevents bar charts/heatmaps from being dominated by low-information rows.

The Streamlit filters allow zero-only attractions to be included whenever the goal is auditing rather than pressure analysis.

## Configured non-queue candidates

The current configured list is stored in `src/parkflow/config.py` as `QUEUE_ANALYSIS_EXCLUDED_ATTRACTIONS`. The list should be treated as editable project metadata. If future data shows that a listed attraction should be modeled as a regular queue-time ride, remove it from that list and document the reason.

## Interpretation rule

Do not write that an attraction has "no queue" just because it has `wait_time = 0`. Use wording such as:

- "reported 0-minute wait in the collected snapshots";
- "not included in queue-pressure charts by default";
- "likely non-queue/scheduled experience" when the configured rule supports that interpretation.
