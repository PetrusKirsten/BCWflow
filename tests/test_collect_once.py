from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from parkflow.data import collect_once
from parkflow.data.operating_hours import OperatingHoursPolicy


def test_should_collect_now_respects_operating_hours():
    policy = OperatingHoursPolicy()
    outside_hours = datetime(2026, 5, 22, 8, 30, tzinfo=ZoneInfo(policy.timezone))

    with patch.object(collect_once, "now_local", return_value=outside_hours):
        assert collect_once.should_collect_now(force_outside_hours=False, policy=policy) is False


def test_should_collect_now_can_force_outside_hours():
    policy = OperatingHoursPolicy()
    outside_hours = datetime(2026, 5, 22, 8, 30, tzinfo=ZoneInfo(policy.timezone))

    with patch.object(collect_once, "now_local", return_value=outside_hours):
        assert collect_once.should_collect_now(force_outside_hours=True, policy=policy) is True
