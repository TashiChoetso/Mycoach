from __future__ import annotations

from app.scoring.momentum import clamp_score, score_area, score_focus, score_momentum


def test_weights_sum_to_one():
    from app.scoring.weights import DEFAULT_WEIGHTS

    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9
    assert "finance" in DEFAULT_WEIGHTS


def test_check_and_count_scores():
    assert score_focus(kind="check", target_value=None, log_status=None, log_value=None) == 0
    assert score_focus(kind="check", target_value=None, log_status="completed", log_value=None) == 100
    assert score_focus(kind="check", target_value=None, log_status="skipped", log_value=None) is None
    assert score_focus(kind="count", target_value=8, log_status="completed", log_value=4) == 50
    assert score_focus(kind="count", target_value=8, log_status="completed", log_value=10) == 100


def test_area_and_momentum_skip_rest():
    assert score_area([None, None]) is None
    assert score_area([100, 0]) == 50
    assert score_momentum([50, 100], seven_day_rate=0.8) == 79
    assert clamp_score(140) == 100
