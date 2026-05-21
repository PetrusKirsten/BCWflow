from __future__ import annotations

import pandas as pd

from parkflow.config import PROCESSED_DIR


def make_modeling_dataset() -> pd.DataFrame:
    queue_path = PROCESSED_DIR / "queue_times.csv"
    weather_path = PROCESSED_DIR / "weather.csv"

    queue = pd.read_csv(queue_path, parse_dates=["last_updated_utc", "ingested_at_utc"])
    if not weather_path.exists():
        return queue

    weather = pd.read_csv(weather_path, parse_dates=["weather_datetime_local"])

    queue["weather_datetime_local"] = pd.to_datetime(queue["last_updated_local"]).dt.tz_localize(None).dt.floor("h")
    weather["weather_datetime_local"] = pd.to_datetime(weather["weather_datetime_local"]).dt.floor("h")

    df = queue.merge(weather, on="weather_datetime_local", how="left")
    return df


def main() -> None:
    df = make_modeling_dataset()
    out_path = PROCESSED_DIR / "modeling_dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved modeling dataset: {out_path}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
