function jitter(base, variancePct = 0.35) {
  const pct = (Math.random() * 2 - 1) * variancePct;
  return Number((base * (1 + pct / 100)).toFixed(6));
}

const pairAnchors = new Map([
  ['WETH/USDC', 3500],
  ['WBTC/USDC', 65000],
  ['ARB/USDC', 0.85],
]);

export async function fetchDexPrice(dex, pair) {
  const anchor = pairAnchors.get(pair) ?? 100;
  const dexAdjustment = dex === 'uniswap' ? 1 : 0.998;
  return jitter(anchor * dexAdjustment);
}
