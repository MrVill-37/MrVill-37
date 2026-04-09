# Hybrid Arbitrage Bot Review (Security + Reliability)

This review covers the Python bot code shared by Mr.V.

## Critical issues

1. **Non-atomic two-leg execution risk (spot arb)**
   - The bot sends the first market order, then the second.
   - If the second fails, you are left with directional exposure and no automatic recovery.
   - Current behavior only logs "manual hedge required".

2. **No circuit breaker on exchange/API instability**
   - Repeated failures continue in the main loop.
   - This can cause cascading retries, stale decisions, and execution during partial outages.

3. **Funding/basis logic uses simple annualization and immediate execution**
   - `rate * 3 * 365` overstates practical carry if rates mean-revert.
   - There is no holding-period model, no borrow cost, no mark/impact model, and no liquidation buffer.

4. **Balance checks are race-prone and incomplete**
   - Free balances are checked immediately before order placement only.
   - Between check and order placement, balances can change.
   - For basis, perp margin requirements are not validated.

5. **Exposure accounting does not represent true risk**
   - Exposure is reserved/released around each trade and mostly flattened immediately.
   - Open basis inventory risk is not tracked as position state (entry, mark, funding accrual, liquidation risk).

## High-priority improvements

1. **Implement a hedge-failure recovery workflow**
   - On second-leg failure, immediately place compensating order (or reduce-only fallback).
   - Add retry policy with bounded attempts and slippage guard.

2. **Use IOC/FOK or post-only logic per strategy**
   - For latency-sensitive arbitrage, avoid blind market orders where possible.
   - Include max spread / min fill ratio checks before accepting partial fills.

3. **Introduce a hard kill-switch**
   - Stop trading after N consecutive API failures, stale data windows, or large realized slippage.
   - Emit structured alerts (webhook/log sink).

4. **Track real positions, not just transient notional**
   - Keep per-venue position ledger with average entry, fees, and mark-to-market PnL.
   - Risk limits should evaluate gross + net + stress-scenario exposure.

5. **Harden data freshness checks**
   - Reject quotes/funding samples older than a strict threshold.
   - Reject books with abnormal spread or too little top-of-book size.

## Medium-priority improvements

- Add idempotency keys / client order IDs for safer retries.
- Enforce symbol-specific min notional and step size using exchange metadata every order.
- Add explicit maker/taker fee mode and dynamic fee tier updates.
- Separate strategy config per symbol and per exchange.
- Record immutable execution journal (JSONL) for audits and post-trade attribution.

## Suggested architecture changes

1. **Pre-trade validation layer**
   - Freshness, spread sanity, depth sanity, fee/slippage model, and risk budget check.

2. **Execution state machine**
   - `PLANNED -> LEG1_SENT -> LEG1_FILLED -> LEG2_SENT -> HEDGED/FAILED_RECOVERY`.

3. **Risk daemon**
   - Continuous checks for exposure, drawdown, connectivity, and position drift.

4. **Strategy-specific PnL models**
   - Spot arb: realized spread net of fees/slippage.
   - Basis: carry accrual model + mark risk + liquidation constraints.

## Test plan you should run for this bot

1. Unit tests
   - Quote freshness rejection.
   - Fee/slippage edge threshold checks.
   - Risk limit acceptance/rejection paths.
   - Second-leg failure recovery path.

2. Integration tests (mock exchange)
   - Partial fills and timeout scenarios.
   - Balance changes between check and submit.
   - Exchange outage and reconnect behavior.

3. Dry-run simulation
   - Replay historical books/funding data.
   - Measure hit ratio, slippage, and drawdown under stress windows.

## Minimal secure defaults

- `DRY_RUN=true` in all non-production contexts.
- `MAX_TRADE_USD` tiny until validated.
- Mandatory kill-switch thresholds for errors, slippage, and drawdown.
- Disable basis trading unless perp margin and liquidation checks are implemented.
