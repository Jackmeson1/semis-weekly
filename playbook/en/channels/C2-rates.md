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

## From the videos (the author, stated, 2024-05 to 2026-10, 83 videos)

What follows is the logic the author laid out in the weekly videos, recorded as they meant it. It does not mean the logic has been validated. The figures in brackets are the number of videos that support it and when. Where the author changed their position, the date is given. Items marked "added" are ours, not the author's. These are probability judgments, not laws. A conclusion is usually a chain of conditional judgments multiplied together; each link is likely but none is certain, and the author often says "most likely", "I think" or "fifty-fifty". Read each item as "under these conditions, it tends to go this way". When checking, look at which links have happened, one by one; do not test the whole conclusion as if it had to hold.

- **Look at volatility and speed, not the level** (at least from 2025-01). The real money that buys credit (insurers, pension funds, foreign investors) looks at the all-in yield, so a steady rise in rates is actually good for them. What they cannot stand is rates swinging back and forth.
- **A sharp move in the 10-year yield needs its cause checked first** (6 videos). A rise driven by a strong economy is not a warning. A yield rise with a falling dollar is read as capital flight (2025-04). A sharp rise only adds to the concern when volatility rises too (2026-05, 2026-09). If only the 2-year moves and the 10-year does not, the Fed path is just an event and not a driver of the long end.
- **The curve has a direction** (8 videos). A bull steepener is read as rate-cut pricing and is fairly neutral. A bear steepener is read as supply or term premium and leans negative. Flattening caused by fast rate hikes is the most dangerous.
- **Supply must be counted by duration** (about 12 videos). What weighs on the long end is the year's net supply measured by duration, not the face amount issued. Short-dated debt does not weigh on the long end. The author's view has changed. From 2024-05 to 2025-01 supply was seen as the biggest risk to the long end. From 2025-04, with supply down year over year and banks able to buy more Treasuries, it was only background. In the 2026-09 shock the author said buyers "know it is cheap and still do not move."
- **Looser bank capital rules cushion supply** (7 videos). This is why supply did not push the 10-year up in the first half of 2026. From 2026-06-30 the author thinks most of this effect has already played out.
- **After the Fed stops weighing on the long end** (from 2026-06, under the new chair). The long end moves toward the pace of nominal GDP growth, and the gap between nominal growth and the 10-year yield is about 180bp. Use it only as a reading; do not copy the author's level forecasts.
- **How a rate shock ends** (2026-09 to 10). Rate volatility falls from its high, the 10-year yield comes down from its peak, and convexity hedging ends. The recovery order the author observed was rate volatility, then major currencies, then emerging-market and European sovereign bonds, then CCC credits, then the stock market (an observation from a single event).
- **The yen has two paths.** A stronger yen together with carry-trade unwinding is the bad case. When Japanese fiscal policy pushes up the long end of Japanese bonds and the yen weakens at the same time, the global long end steepens, but carry-unwind risk is small. To judge the carry trade, watch the volatility of Japanese rates, not whether the yen rises or falls. The 2024-07 episode ran the other way: US stocks fell first and that triggered the carry unwind.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty.
