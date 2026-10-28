# Distant-Horizon Ordinal Playbook (draft v0.2, 2026-10-28)

The author: a macro trader who writes publicly on X; this playbook does not identify them.

These are the judgment rules the model follows when it writes the weekly report. They are distilled from the author's 3,271 posts between 2024-01 and 2026-10 (the research process is not published with this repository). Code computes all numbers according to `signals/signals.yaml`; the model only reads the results and does not compute anything itself.

## Three-level aggregation

The author judges in layers and by time horizon, so the report does too. It aggregates level by level rather than mixing everything at once.

| Level | What it does | What it reads | Rule file | Output |
|---|---|---|---|---|
| 1 Channel | Judge each channel on its own | Only that channel's signals | `channels/C1`–`C7` | 7 files such as `logs/<week>/C1-credit.md` |
| 2 Horizon | Summarize far, mid and near separately | Only level 1 logs | `aggregation.md`, section 1 | `logs/<week>/near.md`, `mid.md`, `far.md` |
| 3 Synthesis | Resolve conflicts across horizons and give the action implication | Only level 2 and `invariants.md` | `aggregation.md`, section 2 | `logs/<week>/synthesis.md` |

- Each level reads only the conclusions of the level below. When level 3 cites a signal, it must also cite the channel log that interprets it.
- If a level gets something wrong, fix that level's log and rerun the levels above it.
- Each channel can be rerun on its own. For example, to update only credit this week, run C1, then levels 2 and 3.

## The seven channels

| Channel | Name | Layer | Main horizon | Signals |
|---|---|---|---|---|
| C1 | Credit | L3.credit | Mid; since 2026 also affects the far-horizon direction | S-L3-01/02/03 |
| C2 | Rates | L1.long_end, L2.treasury_issuance | Near, mid | S-L1-01/02/03, S-L2-01 |
| C3 | Liquidity plumbing | L2 | Mid | S-L2-02 |
| C4 | Positioning | L4 | Near | S-L4-01/02/03/04 |
| C5 | Industry | L5 | Far | S-L5-01/02/03 |
| C6 | Companies and earnings | L6 | Mid | No automatic signal in v1; read the earnings calendar |
| C7 | Policy and events | L1.fed_path, L1.fiscal_politics, L0.geopolitics | Mid | No automatic signal in v1; read the calendar |

Every channel file has the same structure and doubles as teaching material:
1. **Explainer**: what the channel measures and why it transmits to semiconductors. This part was added during the research; it is not the author's view.
2. **What the author thinks**: relevant views and rules (all paraphrased).
3. **Signals**: which signals the channel uses and where the thresholds come from.
4. **Switching rules**: trigger conditions the author has used.
5. **Common pitfalls**.
6. **What to write in this week's log**: the fixed fields.

## Channel log format

Every level 1 log uses this skeleton. The final json block is read into the `judgments` table by `python -m semis ingest`, so field names must not change.

````markdown
# C1 Credit · 2026-W44

**State**: Near
**One line**: ……

## Evidence
| Signal | This period | Prior period | Threshold | State |
|---|---|---|---|---|
| S-L3-03 Hyperscaler capex / operating cash flow | 0.847 | 0.768 (last quarter) | 0.8 / 1.0 | Near |

Rules: INF-02, VETO-01 (not triggered)

## Horizon implications
- Mid: ……
- Far: ……

## Change vs last week
……

## Explainer
Use this week's numbers to explain what the channel measures, in 3–5 sentences, for learning purposes.

## Deviations and uncertainty
…… Write "None" if there are none.

```json
{"level": 1, "scope": "C1", "state": "watch", "verdict": "one line", "horizons": {"mid": "……", "far": "……"},
 "signal_refs": ["S-L3-03"], "rule_refs": ["INF-02"], "deviation": "", "confidence": "medium", "model": "sonnet"}
```
````

- `state` must be one of `slack` / `watch` / `binding` / `na`. The page shows them as Not binding / Near / Binding / No data.
- A channel's `state` is the model's synthesis of that channel's signals. It is usually the most severe one, but it may be raised or lowered with a reason, and the reason goes in `deviation`.
- `horizons` lists only the horizons the channel covers (see channels in signals.yaml).
- Numbers must come from the input package. Do not compute new ones.
- The VETO, NOVETO, INF, ACT and CAL numbers mentioned in channel files are defined in `aggregation.md`, section 2. When writing a level 1 log you may read those tables for reference, but cite only the rules relevant to your channel and make no cross-channel judgments.

## Evidence tags

- **Stated**: the author wrote it explicitly.
- **Inferred**: derived from the author's reasoning or from statistics on their positions.
- **Added**: not the author's; added during the research. A report that cites such a rule must say so.

You may deviate from a rule, but the log's deviation section must say which rule and why.

The author's posts are research material. New posts by the author that are not in the playbook do not take effect automatically; a human must confirm them before the playbook is changed.

## Layer codes

| Layer | Meaning |
|---|---|
| L0 | Long-term structure: AI/token demand, compute bottlenecks, size of US debt, geopolitics |
| L1 | Macro policy: long-end rates, speed of rate moves, Fed path, policy shocks |
| L2 | Liquidity plumbing: Treasury issuance and auctions, net liquidity, TGA, reverse repo |
| L3 | Cross-asset: credit spreads, hyperscaler funding, the dollar, the yen, oil |
| L4 | Positioning and flows: gamma, CTA, hedge fund leverage, volatility |
| L5 | Industry: hyperscaler capex, capacity, memory cycle, model-company revenue |
| L6 | Companies: EPS, gross margin, guidance, valuation |
| L7 | Sentiment and narrative: bubble talk, FOMO |

## Files

```
playbook/
  playbook.md        this page
  invariants.md      four invariants INV-01–04
  channels/
    C1-credit.md  C2-rates.md  C3-liquidity.md  C4-positioning.md
    C5-industry.md  C6-company.md  C7-policy.md
  aggregation.md     aggregation rules for levels 2 and 3: horizon grouping, veto table, trade-offs, actions, calibration
```

## Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-10-28 | First draft, single file |
| 0.2 | 2026-10-28 | Split into three-level aggregation (channel, horizon, synthesis); added explainers to channel files |
| 0.3 | 2026-10-28 | Added the channel log format; added horizon and synthesis log formats and the transmission-chain check to aggregation.md; restored CAL-03 to its original definition (rate volatility and credit spreads both at watch); fixed the wording of the GEX dealer-direction convention in C4 |
