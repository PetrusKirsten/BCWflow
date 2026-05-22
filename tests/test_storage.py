from __future__ import annotations

from parkflow.data.storage import LocalQueueSnapshotStorage, QueueSnapshotSaveResult


def test_local_queue_snapshot_storage_returns_save_result(monkeypatch, tmp_path):
    payload = {
        "lands": [
            {
                "id": 1,
                "name": "Test Land",
                "rides": [
                    {
                        "id": 10,
                        "name": "Test Ride",
                        "is_open": True,
                        "wait_time": 15,
                        "last_updated": "2026-05-22T12:00:00.000Z",
                    }
                ],
            }
        ]
    }
    expected_path = tmp_path / "snapshot.json"

    def fake_save_raw_queue_snapshot(payload, park_id):
        return expected_path

    monkeypatch.setattr(
        "parkflow.data.storage.save_raw_queue_snapshot",
        fake_save_raw_queue_snapshot,
    )

    result = LocalQueueSnapshotStorage().save_queue_snapshot(payload, park_id=319)

    assert isinstance(result, QueueSnapshotSaveResult)
    assert result.raw_snapshot_path == expected_path
    assert result.rows_collected == 1
    assert result.processed_dataset_path is None
