# Airdrop Nexus (Safe Mode)

Offline-capable wallet operations helper built for defensive, consent-based workflows.

## Safety boundaries

- Does not sign or broadcast transactions.
- Does not collect or export private keys or seed phrases.
- Intended only for wallets you own or are explicitly authorized to manage.

## Features

- Validate wallet lists.
- Evaluate local JSON allowlists for airdrop eligibility.
- Create non-broadcast plans for ETH, ERC-20, and NFT assets on supported EVM networks.
- Run a local, futuristic operator UI.

## CLI

From this directory:

```bash
python3 airdrop_nexus.py import-wallets --file wallets.txt
python3 airdrop_nexus.py check-eligibility --wallets wallets.txt --rules eligibility.json
python3 airdrop_nexus.py plan-sweep --inventory inventory.json --vault 0xeDAe4f188103fd971430c67467d90db0ED1bA92c --gas-reserve-eth 0.003
```

## UI

```bash
python3 ui_server.py
# open http://localhost:8080
```

## Tests

```bash
python3 -m pytest -q tests
```
