from __future__ import annotations

from parkflow.data.data_quality import (
    load_best_available_dataset,
    missingness_report,
    print_coverage_summary,
    ride_coverage_report,
)


def main() -> None:
    df, path = load_best_available_dataset()
    if path is None or df.empty:
        print("No processed data found. Run:")
        print("python -m parkflow.data.build_queue_times_dataset")
        return

    print(f"Loaded: {path}")
    print_coverage_summary(df)

    print("\nTop attractions by p90 wait time")
    ride_report = ride_coverage_report(df)
    if ride_report.empty:
        print("No ride-level coverage available.")
    else:
        display_cols = [
            col
            for col in [
                "ride_name",
                "rows",
                "snapshots",
                "days_seen",
                "open_rate",
                "avg_wait_min",
                "p90_wait_min",
                "max_wait_min",
            ]
            if col in ride_report.columns
        ]
        print(ride_report[display_cols].head(15).to_string(index=False))

    print("\nColumns with highest missingness")
    miss = missingness_report(df)
    print(miss.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
