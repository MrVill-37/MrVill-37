from decimal import Decimal

import pytest

from dex_arbitrage import ExchangeQuote, execute_trade, find_arbitrage_opportunity


class DummyWeb3:
    def __init__(self, connected: bool = True):
        self._connected = connected

    def is_connected(self):
        return self._connected


class NotConnectedWeb3(DummyWeb3):
    def __init__(self):
        super().__init__(connected=False)


def test_find_arbitrage_returns_best_buy_sell_and_net_profit():
    quotes = [
        ExchangeQuote("dex-a", Decimal("100"), fee_bps=30),
        ExchangeQuote("dex-b", Decimal("102"), fee_bps=30),
        ExchangeQuote("dex-c", Decimal("101"), fee_bps=5),
    ]

    opp = find_arbitrage_opportunity(
        quotes, trade_size_token0=Decimal("1"), gas_cost_in_token1=Decimal("0.1")
    )

    assert opp is not None
    assert opp.buy_exchange == "dex-a"
    assert opp.sell_exchange == "dex-b"
    assert opp.spread_pct == Decimal("0.02")
    assert opp.estimated_gross_profit == Decimal("2")
    assert opp.estimated_net_profit == Decimal("1.294")


def test_find_arbitrage_returns_none_when_no_spread():
    quotes = [
        ExchangeQuote("dex-a", Decimal("100"), fee_bps=30),
        ExchangeQuote("dex-b", Decimal("100"), fee_bps=30),
    ]
    assert find_arbitrage_opportunity(quotes, Decimal("2"), Decimal("0")) is None


def test_execute_trade_dry_run_validates_required_fields():
    tx = {
        "to": "0x1111111111111111111111111111111111111111",
        "data": "0x",
        "value": 0,
        "gas": 21000,
        "maxFeePerGas": 1,
        "maxPriorityFeePerGas": 1,
        "nonce": 1,
        "chainId": 1,
    }

    result = execute_trade(
        DummyWeb3(),
        tx,
        profit_recipient="0x2222222222222222222222222222222222222222",
        dry_run=True,
    )
    assert result.startswith("dry-run")
    assert "profit recipient" in result


def test_execute_trade_raises_when_not_connected():
    with pytest.raises(ConnectionError):
        execute_trade(
            NotConnectedWeb3(),
            {},
            profit_recipient="0x2222222222222222222222222222222222222222",
            dry_run=True,
        )


def test_execute_trade_rejects_invalid_profit_recipient():
    tx = {
        "to": "0x1111111111111111111111111111111111111111",
        "data": "0x",
        "value": 0,
        "gas": 21000,
        "maxFeePerGas": 1,
        "maxPriorityFeePerGas": 1,
        "nonce": 1,
        "chainId": 1,
    }

    with pytest.raises(ValueError):
        execute_trade(DummyWeb3(), tx, profit_recipient="not-an-address", dry_run=True)
