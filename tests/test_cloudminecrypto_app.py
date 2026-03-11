from decimal import Decimal

import pytest

from cloudminecrypto_app import CloudMineError, estimate_rewards, get_plan


def test_get_plan_valid():
    plan = get_plan("starter")
    assert plan.name == "starter"


def test_get_plan_invalid():
    with pytest.raises(CloudMineError):
        get_plan("vip")


def test_estimate_rewards_output_has_disclaimer():
    out = estimate_rewards("pro", Decimal("1.2"), Decimal("0.2"))
    assert out["plan"] == "pro"
    assert Decimal(out["estimated_monthly_points"]) == Decimal("192.00")
    assert "does not give you ownership of mining hardware" in out["disclaimer"]


def test_estimate_rewards_rejects_extreme_variability():
    with pytest.raises(CloudMineError):
        estimate_rewards("free", Decimal("1.0"), Decimal("0.99"))
