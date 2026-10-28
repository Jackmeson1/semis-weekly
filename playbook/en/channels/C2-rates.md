# C2 Rates

Layer: L1.long_end, L2.treasury_issuance · Main horizon: near, mid

## Explainer · Added

- **The 10-year yield has two parts**: the market's expectation of future short-term rates, plus the term premium, which is the extra compensation for holding long bonds. When Treasury supply is heavy and rate volatility is high, the term premium rises. So a Fed cut pushes down the first part, while the second part may actually rise (INV-02).
- **Why speed matters more than level**: when rates rise slowly, investors have time to adjust. A fast rise triggers two kinds of mechanical selling:
  - Funds that size positions by volatility (risk parity, vol control) cut exposure mechanically.
  - MBS convexity hedging: rates rise → homeowners prepay less → MBS duration lengthens → holders sell Treasuries to hedge → rates rise further. In 2026-10 the author wrote that this kind of convexity squeeze was easing.
- **Treasury auctions**: the Treasury sells new debt, and the question is whether anyone is willing to take it. A "tail" means the auction clears at a yield above where the market was quoting beforehand (when-issued), which signals weak demand. In 2024-05 the author wrote a long post on the mechanics, starting from the difference between limit orders and average-price orders.
- **The curve (2s10s)**: the long end rising more than the short end is a bear steepener, often a sign of supply or term-premium pressure; the short end falling more than the long end is a bull steepener, often a sign of rate-cut expectations. Both are steepening, but they mean opposite things.

## What the author thinks

- SW-M-02: in 2024-05 the author pointed out that the 10-year yield had jumped overnight, was up close to 20bp over 5 days, and had entered a risk warning zone.
- 2026-10: the author wrote that a slow, steady grind higher in rates does not necessarily do much to risk assets; speed is what matters.
- NOVETO-01, level cannot override AI: assets with solid fundamentals need not worry; the AI trade was not built on liquidity.
- SW-m-02: the author holds that anyone who does not dare to buy bonds should not buy stocks; a steadier bond market is a precondition for buying equities.

## Signals

| ID | What | Threshold | Basis |
|---|---|---|---|
| S-L1-01 | 5-trading-day change in the 10-year yield (absolute value) | watch 12bp, binding 20bp | Author |
| S-L1-02 | 20-day standard deviation of daily 10-year yield changes | watch 75th percentile of 3 years, binding 90th percentile | Added |
| S-L1-03 | 20-trading-day change in 2s10s | watch 25bp, advisory only | Added |
| S-L2-01 | Weak coupon auction this week | low bid-to-cover and the 10-year up 5bp on auction day | Author + Added |

## Switching rules

- SW-M-01: a weak auction, with the yield rising 5bp on the auction day
- SW-M-02: 10-year +20bp in 5 days
- SW-M-05: the yen drives a global long-end bear steepening, and stocks and bonds fall together
- SW-M-07: rate volatility hits a new high, and the 10-year and crude oil trade as a pair
- SW-m-02: be willing to buy bonds first, then talk about buying stocks

## Common pitfalls

- The author watches 3m10y swaption implied volatility; we substitute realized volatility. The measures differ, and implied volatility usually moves earlier.
- Free data has no when-issued yield, so S-L2-01 is an approximation, not a true "tail".
- The level thresholds the author has used (4.2%, 4.5%, 6%) reflect the environment at the time; do not copy them directly.
- From June to September 2024 the 10-year yield fell while the curve steepened: that happens when the short end falls more. When judging direction, look at the two things separately.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty.
