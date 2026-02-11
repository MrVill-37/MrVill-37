from decimal import Decimal

import pytest

from airdrop_nexus import (
    Asset,
    ValidationError,
    build_sweep_plan,
    evaluate_eligibility,
    normalize_address,
)


def test_normalize_address_accepts_valid_address():
    address = "0x1111111111111111111111111111111111111111"
    assert normalize_address(address) == address


def test_normalize_address_rejects_invalid_address():
    with pytest.raises(ValidationError):
        normalize_address("0xabc")


def test_evaluate_eligibility_allowlist():
    wallet = "0x1111111111111111111111111111111111111111"
    rules = {
        "allowlists": {
            "campaign-a": [wallet],
            "campaign-b": ["0x2222222222222222222222222222222222222222"],
        }
    }
    result = evaluate_eligibility(wallet, rules)
    assert result == {"campaign-a": True, "campaign-b": False}


def test_build_sweep_plan_subtracts_gas_from_eth():
    wallet = "0x1111111111111111111111111111111111111111"
    vault = "0x2222222222222222222222222222222222222222"
    assets = [
        Asset("ethereum", "eth", "ETH", Decimal("0.05")),
        Asset("ethereum", "erc20", "0x3333333333333333333333333333333333333333", Decimal("3")),
    ]
    plan = build_sweep_plan(wallet, vault, assets, Decimal("0.01"))

    assert len(plan) == 2
    assert plan[0].kind == "eth"
    assert plan[0].amount == Decimal("0.04")
    assert plan[1].kind == "erc20"


def test_build_sweep_plan_rejects_negative_gas_reserve():
    wallet = "0x1111111111111111111111111111111111111111"
    vault = "0x2222222222222222222222222222222222222222"
    assets = [Asset("ethereum", "eth", "ETH", Decimal("1"))]

    with pytest.raises(ValidationError):
        build_sweep_plan(wallet, vault, assets, Decimal("-0.01"))
