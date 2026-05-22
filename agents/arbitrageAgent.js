export function detectOpportunity(prices, { minSpreadPct = 0.3, pair = 'WETH/USDC' } = {}) {
  const markets = Object.entries(prices);
  if (markets.length < 2) {
    return null;
  }

  const sorted = [...markets].sort((a, b) => a[1] - b[1]);
  const [buyDex, buyPrice] = sorted[0];
  const [sellDex, sellPrice] = sorted[sorted.length - 1];

  const spreadPct = ((sellPrice - buyPrice) / buyPrice) * 100;
  if (spreadPct < minSpreadPct) {
    return null;
  }

  return {
    pair,
    buyDex,
    sellDex,
    buyPrice,
    sellPrice,
    spreadPct: Number(spreadPct.toFixed(4)),
    detectedAt: new Date().toISOString(),
  };
}
