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
