# btc-race-24h-20261123-0511

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/CryptoBei/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/CryptoBei/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

Dip-buy mean-reversion BTC trading bot (Python 3.13) for make.fun's "Race a BTC trading bot live for 24 hours" bounty. It trades Coinbase Wrapped BTC (CBBTC) against USDC on 1-minute bars with $1,000 of paper money: buys when the close is 1.5% or more below the trailing 4-hour high, sells when the close recovers to that high (or rises 1.5% above entry), stops out at 1% below entry, and buys once near the end of the window if it has never traded. Chosen after comparing four strategy families on two dev windows (a falling window and a rally window): dip-buy was the only family profitable on both.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wty56aqb&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
