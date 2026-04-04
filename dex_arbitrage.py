"""DEX arbitrage helpers (analysis + execution scaffolding).

This module provides:
- read-only market data fetchers for Uniswap V2-like pools,
- spread/profit estimation with fee + gas awareness,
- a guarded transaction-builder for future execution integration.

It intentionally defaults to *dry-run mode* and does not sign/broadcast
transactions unless explicitly requested by the caller.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from web3 import Web3


ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


@dataclass(frozen=True)
class ExchangeQuote:
    exchange_name: str
    price: Decimal
    fee_bps: int


@dataclass(frozen=True)
class ArbitrageOpportunity:
    buy_exchange: str
    sell_exchange: str
    buy_price: Decimal
    sell_price: Decimal
    spread_pct: Decimal
    estimated_gross_profit: Decimal
    estimated_net_profit: Decimal


def _normalize_address(address: str) -> str:
    normalized = address.strip()
    if not ADDRESS_RE.match(normalized):
        raise ValueError(f"Invalid EVM address: {address}")
    return normalized


def _to_decimal(value: int, decimals: int) -> Decimal:
    return Decimal(value) / (Decimal(10) ** Decimal(decimals))


def get_price(exchange_name: str, url: str) -> ExchangeQuote:
    """Fetch latest token price from a JSON-RPC endpoint.

    Parameters
    ----------
    exchange_name:
        Display name for the exchange/venue.
    url:
        JSON string payload with required fields:
          {
            "rpc_url": "https://...",
            "pair_address": "0x...",
            "pair_abi_path": "uniswap_v2_pair_abi.json",
            "token0_decimals": 18,
            "token1_decimals": 6,
            "fee_bps": 30
          }

    Returns
    -------
    ExchangeQuote with normalized token1/token0 price.
    """

    payload = json.loads(url)
    rpc_url = payload["rpc_url"]
    from web3 import Web3

    pair_address = Web3.to_checksum_address(payload["pair_address"])
    pair_abi_path = Path(payload["pair_abi_path"])
    token0_decimals = int(payload.get("token0_decimals", 18))
    token1_decimals = int(payload.get("token1_decimals", 18))
    fee_bps = int(payload.get("fee_bps", 30))

    if fee_bps < 0 or fee_bps > 10_000:
        raise ValueError(f"Invalid fee_bps: {fee_bps}")

    abi = json.loads(pair_abi_path.read_text())

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to RPC endpoint for {exchange_name}")

    pair = w3.eth.contract(address=pair_address, abi=abi)
    reserve0, reserve1, _ = pair.functions.getReserves().call()

    if reserve0 <= 0 or reserve1 <= 0:
        raise ValueError(f"Invalid reserves for {exchange_name}: {reserve0}, {reserve1}")

    normalized0 = _to_decimal(reserve0, token0_decimals)
    normalized1 = _to_decimal(reserve1, token1_decimals)
    price = normalized1 / normalized0

    return ExchangeQuote(exchange_name=exchange_name, price=price, fee_bps=fee_bps)


def find_arbitrage_opportunity(
    quotes: list[ExchangeQuote], trade_size_token0: Decimal, gas_cost_in_token1: Decimal
) -> ArbitrageOpportunity | None:
    """Compare prices across exchanges and estimate net profit.

    Gross model: (sell_price - buy_price) * trade_size.
    Net model: gross - venue fees (both legs) - gas cost.
    """

    if len(quotes) < 2:
        return None
    if trade_size_token0 <= 0:
        raise ValueError("trade_size_token0 must be > 0")
    if gas_cost_in_token1 < 0:
        raise ValueError("gas_cost_in_token1 must be >= 0")

    buy = min(quotes, key=lambda q: q.price)
    sell = max(quotes, key=lambda q: q.price)

    if sell.price <= buy.price:
        return None

    spread_pct = (sell.price - buy.price) / buy.price
    gross = (sell.price - buy.price) * trade_size_token0

    buy_fee = (buy.price * trade_size_token0) * (Decimal(buy.fee_bps) / Decimal(10_000))
    sell_fee = (sell.price * trade_size_token0) * (Decimal(sell.fee_bps) / Decimal(10_000))
    net = gross - buy_fee - sell_fee - gas_cost_in_token1

    return ArbitrageOpportunity(
        buy_exchange=buy.exchange_name,
        sell_exchange=sell.exchange_name,
        buy_price=buy.price,
        sell_price=sell.price,
        spread_pct=spread_pct,
        estimated_gross_profit=gross,
        estimated_net_profit=net,
    )


def execute_trade(
    w3: "Web3",
    tx: dict[str, Any],
    *,
    profit_recipient: str,
    private_key: str | None = None,
    dry_run: bool = True,
) -> str:
    """Execute atomic transaction using Web3.py (guarded).

    In dry-run mode this only validates and serializes intent.
    To broadcast, pass `dry_run=False` and a private key.

    Parameters
    ----------
    profit_recipient:
        Wallet that receives arbitrage gains. This must be encoded into the
        router/arb contract call data by upstream builder logic.
    """

    if not w3.is_connected():
        raise ConnectionError("Web3 provider is not connected")

    _normalize_address(profit_recipient)

    required_fields = {"to", "data", "value", "gas", "maxFeePerGas", "maxPriorityFeePerGas", "nonce", "chainId"}
    missing = required_fields.difference(tx.keys())
    if missing:
        raise ValueError(f"Missing tx fields: {sorted(missing)}")

    if dry_run:
        return f"dry-run: transaction validated for profit recipient {profit_recipient} but not broadcast"

    if not private_key:
        raise ValueError("private_key is required when dry_run=False")

    signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()
