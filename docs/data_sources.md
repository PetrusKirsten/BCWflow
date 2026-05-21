# Data sources

## Queue-Times

Use cases:

1. Live queue-time snapshots by park.
2. Public aggregated statistics and crowd calendar pages as context.

Important notes:

- Live API timestamps are in UTC.
- The free live API requires visible attribution: `Powered by Queue-Times.com`.
- Detailed historical wait-time access may not be available through the public real-time endpoint. Treat granular history as something to validate before automating.

## Open-Meteo

Use case:

- Hourly historical weather data for Penha, Santa Catarina, Brazil.

Suggested variables:

- temperature_2m
- precipitation
- relative_humidity_2m
- wind_speed_10m
- weather_code

## Calendar features

Generated locally from timestamps:

- date
- hour
- day_of_week
- month
- is_weekend
- time_period

Holidays can be added via a public Brazilian holidays API in a later iteration.
