from parkflow.features.calendar_features import classify_time_period


def test_classify_time_period():
    assert classify_time_period(9) == "morning"
    assert classify_time_period(13) == "afternoon"
    assert classify_time_period(19) == "evening"
    assert classify_time_period(2) == "night"
