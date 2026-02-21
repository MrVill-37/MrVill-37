#!/usr/bin/env python3
"""Airdrop Nexus (safe mode)

Offline-first CLI for consent-based wallet inventory management and sweep planning.
This tool intentionally does NOT sign or broadcast transactions.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SUPPORTED_NETWORKS = {"ethereum", "base", "arbitrum", "zksync", "bnb"}


class ValidationError(ValueError):
    """Raised when input fails safety checks."""


@dataclass(frozen=True)
class Asset:
    network: str
    kind: str  # eth | erc20 | nft
    token: str
    amount: Decimal


@dataclass(frozen=True)
class SweepAction:
    from_wallet: str
    to_vault: str
    network: str
    kind: str
    token: str
    amount: Decimal
    note: str


def is_valid_address(address: str) -> bool:
    return bool(ADDRESS_RE.match(address.strip()))


def normalize_address(address: str) -> str:
    address = address.strip()
    if not is_valid_address(address):
        raise ValidationError(f"Invalid EVM address: {address}")
    return address


def load_wallets(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)

    wallets: list[str] = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        wallets.append(normalize_address(line.split(",")[0]))

    deduped = sorted(set(wallets))
    if not deduped:
        raise ValidationError("No wallet addresses found.")
    return deduped


def load_inventory(path: Path) -> dict[str, list[Asset]]:
    payload = json.loads(path.read_text())
    out: dict[str, list[Asset]] = {}

    for wallet, assets in payload.items():
        nwallet = normalize_address(wallet)
        out[nwallet] = []
        for raw_asset in assets:
            network = raw_asset["network"].lower().strip()
            if network not in SUPPORTED_NETWORKS:
                raise ValidationError(f"Unsupported network: {network}")

            kind = raw_asset["kind"].lower().strip()
            if kind not in {"eth", "erc20", "nft"}:
                raise ValidationError(f"Unsupported asset type: {kind}")

            token = raw_asset["token"].strip()
            if kind in {"erc20", "nft"}:
                token = normalize_address(token)

            try:
                amount = Decimal(str(raw_asset["amount"]))
            except (InvalidOperation, KeyError) as exc:
                raise ValidationError(f"Invalid amount for {wallet}") from exc
            if amount < 0:
                raise ValidationError("Negative balances are not allowed")

            out[nwallet].append(Asset(network, kind, token, amount))
    return out


def parse_eligibility(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    rules = payload.get("rules", {})
    if not isinstance(rules, dict):
        raise ValidationError("Eligibility rules must be an object")
    return rules


def evaluate_eligibility(wallet: str, rules: dict[str, Any]) -> dict[str, bool]:
    # Offline-only placeholder: looks for explicit allowlists.
    allowlists = rules.get("allowlists", {})
    result: dict[str, bool] = {}
    for campaign, campaign_wallets in allowlists.items():
        campaign_set = {normalize_address(w) for w in campaign_wallets}
        result[campaign] = wallet in campaign_set
    return result


def build_sweep_plan(
    wallet: str,
    vault: str,
    assets: list[Asset],
    gas_reserve_eth: Decimal,
) -> list[SweepAction]:
    wallet = normalize_address(wallet)
    vault = normalize_address(vault)
    if gas_reserve_eth < 0:
        raise ValidationError("Gas reserve must be non-negative")

    actions: list[SweepAction] = []
    for asset in assets:
        if asset.kind == "eth":
            sweep_amount = max(Decimal("0"), asset.amount - gas_reserve_eth)
            if sweep_amount > 0:
                actions.append(
                    SweepAction(
                        from_wallet=wallet,
                        to_vault=vault,
                        network=asset.network,
                        kind="eth",
                        token="ETH",
                        amount=sweep_amount,
                        note="subtracts configured gas reserve from wallet ETH",
                    )
                )
            continue

        if asset.amount == 0:
            continue

        note = "plan only - requires explicit owner consent + hardware-signing workflow"
        actions.append(
            SweepAction(wallet, vault, asset.network, asset.kind, asset.token, asset.amount, note)
        )

    return actions


def cmd_import(args: argparse.Namespace) -> int:
    wallets = load_wallets(Path(args.file))
    print(json.dumps({"wallet_count": len(wallets), "wallets": wallets}, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    wallets = load_wallets(Path(args.wallets))
    rules = parse_eligibility(Path(args.rules))
    result = {wallet: evaluate_eligibility(wallet, rules) for wallet in wallets}
    print(json.dumps(result, indent=2))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    inventory = load_inventory(Path(args.inventory))
    gas_reserve_eth = Decimal(str(args.gas_reserve_eth))

    plan: dict[str, list[dict[str, str]]] = {}
    for wallet, assets in inventory.items():
        actions = build_sweep_plan(wallet, args.vault, assets, gas_reserve_eth)
        plan[wallet] = [
            {
                "network": a.network,
                "kind": a.kind,
                "token": a.token,
                "amount": str(a.amount),
                "note": a.note,
            }
            for a in actions
        ]

    print(json.dumps(plan, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Airdrop Nexus (safe mode): offline wallet import, eligibility checks, and sweep planning"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import-wallets", help="Import and validate wallet address list")
    p_import.add_argument("--file", required=True, help="Path to wallet list (one address per line)")
    p_import.set_defaults(func=cmd_import)

    p_check = sub.add_parser("check-eligibility", help="Evaluate wallets against local eligibility rules")
    p_check.add_argument("--wallets", required=True, help="Path to wallet list")
    p_check.add_argument("--rules", required=True, help="Path to local eligibility JSON")
    p_check.set_defaults(func=cmd_check)

    p_plan = sub.add_parser("plan-sweep", help="Create a consent-based, non-broadcast sweep plan")
    p_plan.add_argument("--inventory", required=True, help="Path to local asset inventory JSON")
    p_plan.add_argument("--vault", required=True, help="Vault address")
    p_plan.add_argument("--gas-reserve-eth", type=Decimal, default=Decimal("0.003"))
    p_plan.set_defaults(func=cmd_plan)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
