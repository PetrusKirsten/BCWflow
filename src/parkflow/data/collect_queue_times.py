from __future__ import annotations

from parkflow.data.queue_times import fetch_live_queue_times, flatten_queue_times, save_raw_queue_snapshot


def main() -> None:
    payload = fetch_live_queue_times()
    out_path = save_raw_queue_snapshot(payload)
    df = flatten_queue_times(payload)

    print(f"Saved raw queue snapshot: {out_path}")
    print(f"Rides collected: {len(df)}")
    if not df.empty:
        print(df[["ride_name", "is_open", "wait_time", "last_updated_utc"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
