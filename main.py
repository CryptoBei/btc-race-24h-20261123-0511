"""Dip-buy mean-reversion bot for make.fun's btc-race-24h-20261123-0511:
race a BTC trading bot live for 24 hours. Simulation only: $1,000 of
paper money, one asset (CBBTC, Coinbase Wrapped BTC on Solana), long only.

The idea: 1-minute BTC mean-reverts at the 1-2% scale, while a full-size
round trip costs ~26 bps in fees, slippage and price impact, so the bot
trades rarely and only on a real dip. The regime decides the family:
BTC is -24% over 30 days with a sharp +4% bounce today, so the live
window can rally on or fade. Four families were compared on TWO dev
windows (the Nov 16-17 falling window, -2.8%, and this race's Nov 22-23
rally window, +3.6%): buy-and-hold (-$31.63 / +$32.17), breakout
momentum (-$28.19 / +$26.12), Donchian/EMA/RSI (all negative on at
least one window, RSI -$88 on the rally window from 66 overtraded
round trips). Dip-buy mean reversion was the only family positive on
BOTH windows (+$2.33 / +$20.31 in the offline simulator), so it is the
pick: it buys weakness, sells the recovery quickly, and a 1% stop caps
any single trade's loss if the bounce fades.

Verified with a local bars-replay/v1 mock harness (no Docker on this
machine, so grade-local cannot run a Python bot here): the actual
main.py scores +$20.31 on the dev window, 4 trades, 0 rejections,
max drawdown 0.59%, and two runs produce byte-identical action logs.

Rules (all comparisons in exact integer per-mille, no floats, no clock,
no randomness, so two runs produce byte-identical action logs):
  - LOOKBACK 240 bars (4 hours): the reference high is the max close of
    the previous 240 bars.
  - BUY (full cash) when the close is 1.5% or more below that high:
    close * 1000 < high * 985.
  - SELL the whole position when the close recovers to the high, or
    rises 1.5% above the entry close: close * 1000 >= entry * 1015.
    (The recovery exit dominates in practice; the 1.5% target is a
    backstop that lets winners run a little in a rally.)
  - STOP: sell the whole position when the close falls 1.0% below the
    entry close: close * 1000 <= entry * 990. Caps the loss of any one
    trade at about 1% plus costs.
  - FALLBACK: if no trade has happened by batch 1200, buy once with the
    full cash and hold under the same exit/stop rules, so the bot never
    sits out a window with zero trades (the guardrails need >= 1 trade).

The bot speaks agent-fun/bars-replay/v1 through the vendored shim:
hello once, then one batch per bar (its close, fills, account), one
reply per batch echoing its seq, then done. Orders decided on a batch
fill at the next bar's open; the shim's state carries cash, equity,
positions and the latest close per symbol.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
#: Bars of history the reference high looks back over (4 hours).
LOOKBACK_BARS = 240
#: Buy when the close is at least this far (per-mille) below the high.
DIP_PER_MILLE = 15
#: Sell when the close is this far (per-mille) above the entry close.
EXIT_PER_MILLE = 15
#: Sell when the close is this far (per-mille) below the entry close.
STOP_PER_MILLE = 10
#: If no trade has happened by this batch, buy once and hold.
FALLBACK_BATCH = 1200
#: Wide open, like the kit baselines: a fill never rejects on slippage.
MAX_SLIPPAGE_BPS = 10_000

#: Every batch's close so far (None before the first bar), by seq.
closes = []
#: The decision close of the open position, or None while flat.
entry = None
#: Whether any buy has been sent this run (the fallback fires once).
traded = False


def trailing_high(seq):
    """The max close of the LOOKBACK_BARS bars before batch ``seq``, or None."""
    if seq < LOOKBACK_BARS:
        return None
    high = None
    for i in range(seq - LOOKBACK_BARS, seq):
        c = closes[i]
        if c is not None and (high is None or c > high):
            high = c
    return high


def on_batch(state, batch):
    """The orders decided on this bar; None or [] for none."""
    global entry, traded
    closes.append(state.close(SYMBOL))
    if state.warming_up:
        return []
    px = closes[batch["seq"]]
    if px is None:
        return []
    position = state.positions.get(SYMBOL)
    high = trailing_high(batch["seq"])

    if position is None:
        # Flat: buy a dip, or the fallback once the window is nearly over.
        if high is not None and px * 1000 < high * (1000 - DIP_PER_MILLE):
            entry = px
            traded = True
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if batch["seq"] >= FALLBACK_BATCH and not traded:
            entry = px
            traded = True
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # In a position: exit on recovery, on the gain target, or on the stop.
    if entry is None:
        return []
    if (px * 1000 >= entry * (1000 + EXIT_PER_MILLE)
            or (high is not None and px >= high)
            or px * 1000 <= entry * (1000 - STOP_PER_MILLE)):
        entry = None
        return [{"side": "sell", "symbol": SYMBOL, "qty": position.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
