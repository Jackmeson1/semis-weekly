# C4 Positioning

Layer: L4 · Main horizon: near (within two weeks)

## Explainer · Added

- **Dealer gamma**: after selling options, market makers must keep hedging. When net gamma is positive, they sell as the price rises and buy as it falls, which dampens volatility; when it is negative, the reverse holds: they chase price in both directions and amplify volatility. The price level where net gamma changes sign is the gamma flip.
- **CTA**: funds that trade mechanically on price trends. When a trend turns, they buy or sell in size and in a fairly predictable direction.
- **Vol control**: funds that adjust exposure to realized volatility. When volatility rises they cut exposure mechanically, and when it falls they add back.
- **Why it only governs timing**: these funds are forced to buy and sell by rules, and their trades say nothing about their view of the companies. They can push prices away from fundamentals in the short run, but the gap closes (INF-03).

## What the author thinks

- In the short run, look only at positioning: the author holds that when buying a dip you should ignore fundamentals and watch positioning alone; a momentum-driven selloff has nothing to do with company fundamental research.
- **Repair order**, after the sharp drop of August 2024: step one is waiting for gamma to recover (about 1 week); step two is the CTA stop-loss selling ending (2 weeks or more); step three is long-only funds (LOs) buying the dip. This is the best teaching case in the channel: look at volatility and gamma first, then CTAs, and long-term money last.
- ACT-02, enter after positioning clears: on 2026-03-31 the author listed seven funding-structure reasons and bought with full size; one example was that CTA selling had run its course, so from the following week CTAs would be buyers whether the market rose or fell.

## Signals

| ID | What | Threshold | Basis |
|---|---|---|---|
| S-L4-01 | Suppressed volatility: VIX below the 15th percentile of 3 years | watch only | Inferred |
| S-L4-02 | Volatility shock: VIX ≥ 25 or +6 over 5 days | watch VIX ≥ 20 or +4 over 5 days | Added |
| S-L4-03 | SPY + QQQ net GEX and distance to the flip | negative gamma is binding; within 1.5% of the flip is watch | Inferred + Added |
| S-L4-04 | 3-year percentile of CFTC leveraged-fund net equity-index futures positions | below 10 is a crowded short, above 90 is a crowded long | Inferred |

## Switching rules

- SW-M-04: VIX very low, with heavy vol selling and CTAs and vol-control funds adding leverage together → low tolerance for error
- SW-m-01: volatility falls back, gamma rebuilds, and deleveraged longs return
- SW-m-03: dealer gamma recovers and the CTA tailwind is spent → the focus shifts to earnings

## Common pitfalls

- GEX depends on an assumption about dealer direction. The public convention (the SqueezeMetrics white paper) is that customers sell calls and buy puts, so dealer call gamma is positive and put gamma is negative. Public data cannot show the true direction, and paid products only estimate it. The gamma flip is not a factual price level.
- The direction assumption is less reliable for single-stock options (NVDA, SMH) than for indices; SMH is displayed but not used for judgment.
- A low VIX is not by itself a sell signal; it only means low tolerance for error.
- CFTC positions are as of Tuesday and published on Friday, a 3-day lag.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty. Add one item: by the repair order, which step we are on now.
