# C1 Credit

Layer: L3.credit · Main horizon: mid (a few weeks to a quarter); since 2026 it also affects the far-horizon direction (VETO-01)

## Explainer · Added

- **Credit spread (option-adjusted spread, OAS)**: a corporate bond's yield minus the yield on a Treasury of the same maturity, with the value of the bond's embedded options removed. It is the extra compensation investors demand for taking default risk and liquidity risk. Investment grade (IG) means issuers rated BBB or above; high yield (HY) means those below.
- **Why it transmits to semiconductors**: AI capex is increasingly financed with borrowed money, such as hyperscaler bond issuance, data-center project financing (SPVs) and neocloud loans. Wider spreads mean money is more expensive and harder to raise, so capex plans come under pressure, and that ends up in chip orders.
- **Capex as a share of operating cash flow**: below 1, capex can be covered by what the company earns; above 1, free cash flow is negative and the gap must be filled with external funding. The higher the ratio, the more important the credit layer becomes (INF-02).
- The credit market often feels stress before the equity market, because creditors care only about getting their money back and do not share in the upside.

## What the author thinks

- INV-04: a falling stock price can be endured, but deteriorating credit cannot. As long as credit does not break down sharply, one can stay firmly bullish; balance-sheet runoff or war does not change that.
- 2026-10: the author judged that the credit market currently faces an interest-rate volatility shock, not a supply-side shock; next year brings a smaller AI test, and the real supply-side test comes in 2028/29. In the same post the author said yield-oriented buyers (insurers, pension funds) hold back when rates are swinging sharply.
- Availability of funding matters more than its cost: the author argued that as long as each unit of compute keeps earning more, a few hundred basis points of extra funding cost does not change the investment math.
- CAL-02, admitted error: one cannot ignore the macro funding backdrop just because the company and industry layers look strong.

## Signals

| ID | What | Threshold | Basis |
|---|---|---|---|
| S-L3-01 | 20-trading-day change in the high-yield spread | watch +40bp, binding +75bp | Added |
| S-L3-02 | 20-trading-day change in the investment-grade spread | watch +12bp, binding +25bp | Added |
| S-L3-03 | Capex of 5 hyperscalers as a share of operating cash flow (last 4 quarters) | watch 0.8, binding 1.0 | Inferred |

## Switching rules

- SW-M-06: credit spreads and CDS deteriorate sharply → the far horizon takes over
- SW-m-05: rate volatility calms and yield-oriented buyers return to the credit market → can go back to earnings

## Common pitfalls

- The ICE BofA spreads on FRED cover only the last 3 years (in practice, starting 2023-10-30). Percentiles must use our own stored history; until it fills up, the sample is short.
- Index spreads cover the whole market, not AI specifically. The author watches single-name CDS (hyperscalers, neoclouds), which we cannot get.
- IG and HY can diverge: much of the AI bond issuance is investment grade, so IG moves first.

## From the videos (the author, stated, 2024-05 to 2026-10, 83 videos)

What follows is the logic the author laid out in the weekly videos, recorded as they meant it. It does not mean the logic has been validated. The figures in brackets are the number of videos that support it and when. Where the author changed their position, the date is given. Items marked "added" are ours, not the author's. These are probability judgments, not laws. A conclusion is usually a chain of conditional judgments multiplied together; each link is likely but none is certain, and the author often says "most likely", "I think" or "fifty-fifty". Read each item as "under these conditions, it tends to go this way". When checking, look at which links have happened, one by one; do not test the whole conclusion as if it had to hold.

- **Capex above operating cash flow does not mean funding has broken** (8 videos, 2026-02 to 10). The author's test is whether companies can still borrow, not whether cash flow is negative. A hyperscaler ratio of 1.0 only means funding dependence is rising. Funding counts as broken only when spreads are also widening, or when bond or equity issuance is being blocked.
- **The big funding test comes from late 2027 to 2028** (position changed 2026-10-27). Before that date, the author thought current liquidity was insufficient and that debt liquidity was the thing most worth worrying about. After it, the author said the real test is the refinancing wall plus new AI issuance, and that 2027 is only a small test that weighs on valuations.
- **Telling a liquidity shock from a fundamental deterioration** (4 or more videos). Check the order of causes. In a liquidity shock, rates and credit move first, equities follow two or three weeks later, and demand readings have not weakened beforehand. The author also looks "sideways" at whether investment-grade bonds, junk bonds, municipal bonds, peripheral European government bonds, currencies and peripheral-country equities are all falling together. The author twice admitted to underestimating how late equities react (2024-08, missing the yen carry trade; 2026-10, admitting equities had simply arrived late).
- **Where a shock starts decides how long it lasts.** A shock that comes out of rates and currencies is sharp and short. A shock that comes out of credit is slow and long, and can last a year. It ends when policy steps in or buyers return, not when oil prices or fundamentals change.
- **The left tail cracks first** (2026-10). The order is: buyers of yield pull back, then the lowest-rated CCC credits collapse first, then banks and asset managers hedge AI with single-name CDS, then equities are sold into a vacuum of funding. The index spread may only be near the watch level at that point.
- **When spreads widen, first ask why.** It could be a supply peak that buyers are unwilling to absorb, crowded positions clearing, or buyers truly pulling back. In 2025-10 to 12 the author read widening as clearing (leaning positive). In 2026-09 to 10 the author read the same widening as cracks across the board (leaning negative). The difference was the starting point and the buyers.
- **Funding landing all at once is itself a trigger** (2026-06 to 10). Large bond deals, IPOs and other funding landing in the same period pull cash away from long positions in a window short of liquidity, and set off momentum unwinding. When liquidity is poor, concentration hurts more than the total amount.

## What to write in this week's log

All channel logs have the same fields:

- State: Binding / Near / Not binding / No data
- One-line conclusion
- Evidence: signal IDs and values, rule IDs
- **Horizon implications**: only the horizons this channel covers. C1 writes "Mid" and "Far", for example "Mid: spreads near binding, lean toward adding a hedge; Far: capex / operating cash flow at 0.85, dependence on funding rising"
- Change vs last week: which signal's state changed
- Explainer: use this week's numbers to explain what the channel measures (for learning, 3–5 sentences)
- Deviations and uncertainty

A channel log judges only its own channel and does not comment on other channels. Transmission across channels is checked at level 2.
