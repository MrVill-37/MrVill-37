# Airdrop Nexus

Airdrop Nexus is a terminal-based, offline-capable airdrop management and asset sweeping toolkit. It focuses on importing wallet lists, checking airdrop eligibility, claiming tokens, and sweeping ERC-20 / ERC-721 assets into a vault address.

## Features

- Import wallet lists (CSV or JSON) into a normalized JSON format.
- Check eligibility for configured airdrops.
- Claim configured airdrops.
- Sweep ERC-20 tokens and ERC-721 NFTs to a vault address.
- Multi-network support (Ethereum, Base, Arbitrum, zkSync, BNB).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or use the helper script:

```bash
./scripts/create_virtualenv.sh
```

Edit the config at `config/airdrop_nexus.json` with your RPC URLs, token lists, NFT contracts, and airdrop ABIs.

### Import wallets

```bash
python -m airdrop_nexus.cli import-wallets --input wallets.csv --output wallets.json
```

CSV format example:

```csv
address,private_key
0xabc...,0xYOUR_PRIVATE_KEY
```

### Check eligibility

```bash
python -m airdrop_nexus.cli check-eligibility --wallets wallets.json --network ethereum
```

### Claim airdrops

```bash
python -m airdrop_nexus.cli claim --wallets wallets.json --network ethereum
```

### Sweep assets

```bash
python -m airdrop_nexus.cli sweep --wallets wallets.json --network ethereum --tokens --nfts
```

Use `--dry-run` to build transactions without broadcasting them.

## Security notes

- Keep private keys in offline storage when possible. Use hot keys only for sweep execution.
- Consider running behind a local RPC node or a dedicated, isolated RPC endpoint.
- Validate contract addresses and ABIs before running claims or sweeps.
