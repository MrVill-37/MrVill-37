import argparse
from pathlib import Path

from airdrop_nexus.claims import claim_airdrop
from airdrop_nexus.config import load_config
from airdrop_nexus.eligibility import check_eligibility
from airdrop_nexus.io_utils import load_wallets, save_wallets
from airdrop_nexus.networks import create_clients
from airdrop_nexus.sweep import sweep_erc20, sweep_erc721


def _resolve_config(path: str) -> Path:
    return Path(path).expanduser().resolve()


def cmd_import_wallets(args: argparse.Namespace) -> None:
    wallets = load_wallets(_resolve_config(args.input))
    save_wallets(_resolve_config(args.output), wallets)
    print(f"Imported {len(wallets)} wallets to {args.output}")


def cmd_check_eligibility(args: argparse.Namespace) -> None:
    config_path = _resolve_config(args.config)
    config = load_config(config_path)
    clients = create_clients(config.networks)
    wallets = load_wallets(_resolve_config(args.wallets))
    config_dir = config_path.parent

    network = args.network
    if network not in clients:
        raise ValueError(f"Unknown network {network}")

    for wallet in wallets:
        for airdrop in config.airdrops.get(network, []):
            result = check_eligibility(
                clients[network].web3,
                wallet,
                airdrop,
                config_dir,
            )
            print(
                f"{wallet.address} :: {result.airdrop_name} eligible={result.eligible}"
            )


def cmd_claim(args: argparse.Namespace) -> None:
    config_path = _resolve_config(args.config)
    config = load_config(config_path)
    clients = create_clients(config.networks)
    wallets = load_wallets(_resolve_config(args.wallets))
    config_dir = config_path.parent

    network = args.network
    if network not in clients:
        raise ValueError(f"Unknown network {network}")

    for wallet in wallets:
        for airdrop in config.airdrops.get(network, []):
            result = claim_airdrop(
                clients[network].web3,
                wallet,
                airdrop,
                config_dir,
            )
            print(f"{wallet.address} :: {result.airdrop_name} tx={result.tx_hash}")


def cmd_sweep(args: argparse.Namespace) -> None:
    config_path = _resolve_config(args.config)
    config = load_config(config_path)
    clients = create_clients(config.networks)
    wallets = load_wallets(_resolve_config(args.wallets))

    network = args.network
    if network not in clients:
        raise ValueError(f"Unknown network {network}")

    for wallet in wallets:
        if args.tokens:
            token_result = sweep_erc20(
                clients[network].web3,
                wallet,
                config.vault_address,
                config.tokens.get(network, []),
                dry_run=args.dry_run,
            )
            for message in token_result.submitted:
                print(f"{wallet.address} :: ERC20 {message}")
            for message in token_result.skipped:
                print(f"{wallet.address} :: ERC20 skipped {message}")

        if args.nfts:
            nft_result = sweep_erc721(
                clients[network].web3,
                wallet,
                config.vault_address,
                config.nfts.get(network, []),
                dry_run=args.dry_run,
            )
            for message in nft_result.submitted:
                print(f"{wallet.address} :: NFT {message}")
            for message in nft_result.skipped:
                print(f"{wallet.address} :: NFT skipped {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Airdrop Nexus - terminal-based airdrop manager and sweeper"
    )
    parser.add_argument(
        "--config",
        default="config/airdrop_nexus.json",
        help="Path to the Airdrop Nexus config file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import-wallets", help="Import wallets")
    import_parser.add_argument("--input", required=True, help="CSV or JSON input")
    import_parser.add_argument("--output", required=True, help="JSON output")
    import_parser.set_defaults(func=cmd_import_wallets)

    eligibility_parser = subparsers.add_parser(
        "check-eligibility", help="Check airdrop eligibility"
    )
    eligibility_parser.add_argument("--wallets", required=True, help="Wallets file")
    eligibility_parser.add_argument("--network", required=True, help="Network key")
    eligibility_parser.set_defaults(func=cmd_check_eligibility)

    claim_parser = subparsers.add_parser("claim", help="Claim configured airdrops")
    claim_parser.add_argument("--wallets", required=True, help="Wallets file")
    claim_parser.add_argument("--network", required=True, help="Network key")
    claim_parser.set_defaults(func=cmd_claim)

    sweep_parser = subparsers.add_parser(
        "sweep", help="Sweep ERC-20 tokens and NFTs"
    )
    sweep_parser.add_argument("--wallets", required=True, help="Wallets file")
    sweep_parser.add_argument("--network", required=True, help="Network key")
    sweep_parser.add_argument(
        "--tokens",
        action="store_true",
        help="Sweep ERC-20 tokens from config",
    )
    sweep_parser.add_argument(
        "--nfts",
        action="store_true",
        help="Sweep ERC-721 NFTs from config",
    )
    sweep_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build transactions without sending",
    )
    sweep_parser.set_defaults(func=cmd_sweep)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
