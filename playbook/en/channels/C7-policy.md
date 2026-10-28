# C7 Policy and events

Layer: L1.fed_path, L1.fiscal_politics, L0.geopolitics · Main horizon: mid

## Explainer · Added

- This channel holds things that cannot be expressed as a single number: FOMC meetings, tariffs, elections, wars and export controls.
- **In the author's ranking the Fed rate-cut path is always last** (HZ-05, net −53). Its effect on assets has to pass through long-end rates and liquidity before it shows up, so reading C2 directly is enough.
- **A policy shock's veto needs an expiry date** (CAL-01). When a shock first arrives everything else gives way; once prices stop reacting to new policy news, the veto should end, without waiting for the policy itself to take effect.

## What the author thinks

- The number of cuts does not matter: the author holds that the rate-cut topic is stale and the market need not focus on it, and that two cuts versus one makes little difference; it does not help long-end rates and cannot produce a liquidity-driven bull market.
- SW-M-03: when the market prices in too many cuts, the importance of macro returns.
- CAL-01, the author's own assessment of their biggest mistake: after leaving the market at the end of the previous year, the biggest error of that year was not daring to buy the dip in April, having failed to see that the tariff threats would ultimately be withdrawn.

## Signals

There is no automatic signal in v1. The inputs are:
- The calendar: FOMC meetings, major data releases, known policy milestones (`sources/calendar.yaml`)
- You can paste the news headlines you are watching this week into `inputs/<week>/notes.md`; the model judges only from what you provide and does not look for news itself

## Common pitfalls

- Do not write a separate conclusion about rate-cut expectations; leave that to C2.
- During a policy shock, record the date the shock began, and each week check whether prices are still reacting to new news, to judge whether the veto has expired.

## What to write in this week's log

State (whether a policy shock is in effect and whether it has expired), one line, evidence, deviations and uncertainty.
