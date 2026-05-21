from __future__ import annotations

import argparse

from parkflow.config import PROCESSED_DIR
from parkflow.data.weather import fetch_hourly_weather


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect hourly weather from Open-Meteo.")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    args = parser.parse_args()

    df = fetch_hourly_weather(args.start_date, args.end_date)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "weather.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved weather dataset: {out_path}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
