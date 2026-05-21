# Exploratory Analysis Plan

This project uses EDA as a bridge between the raw public/proxy data pipeline and the final portfolio narrative.

## Current EDA questions

1. Which attractions show the highest queue pressure in the collected sample?
2. Which local hours appear more critical?
3. How does queue pressure vary across attraction and hour?
4. Are weather variables already linked and ready for exploratory comparisons?
5. How much coverage is needed before writing stronger conclusions?

## Minimum coverage before stronger claims

The dashboard and notebook work with a few snapshots, but conclusions should stay conservative until the dataset contains:

- multiple days of snapshots;
- at least one weekend day;
- several park operating hours;
- repeated observations for the same attraction-hour combinations;
- weather records linked to the same queue-time period.

## Interpretation rules

- Treat queue times as proxy data, not official attendance.
- Prioritize median and p90 over mean alone.
- Report sample size for every ranking or comparison.
- Avoid causal language when discussing weather.
- Label early charts as exploratory while data coverage is small.
