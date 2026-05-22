export class RiskAgent {
  constructor({
    maxTradePercent = 0.02,
    dailyLossLimitPercent = 0.05,
    minProfitOverGasMultiplier = 2,
  } = {}) {
    this.maxTradePercent = maxTradePercent;
    this.dailyLossLimitPercent = dailyLossLimitPercent;
    this.minProfitOverGasMultiplier = minProfitOverGasMultiplier;
    this.dailyPnl = 0;
  }

  riskCheck({ expectedProfitEth, expectedGasEth, tradeSizeEth, equityEth }) {
    if (tradeSizeEth > equityEth * this.maxTradePercent) {
      return { ok: false, reason: 'Trade size exceeds max allocation.' };
    }

    if (expectedProfitEth < expectedGasEth * this.minProfitOverGasMultiplier) {
      return { ok: false, reason: 'Profit is below gas-adjusted threshold.' };
    }

    if (Math.abs(this.dailyPnl) > equityEth * this.dailyLossLimitPercent) {
      return { ok: false, reason: 'Daily loss limit reached.' };
    }

    return { ok: true };
  }

  recordPnl(deltaEth) {
    this.dailyPnl += deltaEth;
  }
}
