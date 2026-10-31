from datetime import date

import pytest

from brewly import rules


def test_pause_accepts_max_weeks():
    out = rules.pause({"status": "active"}, 8, date(2024, 1, 1))
    assert out["status"] == "paused"
    assert out["paused_until"] == "2024-02-26"


@pytest.mark.parametrize("weeks", [0, 9])
def test_pause_rejects_out_of_range(weeks):
    with pytest.raises(rules.RuleError):
        rules.pause({}, weeks, date(2024, 1, 1))
