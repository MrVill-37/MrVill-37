import fs from 'node:fs/promises';

import { provider } from './core/provider.js';
import { wallet } from './core/wallet.js';
import { detectOpportunity } from './agents/arbitrageAgent.js';
import { startMempoolMonitor } from './agents/mempoolAgent.js';
import { RiskAgent } from './agents/riskAgent.js';
import { StrategyAgent } from './agents/strategyAgent.js';
import { compound } from './agents/profitAgent.js';
import { executeTrade } from './engine/tradeExecutor.js';
import { OpportunityQueue } from './engine/opportunityQueue.js';
import { scanPrices } from './data/marketScanner.js';

async function loadConfig(path) {
  const content = await fs.readFile(path, 'utf-8');
  return JSON.parse(content);
}

async function main() {
  const exchanges = await loadConfig('./config/exchanges.json');
  const queue = new OpportunityQueue();
  const risk = new RiskAgent();
  const strategy = new StrategyAgent();
  const tradeHistory = [];

  const settings = strategy.snapshot();
  const prices = await scanPrices('WETH/USDC', exchanges);
  const opportunity = detectOpportunity(prices, settings);

  if (opportunity) {
    queue.enqueue(opportunity);
  }

  const current = queue.dequeue();
  if (!current) {
    console.log('No opportunity met current strategy threshold.');
    return;
  }

  const equityEth = 10;
  const tradeSizeEth = 0.2;
  const expectedGasEth = 0.003;
  const expectedProfitEth = (current.spreadPct / 100) * tradeSizeEth;

  const decision = risk.riskCheck({
    expectedProfitEth,
    expectedGasEth,
    tradeSizeEth,
    equityEth,
  });

  if (!decision.ok) {
    console.log(`Trade blocked by risk controls: ${decision.reason}`);
    return;
  }

  const route = {
    amountInEth: tradeSizeEth,
    buyDex: current.buyDex,
    sellDex: current.sellDex,
    pair: current.pair,
    minSpreadPct: settings.minSpreadPct,
  };

  const result = await executeTrade(route, { dryRun: true });
  const realizedPnl = expectedProfitEth - expectedGasEth;
  risk.recordPnl(realizedPnl);
  tradeHistory.push({ pnlEth: realizedPnl, spreadPct: current.spreadPct });

  const optimization = strategy.optimize(tradeHistory);
  const tradingCapital = compound({ walletBalanceEth: equityEth });

  const mempoolMonitor = startMempoolMonitor(provider, {
    watchedAddress: process.env.UNISWAP_ROUTER,
    onRelevantTx: (tx) => {
      console.log('Relevant mempool tx observed:', tx.hash);
    },
  });

  mempoolMonitor.stop();

  console.log(
    JSON.stringify(
      {
        status: result.status,
        walletConnected: Boolean(wallet),
        opportunity: current,
        execution: result,
        riskDailyPnlEth: risk.dailyPnl,
        optimizedStrategy: optimization,
        tradingCapitalEth: tradingCapital,
      },
      null,
      2
    )
  );
}

main().catch((err) => {
  console.error('Bot failed:', err);
  process.exitCode = 1;
});
