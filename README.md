## Crypto Fund Bot (Multi-Agent, Risk-Managed)

This repository now contains a production-style baseline for a **crypto hedge fund bot** organized as specialized agents and services.

## Architecture

```text
crypto-fund/
  core/
    provider.js
    wallet.js
  agents/
    mempoolAgent.js
    arbitrageAgent.js
    strategyAgent.js
    riskAgent.js
    profitAgent.js
  engine/
    tradeExecutor.js
    opportunityQueue.js
  data/
    priceFeeds.js
    marketScanner.js
  config/
    tokens.json
    exchanges.json
  index.js
```

## What is implemented

- **Wallet/provider layer** using `ethers` with `.env` support.
- **Market scanning** across configured DEXes.
- **Arbitrage detection** using spread thresholds.
- **Risk controls**:
  - max trade size (% of equity)
  - daily loss limits
  - minimum profit over gas
- **Execution engine** with safe dry-run mode.
- **Mempool monitor** hook for pending tx analysis.
- **Strategy optimizer** that tunes spread/slippage settings from outcomes.
- **Profit compounding** to continuously adjust trading capital.

## Quick start

```bash
npm install
npm test
npm start
```

Create a `.env` file if you want chain connectivity:

```env
RPC_HTTP=https://your-rpc
# or
RPC_WS=wss://your-rpc
PRIVATE_KEY=0xyourprivatekey
UNISWAP_ROUTER=0xYourWatchedRouter
```

## Security defaults

- Uses **dry-run execution** by default.
- Does not send real swaps unless you implement router calls in `engine/tradeExecutor.js`.
- Isolated risk checks gate execution.

## Next production upgrades

- Redis-backed distributed queue.
- Flashbots/private tx relay integration.
- On-chain DEX quoter integrations (Uniswap v3/Sushi routers).
- Persistent trade journal + strategy backtesting.
- Metrics/alerts (Prometheus + Grafana).
