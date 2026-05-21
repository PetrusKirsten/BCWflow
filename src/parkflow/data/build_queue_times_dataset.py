from __future__ import annotations

from pathlib import Path

import pandas as pd

from parkflow.config import PARK_TIMEZONE, PROCESSED_DIR, RAW_DIR
from parkflow.data.queue_times import flatten_raw_snapshot
from parkflow.features.calendar_features import add_time_features


def build_queue_times_dataset(raw_dir: Path = RAW_DIR / "queue_times") -> pd.DataFrame:
    files = sorted(raw_dir.glob("park_id=*/**/*.json"))
    frames = []

    for file in files:
        df = flatten_raw_snapshot(file)
        if not df.empty:
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.drop_duplicates(
        subset=["park_id", "ride_id", "last_updated_utc", "ingested_at_utc"], keep="last"
    )
    df_all = add_time_features(df_all, timestamp_col="last_updated_utc", timezone=PARK_TIMEZONE)
    return df_all


def main() -> None:
    df = build_queue_times_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "queue_times.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved processed queue dataset: {out_path}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
