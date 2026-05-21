from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import requests

from parkflow.config import OPEN_METEO_ARCHIVE_URL, PARK_LATITUDE, PARK_LONGITUDE, PARK_TIMEZONE

DEFAULT_HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]


def fetch_hourly_weather(
    start_date: str | date,
    end_date: str | date,
    latitude: float = PARK_LATITUDE,
    longitude: float = PARK_LONGITUDE,
    timezone: str = PARK_TIMEZONE,
    hourly_variables: Iterable[str] = DEFAULT_HOURLY_VARIABLES,
    timeout: int = 30,
) -> pd.DataFrame:
    """Fetch hourly historical weather from Open-Meteo Archive API."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "hourly": ",".join(hourly_variables),
        "timezone": timezone,
    }
    response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    hourly = payload.get("hourly", {})
    if not hourly:
        return pd.DataFrame()

    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"time": "weather_datetime_local"})
    df["latitude"] = payload.get("latitude")
    df["longitude"] = payload.get("longitude")
    df["timezone"] = payload.get("timezone")
    return df
