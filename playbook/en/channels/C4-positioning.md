# C4 Positioning

Layer: L4 · Main horizon: near (within two weeks); the mid horizon reads it too (the author: from two weeks to three months, positioning outweighs the company layer)

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

## From the videos (the author, stated, 2024-05 to 2026-10, 83 videos)

What follows is the logic the author laid out in the weekly videos, recorded as they meant it. It does not mean the logic has been validated. The figures in brackets are the number of videos that support it and when. Where the author changed their position, the date is given. Items marked "added" are ours, not the author's. These are probability judgments, not laws. A conclusion is usually a chain of conditional judgments multiplied together; each link is likely but none is certain, and the author often says "most likely", "I think" or "fifty-fifty". Read each item as "under these conditions, it tends to go this way". When checking, look at which links have happened, one by one; do not test the whole conclusion as if it had to hold.

- **Positioning also decides how deep a fall goes** (7 videos, 2025-02 to 2026-03). A deep fall is likely mainly when CTAs, volatility-control funds, volatility selling, and credit and rate positions are crowded at once. When several of these are not crowded, write "it can fall, but a deep fall is unlikely." When positioning is heavy, good earnings are only a window to sell.
- **Clearing does not require leverage to go to zero** (8 videos). The observable test is that bad news no longer brings growing selling pressure. CTAs, dealer gamma and order-book depth all turn better together. The money buying the dip is larger than the mechanical selling. If a market has already fallen past the extreme of light positioning, do not keep chasing the short side.
- **Leveraged-fund positioning: flow is not stock** (12 videos). An extreme in flow only says short-term clearing is close. A low net position in index futures may be single-stock long-short pairs, and does not mean a bearish view. On 2026-07-14 the author admitted to having misread such pairs as a long-short bet. The AI rally has raised structural leverage, so the 3-year percentile can read "clearly deleveraged" as "still high." Read it together with the 1-year percentile.
- **Passive buying and selling run both ways** (12 videos). After volatility falls, CTAs and volatility-control funds will most likely buy whether the market rises or falls. This is the source of cash in the repair phase. When policy uncertainty holds volatility high, this path is blocked. The starting point is not only VIX: forced covering by volatility sellers, credit options, yen carry unwinds and momentum portfolios can all start it. Whether forced unwinding can exit in an orderly way decides if the shock spills over into a liquidity crisis.
- **CTAs are asymmetric** (7 videos). When fully invested, they buy only a little on the way up and sell a lot on the way down. CTAs being full is not enough. Only when leveraged funds are also crowded does the author call a pullback likely.
- **For VIX, look at the starting point** (8 videos). Starting from an extremely low level, 15 to 20 should already be treated as an alarm (volatility-selling funds mostly sell at 12 to 13 and must cover by 15 to 16). Starting from a level that is not low, with few volatility sellers on the way down, even 25 is not a shock.
- **For gamma, look at its size and how much it has shrunk from its high, not just its sign** (7 videos). Be alert when the shield shrinks fast from a high level, even if it is still positive. Positive gamma near a one-year high means "volatility suppressed but fragile." Negative gamma is an amplifier, not the cause.
- **Low tolerance for error needs three things read together** (6 videos): heavy positioning, high valuation and strong fundamentals. When positioning is light, downgrade the case and do not treat it as brittle.
- **Earnings window** (5 videos). In the week a leader reports, the company layer rises to the same rank as positioning. When positioning is light, decent results get bought as people add allocation. When positioning is heavy, good results become a window to sell instead.
- **Exception during a recession scare** (2025-03 to 04). When a policy shock raises recession worries, positioning clearing only supports a very short-term bounce. Afterwards the author went back to the normal view that clearing means entry.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty. Add one item: by the repair order, which step we are on now.
