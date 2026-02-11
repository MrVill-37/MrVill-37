## Airdrop Nexus (Safe Mode)

Terminal-based, offline-capable wallet operations helper focused on **defensive** and **consent-based** workflows.

### What it does
- Imports and validates wallet lists.
- Evaluates local airdrop eligibility rules (offline JSON allowlists).
- Builds a **non-broadcast sweep plan** for ETH/ERC-20/NFT assets across:
  - Ethereum
  - Base
  - Arbitrum
  - zkSync
  - BNB Chain

### Security posture
- No transaction signing.
- No transaction broadcasting.
- No key exfiltration logic.
- Explicitly intended for wallets you own/control with clear authorization.

### Quick start
```bash
python3 airdrop_nexus.py import-wallets --file wallets.txt
python3 airdrop_nexus.py check-eligibility --wallets wallets.txt --rules eligibility.json
python3 airdrop_nexus.py plan-sweep --inventory inventory.json --vault 0xeDAe4f188103fd971430c67467d90db0ED1bA92c --gas-reserve-eth 0.003
```

### Example input: `wallets.txt`
```txt
0x1111111111111111111111111111111111111111
0x2222222222222222222222222222222222222222
```

### Example input: `eligibility.json`
```json
{
  "rules": {
    "allowlists": {
      "campaign-alpha": ["0x1111111111111111111111111111111111111111"]
    }
  }
}
```

### Example input: `inventory.json`
```json
{
  "0x1111111111111111111111111111111111111111": [
    {"network": "ethereum", "kind": "eth", "token": "ETH", "amount": "0.05"},
    {"network": "base", "kind": "erc20", "token": "0x3333333333333333333333333333333333333333", "amount": "250"},
    {"network": "arbitrum", "kind": "nft", "token": "0x4444444444444444444444444444444444444444", "amount": "1"}
  ]
}
```
