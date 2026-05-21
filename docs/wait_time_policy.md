# Wait-time reporting policy

Some attractions may appear in the Queue-Times payload without a reported `wait_time` value. In this project, that is handled as a data semantics issue, not as an automatic error.

## Core rule

Missing wait-time values must stay missing.

Do **not** convert missing wait times to `0`, because a missing value does not necessarily mean a zero-minute queue. It can mean:

- the attraction is a show or scheduled experience;
- the attraction does not operate with a traditional queue;
- the source does not publish a queue value for that attraction;
- the attraction was closed or had unknown status at the snapshot time.

## Analysis behavior

Queue-pressure charts and metrics exclude records where `wait_time` is missing by default.

Coverage/audit views keep those records and show:

- wait-time reporting rate;
- records without wait time;
- attractions that never reported wait time in the current dataset;
- a conservative `mode_hint` for likely scheduled experiences.

## Interpretation

Attractions without reported wait time should be described as:

> attractions without queue-time reporting in the current source/sample

Avoid saying:

> attractions with zero wait

unless a real `wait_time = 0` value was reported by the source.
