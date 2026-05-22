export function compound({ walletBalanceEth, reservePercent = 0.3 }) {
  const tradingCapital = walletBalanceEth * (1 - reservePercent);
  return Number(tradingCapital.toFixed(6));
}
