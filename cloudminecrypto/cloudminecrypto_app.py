#!/usr/bin/env python3
"""CloudMineCrypto app simulator.

Educational, app-style CLI that explains self-mining tradeoffs and estimates
reward points for CloudMineCrypto plan tiers.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class Plan:
    name: str
    monthly_price_usd: Decimal
    reward_rate_multiplier: Decimal
    support_level: str
    has_analytics: bool


SELF_MINING_PAIN_POINTS = [
    "High upfront hardware cost (ASICs, power supplies, cables)",
    "Electricity and cooling requirements",
    "Heat, noise, and space constraints",
    "Ongoing maintenance and operational complexity",
]

PLANS: dict[str, Plan] = {
    "free": Plan(
        name="free",
        monthly_price_usd=Decimal("0"),
        reward_rate_multiplier=Decimal("1.0"),
        support_level="community",
        has_analytics=False,
    ),
    "starter": Plan(
        name="starter",
        monthly_price_usd=Decimal("9.99"),
        reward_rate_multiplier=Decimal("1.4"),
        support_level="priority-email",
        has_analytics=True,
    ),
    "pro": Plan(
        name="pro",
        monthly_price_usd=Decimal("24.99"),
        reward_rate_multiplier=Decimal("2.0"),
        support_level="concierge",
        has_analytics=True,
    ),
}

APP_NOTE = (
    "CloudMineCrypto does not give you ownership of mining hardware, and using "
    "the app does not mean you are operating a real Bitcoin mining rig. "
    "Rewards and rates can vary over time, and nothing shown in the app is a "
    "guarantee of future results."
)


class CloudMineError(ValueError):
    """Raised when invalid user input is detected."""


def _decimal(value: str, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except InvalidOperation as exc:
        raise CloudMineError(f"Invalid numeric value for {label}: {value}") from exc
    if out < 0:
        raise CloudMineError(f"{label} must be non-negative")
    return out


def get_plan(plan_name: str) -> Plan:
    key = plan_name.lower().strip()
    if key not in PLANS:
        valid = ", ".join(sorted(PLANS.keys()))
        raise CloudMineError(f"Unknown plan '{plan_name}'. Choose one of: {valid}")
    return PLANS[key]


def estimate_rewards(
    plan_name: str,
    activity_score: Decimal,
    market_variability: Decimal,
) -> dict[str, str]:
    """Estimate monthly reward points with variability stress.

    Formula intentionally simple and educational:
      base_points = 100 * activity_score
      adjusted = base_points * plan_multiplier * (1 - variability)
    """

    plan = get_plan(plan_name)
    if market_variability > Decimal("0.95"):
        raise CloudMineError("market_variability must be <= 0.95")

    base_points = Decimal("100") * activity_score
    adjusted = base_points * plan.reward_rate_multiplier * (Decimal("1") - market_variability)

    return {
        "plan": plan.name,
        "activity_score": str(activity_score),
        "market_variability": str(market_variability),
        "estimated_monthly_points": str(adjusted.quantize(Decimal("0.01"))),
        "disclaimer": APP_NOTE,
    }


def cmd_compare(_: argparse.Namespace) -> int:
    payload = {
        "self_mining_constraints": SELF_MINING_PAIN_POINTS,
        "cloudminecrypto_fit": {
            "summary": (
                "App-based Bitcoin rewards experience on mobile/desktop with "
                "free start, optional plans, progress tracking, and reward balance."
            ),
            "important_note": APP_NOTE,
        },
    }
    print(json.dumps(payload, indent=2))
    return 0


def cmd_plans(_: argparse.Namespace) -> int:
    payload = {name: asdict(plan) for name, plan in PLANS.items()}
    for name, plan_info in payload.items():
        plan_info["monthly_price_usd"] = str(plan_info["monthly_price_usd"])
        plan_info["reward_rate_multiplier"] = str(plan_info["reward_rate_multiplier"])
        plan_info["name"] = name
    print(json.dumps(payload, indent=2))
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    activity = _decimal(args.activity_score, "activity_score")
    variability = _decimal(args.market_variability, "market_variability")
    payload = estimate_rewards(args.plan, activity, variability)
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CloudMineCrypto app CLI: compare approaches, inspect plans, and estimate reward points"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_compare = sub.add_parser("compare", help="Show self-mining constraints and CloudMineCrypto positioning")
    p_compare.set_defaults(func=cmd_compare)

    p_plans = sub.add_parser("plans", help="List available plan definitions")
    p_plans.set_defaults(func=cmd_plans)

    p_estimate = sub.add_parser("estimate", help="Estimate monthly points for a selected plan")
    p_estimate.add_argument("--plan", required=True, help="Plan name: free | starter | pro")
    p_estimate.add_argument("--activity-score", required=True, help="User activity multiplier (e.g. 1.0)")
    p_estimate.add_argument(
        "--market-variability",
        default="0.15",
        help="Risk haircut [0..0.95] for changing reward/rate conditions",
    )
    p_estimate.set_defaults(func=cmd_estimate)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
