export class StrategyAgent {
  constructor() {
    this.minSpreadPct = 0.3;
    this.slippageBps = 50;
  }

  optimize(tradeHistory) {
    if (!tradeHistory.length) {
      return this.snapshot();
    }

    const wins = tradeHistory.filter((x) => x.pnlEth > 0).length;
    const winRate = wins / tradeHistory.length;

    if (winRate < 0.55) {
      this.minSpreadPct = Number((this.minSpreadPct + 0.05).toFixed(2));
      this.slippageBps = Math.max(10, this.slippageBps - 5);
    }

    return this.snapshot();
  }

  snapshot() {
    return {
      minSpreadPct: this.minSpreadPct,
      slippageBps: this.slippageBps,
    };
  }
}
