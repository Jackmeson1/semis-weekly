# semis-weekly

[![tests](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml)

A weekly "far-layer" report for semiconductor investing. Earnings and industry data are easy to find; this
system covers the layers further out — credit, rates, liquidity plumbing, positioning and policy — and decides,
week by week, which of them is actually binding.

[中文说明](README.zh.md)

The judgment rules are distilled from three years of public posts by a macro trader on X (who is not
identified here). The core idea taken from them: the far layers are **constraints**, the near layers are the
**objective**. When the constraints are slack, earnings and the industry decide direction; when a constraint
binds, it vetoes, and which layer gets the final say depends on the horizon.

## How it works

```
sources/registry.yaml       22 series and event feeds, every endpoint tested
   ↓ fetch (raw responses archived; option chains gzipped)
schema/schema.sql           DuckDB: raw_fetch → observations (point-in-time) → events
   ↓ code computes 15 signals from signals/signals.yaml
signals, signal_history     value and state (slack / watch / binding / na) per signal per week
   ↓ level 1: one model per channel, reading only that channel (playbook/<lang>/channels/)
logs/<week>/C1…C7           7 channel logs: evidence, horizon implications, an explainer
   ↓ level 2: far / mid / near (playbook/<lang>/aggregation.md), including a transmission-chain check
logs/<week>/near, mid, far
   ↓ level 3: synthesis (aggregation.md + invariants.md)
logs/<week>/synthesis.md
   ↓ render
reports/<week>.html         the weekly page
   ↓ 4–8 weeks later
calibration                 record what held and which thresholds should move
```

- **Code computes, models judge.** Fetching, cleaning and signals are deterministic and reproducible. Models
  only read the results, decide, and write logs.
- **Each level reads only the level below.** If one level is wrong you can trace it and rerun just that level
  and the ones above it. A single channel can be rerun on its own.
- **Every number has a source.** `semis check` verifies that each number in a log appears in its input packet
  (or the logs one level down), allowing for rounding and unit conversions. `ingest` refuses logs that fail.
- **Written for a reader, not a checker.** Logs follow `playbook/<lang>/style.md`: conclusion first, one claim
  per sentence, terms explained where they first appear. Signal and rule IDs stay in the json for tracing; the
  text uses the names in `playbook/glossary.yaml`, and `check` rejects IDs anywhere the page shows them.
- **Point-in-time.** Observations keep their first-seen and release times; backfilled signals never see a
  quarterly or monthly report that was published later.

## Channels

| Channel | Data | Signals |
|---|---|---|
| C1 Credit | FRED ICE BofA spreads; SEC cloud capex and operating cash flow | S-L3-01/02/03 |
| C2 Rates | FRED yields and curve; TreasuryDirect auctions | S-L1-01/02/03, S-L2-01 |
| C3 Liquidity plumbing (low weight) | FRED Fed assets, TGA, reverse repo | S-L2-02 |
| C4 Positioning | Cboe VIX; GEX computed from Cboe option chains (SPY, QQQ, SMH); CFTC TFF | S-L4-01/02/03/04 |
| C5 Industry | FinMind monthly revenue for TSMC and the Taiwan AI-server chain; SEC cloud capex | S-L5-01/02/03 |
| C6 Company results | SEC 8-K Item 2.02 and the EX-99.1 press release (11 US companies); 6-K results releases (TSMC, ASML) | model reads the release |
| C7 Policy and events | FOMC calendar and statements (fetched after each meeting); upcoming auctions; optional user notes | model reads statements and calendar |

TLT 30-day implied vol is archived daily but not yet a signal; it becomes a C2 proxy for swaption vol once
there is enough history.

## Quick start

Requires Python 3.12 (tested with uv) and network access.

```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # .venv/bin/python on macOS/Linux
cp .env.example .env        # set CONTACT_NAME and CONTACT_EMAIL (SEC requires them); SEMIS_LANG=en or zh
P=.venv/Scripts/python.exe
$P -m semis prepare         # fetch -> signals -> level-1 input packets for all channels
$P -m semis backfill        # optional: 26 weeks of signal history
$P -m unittest discover -s tests
```

## A weekly run

The model steps are designed for Claude Code: `.claude/skills/weekly-report/SKILL.md` runs the whole flow
when you say "run this week's report" (or "出本周报告"). By hand:

```
$P -m semis prepare
$P -m semis prompt --run 2026-W44 --channel C1    # give this to one model per channel (C1..C7)
$P -m semis check  --run 2026-W44
$P -m semis ingest --run 2026-W44
#   levels 2 and 3: write near/mid/far.md and synthesis.md following playbook/<lang>/aggregation.md
$P -m semis check  --run 2026-W44
$P -m semis ingest --run 2026-W44
$P -m semis render --run 2026-W44                 # reports/2026-W44.html
$P -m semis review                                 # judgments from 4–8 weeks ago awaiting an outcome
$P -m semis calibrate --run 2026-W44 --item 2:near:state --outcome right --note "..."
```

`--lang en|zh` (or `SEMIS_LANG` in `.env`) picks the playbook, prompts and page language. One issue is
produced in one language.

## Data sources and terms

All sources are free. Most are official (FRED, SEC EDGAR, TreasuryDirect, Federal Reserve, CFTC). Cboe
delayed option chains and FinMind are public but their terms are marked `check` in the registry; they are
fetched once a day for personal research. The SEC contact email is sent only to sec.gov; every other source
gets an honest `python-requests` User-Agent (FRED drops requests that don't carry it).

## Known limitations

- GEX depends on an assumption about which side dealers are on (customers sell calls and buy puts). Near the
  flip, the sign can change. Contracts expiring on the data date are excluded.
- No when-issued yields, so auction weakness is approximated with bid-to-cover and the 10-year move.
- Swaption implied vol is not free; realized 10-year vol stands in for now.
- ICE BofA spreads on FRED only go back 3 years, so percentiles have a short sample until local history builds up.
- 6-K filings carry no item codes, so TSMC and ASML results are recognized by their exhibit text; a release
  that does not mention a quarter and a results line in its opening would be missed.
- Most thresholds are initial values marked "added"; the calibration log is how they get fixed.
- Backfilled history uses the current data vintage; revisions cannot be restored. GEX has no history before the first snapshot.

The page follows IBM Carbon (type scale, spacing, tokens, tiles, tags, data tables), with the UK Analysis
Function chart guidance for sparklines. Every state pairs a color with a shape, so nothing relies on color alone.

## Layout

```
semis/        fetch, signals, render, CLI (python -m semis)
sources/      registry.yaml
signals/      signals.yaml (thresholds and change log)
schema/       schema.sql
playbook/     zh/ and en/: playbook, invariants, aggregation, style, channels/C1–C7; glossary.yaml
prompts/      level-1 prompt templates (zh, en)
tests/        regression tests
```

Not in the repository: `.env`, `data/` (database and raw archive), `logs/`, `reports/`.

## License

MIT, see [LICENSE](LICENSE). Not investment advice.
