from __future__ import annotations

import json

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from parkflow.config import PROCESSED_DIR, PROJECT_ROOT


def evaluate_group_mean_baseline(df: pd.DataFrame) -> dict[str, float]:
    """Baseline: predict wait time using average wait by ride and hour from train set."""
    model_df = df.dropna(subset=["wait_time", "ride_name", "hour"]).copy()
    train, test = train_test_split(model_df, test_size=0.25, random_state=42)

    global_mean = train["wait_time"].mean()
    group_means = train.groupby(["ride_name", "hour"])["wait_time"].mean()

    preds = []
    for _, row in test.iterrows():
        preds.append(group_means.get((row["ride_name"], row["hour"]), global_mean))

    metrics = {
        "mae": mean_absolute_error(test["wait_time"], preds),
        "rmse": mean_squared_error(test["wait_time"], preds) ** 0.5,
        "r2": r2_score(test["wait_time"], preds),
        "n_train": int(len(train)),
        "n_test": int(len(test)),
    }
    return metrics


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / "modeling_dataset.csv")
    metrics = evaluate_group_mean_baseline(df)

    out_dir = PROJECT_ROOT / "reports" / "model_metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "baseline_metrics.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
