import test from 'node:test';
import assert from 'node:assert/strict';

import { detectOpportunity } from '../agents/arbitrageAgent.js';
import { RiskAgent } from '../agents/riskAgent.js';
import { compound } from '../agents/profitAgent.js';

test('detectOpportunity returns route for sufficient spread', () => {
  const result = detectOpportunity({ uniswap: 100, sushiswap: 100.5 }, { minSpreadPct: 0.3, pair: 'WETH/USDC' });
  assert.ok(result);
  assert.equal(result.buyDex, 'uniswap');
  assert.equal(result.sellDex, 'sushiswap');
});

test('risk agent blocks weak profit', () => {
  const risk = new RiskAgent();
  const decision = risk.riskCheck({
    expectedProfitEth: 0.001,
    expectedGasEth: 0.001,
    tradeSizeEth: 0.1,
    equityEth: 10,
  });

  assert.equal(decision.ok, false);
});

test('compound keeps reserve in wallet', () => {
  assert.equal(compound({ walletBalanceEth: 10, reservePercent: 0.3 }), 7);
});
