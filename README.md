## Wallet Monitoring Utility (Defensive)

This repository now contains a **defensive wallet auditing script** that checks
public blockchain metadata for addresses you own or are explicitly authorized to
monitor.

### What it does
- Validates Ethereum address formatting.
- Fetches public ETH balance and latest transaction metadata from Etherscan.
- Flags inactivity based on a configurable threshold.
- Exports reports to JSON.

### What it does **not** do
- No private key recovery.
- No seed brute forcing.
- No unauthorized asset retrieval.

### Usage
```bash
export ETHERSCAN_API_KEY="<your-key>"
python 'seed gen 2.0' 0xYourAddressHere --inactive-days 120 --output report.json
```

> Use only with wallets you control or are legally authorized to audit.
