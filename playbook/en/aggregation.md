# Aggregation rules: level 2 (horizon) and level 3 (synthesis)

## 1. Level 2: far, mid, near

Each horizon reads only the channel logs listed in the table below and answers one question. Do not go back to the raw signals; if you need a number, cite the number in the channel log.

**Near flags risk; it does not time.** Calls on the next two weeks are not accurate, and the log says so. The near log only answers whether conditions would amplify a short-run drop; it does not say "add now" or "cut now". The action comes from far and mid. (A choice of this project, made in 2026-10.)

| Horizon | Question it answers | Channel logs to read | Rules that apply |
|---|---|---|---|
| Near (within two weeks) | Would a drop be amplified in the short run? (a risk flag only) | C4, and the speed part of C2 | HZ-01, INF-03, ACT-02, VETO-03 |
| Mid (two weeks to one earnings cycle) | How large a position, and whether to hedge | C1, C2, C3, C4, C6, C7 | HZ-02, HZ-03, VETO-02, VETO-04, CAL-01, CAL-03 |
| Far (six months or more) | Does the direction for semiconductors still hold? | C5, C1's S-L3-03, `invariants.md` | HZ-04, VETO-01, NOVETO, INF-01, INF-02 |

Each horizon log contains: the conclusion, the channel logs it relies on, whether channels conflict, how conflicts were resolved, the result of the transmission-chain check, and deviations and uncertainty.

### Transmission-chain check

Level 1 channels are judged in isolation and cannot see transmission between channels. Level 2 must check the known chains explicitly: **when an upstream channel is already at watch or binding and the downstream one has not moved yet, mark it "Transmitting, downstream unconfirmed"**. This is the early warning that isolated judgment misses.

| Chain | Path | Basis |
|---|---|---|
| CH-A | C2 rate volatility → C1 credit → hyperscaler and neocloud funding → C5 industry | Stated: the author said the source of the shock is interest-rate volatility (the correlation between rates and oil), which is spreading in a trend to other macro assets, though not yet to equities |
| CH-B | C1 credit → hyperscaler capex (S-L3-03) → C5 industry | Inferred: INF-02 |
| CH-C | C4 volatility shock → vol control and CTAs sell mechanically → deleveraging | Inferred: the repair order in C4, reversed, is the transmission order |
| CH-D | C7 policy shock → C2 long end → C1 credit | Added: during the April 2025 tariff shock, the long end and credit came under pressure together |

Do not invent new chains. If you suspect a new one, write it under "Deviations and uncertainty"; a human confirms it before it is added to this table.

### Horizon ranking · Inferred

Derived from 393 filtered pairwise comparisons. The core entries hold under all five filter strengths.

| ID | Horizon | Who has the final say (higher on the left) |
|---|---|---|
| HZ-01 | Within two weeks | Positioning (L4) far above the other layers; companies and macro policy at the bottom |
| HZ-02 | Two weeks to three months | Positioning (L4) > cross-asset/credit (L3) > the rest; companies lowest |
| HZ-03 | One earnings cycle | Liquidity plumbing (L2) ≈ industry (L5) ≈ AI demand (L0) > companies (L6); macro policy lowest |
| HZ-04 | Six months or more | Industry (L5) ≈ AI demand (L0) ≈ US Treasury supply (L2); companies and macro policy at the bottom |
| HZ-05 | All horizons | The Fed rate-cut path ranks last (net −53) |

### Horizon log format

Files `logs/<week>/near.md`, `mid.md`, `far.md`. Numbers must come only from level 1 logs. Follow `style.md`: names, not IDs, in the text and tables.

````markdown
# Mid · two weeks to one earnings cycle · 2026-W44

**State**: Near
**One line**: ……

## Channels used
| Channel | State | Implication for this horizon (taken from the channel log) |
|---|---|---|

## Conflicts between channels
…… Write "None" if there are none.

## Transmission chains
| Chain | Status | Note |
|---|---|---|
| Rate volatility into credit and cloud funding | Transmitting, downstream unconfirmed / Not seen / Not applicable | …… |

## Conclusion
Answer this horizon's question (see the table in section 1).

## Deviations and uncertainty

```json
{"level": 2, "scope": "mid", "state": "watch", "verdict": "……",
 "chains": {"CH-A": "Not seen｜……", "CH-B": "Transmitting, downstream unconfirmed｜……"},
 "input_refs": ["1:C1:state", "1:C2:horizon:mid"], "rule_refs": ["HZ-02"], "deviation": "", "confidence": "medium", "model": "opus"}
```
````

## 2. Level 3: synthesis

### Synthesis log format

File `logs/<week>/synthesis.md`. Numbers must come only from level 1 and level 2 logs. Follow `style.md`.

````markdown
# Synthesis · 2026-W44

**Action**: Hold
**One line**: ……

## Roles
Far sets direction: ……; mid sets position size and hedging: ……; near flags short-run risk: ……

## Exception checks
Three questions, each answered yes or no with the evidence: Is funding blocked? Is strong industry data hiding a funding risk? Are rate volatility and credit spreads in trouble at the same time?

## Invariant check
| Invariant | Status | Basis |
|---|---|---|

## Deviations and uncertainty (all levels)

```json
{"level": 3, "scope": "all", "action": "Hold", "verdict": "……",
 "invariants": {"INV-01": "Stable｜……", "INV-02": "Stable｜……", "INV-03": "Stable｜……", "INV-04": "Under pressure｜……"},
 "input_refs": ["2:near:state", "2:mid:state", "2:far:state"], "rule_refs": ["ACT-01"], "deviation": "", "confidence": "medium", "model": "opus"}
```
````

`action` must be one of: Add / Hold / Reduce / Hedge (they may be combined, for example "Hold, add a light hedge").

Read the three horizon logs and `invariants.md`, and reach a conclusion in the following order.

1. **Roles** (ACT-01): far sets direction, mid sets position size and hedging. Near only flags short-run risk; it is not accurate and does not set the timing of entries and exits (a choice of this project, see section 1).
2. **Exceptions**:
   - VETO-01: when C1 is binding and S-L3-03 is binding, the mid-horizon conclusion may downgrade the far-horizon direction.
   - CAL-02: when industry (C5) looks very good while credit (C1) is deteriorating, follow credit.
   - CAL-03: when rate volatility (C2's S-L1-02) and credit spreads (C1's S-L3-01 or S-L3-02) are both at watch, treat it as binding. This is the "liquidity shock" combination; it is not any two signals from C1 and C2 being at watch together.
3. **Invariant check**: INV-01 to INV-04, each marked Stable / Under pressure / Shaken.
4. **Action implication**: Add / Hold / Reduce / Hedge. Do not write specific position sizes or price levels.
5. **Deviations and uncertainty**: collect all deviations from the three levels, missing data, and any "Added" rules that were used.

### Veto table

What can veto INV-01 (AI demand):

| ID | What | How long it lasts | Channel | Basis |
|---|---|---|---|---|
| VETO-01 | Funding breaks down | Changes the direction | C1 | Stated |
| VETO-02 | Rate speed gets out of control | A few weeks | C2 | Inferred |
| VETO-03 | Extreme positioning: negative gamma, volatility shock | A few days to a few weeks; changes timing only | C4 | Inferred |
| VETO-04 | Policy shock | A few weeks to one quarter; has an expiry date | C7 | Inferred |

What cannot override INV-01:

| ID | What | The author's view (paraphrased) |
|---|---|---|
| NOVETO-01 | Level of long-end rates | Assets with solid fundamentals need not fear the level of rates; the AI trade was not built on liquidity |
| NOVETO-02 | Fed rate-cut path | See HZ-05 |
| NOVETO-03 | Bubble talk, crash talk | The author's attitude is to ignore it outright |
| NOVETO-04 | Delays and small problems in the industry | The author sees CPO and 800V as only a matter of time and says to keep watching the models |

### Trade-off rules · Inferred

- **INF-01 Rate speed vs AI demand**: normally AI wins; when rate speed gets out of control, rates win for a few weeks, then AI takes over again. What decides it is speed, not level. Added: one can also compare how fast earnings expectations are being revised up with how fast the 10-year yield is rising.
- **INF-02 Credit ranks higher as the share of external funding rises**: the more capex depends on external funding, the higher credit ranks. S-L3-03 quantifies this.
- **INF-03 Positioning changes timing only**: when positioning is extreme, hedge, reduce or wait, and enter once it has cleared; do not change the directional view because of positioning.

### Action rules · Inferred

- **ACT-01**: the far horizon sets position size and hedging; the near horizon decides what to buy. Position statistics: 42% of buy rationales sit at the company layer and 27% at the industry layer; actions justified by rates alone are almost all rate trades, hedges or reductions.
- **ACT-02**: once positioning has cleared, positioning reasons alone can set the entry timing. Example: 2026-03-31, when the author entered on funding-structure reasons (see C4).

### Calibration lessons

The author's mistakes almost always come from thresholds, not from the ordering.

- **CAL-01** A policy shock's veto needs an expiry date (see C7).
- **CAL-02** Industry strength cannot override the funding backdrop: the author admitted that one cannot ignore the macro funding backdrop just because the company and industry layers look strong.
- **CAL-03** The effect of a liquidity shock on equities is easy to underestimate: the author admitted underestimating the effect of such shocks on equities. The trigger is S-L1-02 and S-L3-01/02 both at watch (when the files were split in v0.2 this was mistakenly written as "C1 and C2 both at watch"; it was found and corrected in 2026-W44).
- **CAL-04** Thresholds are recalibrated as the rate environment changes; review the calibration log every 4–8 weeks.

## 3. From the videos: conditions, exceptions and new chains (the author, stated, 2024-05 to 2026-10)

What follows records the logic the author laid out in the videos, as they meant it. It does not mean the logic has been validated. Where the author changed their position, the date is given. Levels 2 and 3 may cite these when judging, and must give the date and write "the author thinks." These are probability judgments: a conclusion is often the product of several conditional links, none of them certain. Check transmission chains link by link and say which links have happened and which are not yet visible; do not test a whole chain as if it had to hold.

### Exceptions to the horizon ranking

- **HZ-05 puts the Fed path last, with exceptions** (9 videos, recurring from 2024-08 to 2026-09). When nonfarm payrolls break through the line, when the odds of a cut or hike are rewritten sharply within a week, or when inflation is high while growth is falling (the Fed has no room to act), the Fed path rises within two weeks to the same rank as positioning, as a "short-term catalyst." It does not change the long-term ranking.
  - The payrolls lines (11 or more videos, 2024-06 to 2025-08): a three-month average below about 120,000 means the Fed moves from watching inflation to watching growth. Below about 80,000, the Fed puts unemployment ahead of inflation. An unemployment rate of 4.5% to 4.7% is the second line. The author also said that the job gains needed to hold unemployment steady change with immigration: about 150,000 to 180,000 in 2024-10, and about 50,000 from 2025-09.
  - Overpricing counts in both directions (7 videos): macro matters again when cuts are overpriced and also when hikes are overpriced.
  - Stages of bad news (9 videos): while the number of cuts is not settled and the economy is not in recession, bad news is good news. Once the cuts are settled, or when cuts cannot rescue earnings, bad news is bad news. Stocks fall hardest just as the data starts to get worse, and the equity bottom comes before the data bottom.
  - The Fed's trade-off (from 2025-04): when inflation comes from one-off shocks such as tariffs and oil, and wages are not out of control (about 3.5% to 3.6% is consistent with 2% inflation), the Fed chooses to protect jobs.
  - Cuts must be split into precautionary and recessionary: after a precautionary cut stocks mostly keep rising, and after a recessionary cut they do not. There is a "sell the news" risk on the day of the cut.
  - Ranking of labor data: the establishment-survey payrolls come ahead of the unemployment rate, and the unemployment rate comes ahead of sentiment surveys.
- **HZ-02 earnings window**: in the week a leader reports, the company layer rises to the same rank as positioning (see C4).

### Vetoes and non-vetoes

- **VETO-04 / CAL-01**: expiry is judged by two checks, on prices and on actual policy, split into a price layer and a real-economy layer, with the expected expiry set by the type of shock (see C7).
- **VETO-01**: capex at 1.0 of operating cash flow does not mean funding has broken. What matters is whether companies can still borrow (see C1).
- **NOVETO-01 level of the long end**: it mostly cannot hold down assets with earnings growth (AI, semiconductors). It does weigh on assets with no earnings that depend on liquidity (small caps, unprofitable tech, gold). On the index as a whole it works slowly through valuation. This assumes the main line is intact and rate speed is orderly.
- **NOVETO-03 bubble talk**: keep ignoring it. The reasons and the watch points are in `invariants.md`.
- **INF-03 / ACT-02**: positioning also decides depth, and clearing does not require leverage to go to zero (see C4). In the 2025-03 to 04 period of policy shock plus recession worries, clearing only supported a very short-term bounce.

### Transmission chains (corrected and new)

| Chain | Path | Basis |
|---|---|---|
| CH-A (extended) | Oil and diesel volatility → the Fed does not support the long end → rate volatility → insurers and hedge funds forced to deleverage, and mortgage-bond convexity hedging → buyers of yield pull back → CCC credits collapse first → single-name CDS used to hedge AI → equities sold into a funding vacuum | Stated, the environment from 2026-03; the author stresses it is "oil volatility passing into rate volatility," not "oil to inflation to rates" |
| CH-C (two-way) | Volatility shock → CTAs and volatility-control funds sell passively → deleveraging; in reverse: volatility falls → both kinds of fund most likely buy whether the market rises or falls | Stated, 12 videos |
| CH-D (corrected) | Policy shock → long end: down in the safe-haven phase, up in the leveraged-unwind phase, up in the fiscal-expectations phase, down during a government shutdown; the step "then passes into credit" was never stated in the videos and is our inference | Stated (first half); the second half is added |
| CH-E (new) | Political or scheduled event → uncertainty → volatility-selling funds step in and out → gamma → the index; once the result lands, good or bad, uncertainty clears and volatility sellers come back | Stated, 5 videos |
| CH-F (new) | Tariffs, immigration, spending cuts → growth falls, inflation rises → rate cuts are delayed → neither the Fed nor the government supports the market → risk assets under pressure (the Fed is blocked; the long end is not rising) | Stated, strongest in 2025-03 to 06 |
| CH-G (new) | Capital spending → drains the investment-grade credit pool → squeezes non-AI borrowers such as banks, pharma and infrastructure → forces the Fed or the White House to add liquidity | Stated, 2026-07 |
| CH-H (new) | Large funding landing all at once → pulls cash from long positions → leveraged long-short momentum unwinds → semiconductors fall | Stated, 2026-06 to 10 |
| CH-I (new) | Geopolitical shipping disruption → headline inflation rises first, core is slow → after inventories run out, demand is forced down (about half a year) → overlaps in timing with credit constraints on hyperscaler capex | Stated, only in a supply-shock environment |

### Dated views (log only; give the date when citing)

- Position size: from 2024-11 to 2025-04 it came down to within 60%. From 2025-12 it is 60% to 70%; do not go fully to cash, and when short of cover, switch to more resilient stocks.
- "The Fed leans loose no matter who is chair": true only from 2025-11 to 2026-04. From 2026-05 the room for cuts shrank to about one or fewer, and hike pricing appeared.
- What to look at first once CTA buying is exhausted: before 2026-07-21, earnings; after it, credit first.
- The US dollar: strong in 2025-01, turned to medium-term depreciation on 2025-04-29, judged to be at the bottom on 2026-01-06. The stable part is that the author treats the dollar as a risk asset.
- China: background only. Stimulus brought only a rebound of 3 to 6 months (2024-06 to 2025-04). From 2025-07 the author said China is exporting deflation, which pushes down US prices.
