# semis-weekly

[![tests](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml)

A weekly report for semiconductor investors that looks past earnings: interest rates, credit, market liquidity,
positioning and policy.

[中文说明](README.zh.md)

## Why

Earnings and industry news are everywhere. But chip stocks often move for other reasons: rates jump, borrowing
gets more expensive, or too many investors are crowded into the same trade. These forces sit further from the
companies, and few people track them every week.

Once a week this project pulls free public data, computes 15 indicators, and has AI write a one-page web report
by fixed rules. Each report answers three questions:

- Which of these forces are tightening this week, and which are not?
- What does that mean for the next two weeks, the next earnings season, and six months out?
- Should you add, hold, trim, or hedge?

## The idea

Think of macro as the brakes and earnings as the accelerator. While the brakes are off, earnings and the
industry are enough. Once the brakes are on, they decide.

Which brake matters most depends on how far ahead you look:

- **Under two weeks**: positioning. When options dealers are chasing the market and amplifying moves, good
  companies fall with everything else.
- **One earnings season**: market liquidity, the industry cycle and AI demand.
- **Six months and more**: the industry and AI demand themselves. Only a real break in funding changes the
  direction.

The framework draws on a macro trader's public commentary, organized into a rulebook in `playbook/`.

## What a report contains

- A one-line conclusion and action at the top, such as "hold, add a small hedge."
- A view for each horizon (far, mid, near) and whether they conflict.
- The weekly state of all 15 indicators over the past six months: not binding, near, or binding.
- One card per topic: credit, rates, liquidity, positioning, industry, company results, policy. Each card
  explains one concept with this week's real numbers, so you can learn macro as you read.
- Upcoming Fed meetings and Treasury auctions, and when each data series was last updated.

## How it works

1. **Fetch.** Every source is free, and most are official: the Fed's FRED database, SEC filings, the US
   Treasury, the CFTC, Cboe option data, and Taiwan companies' monthly revenue.
2. **Compute.** Code computes the indicators, so results can be checked. History uses only data that had been
   published at the time, so it never peeks at the future.
3. **Write by topic.** One AI model writes each topic and sees only that topic's data. Their notes are combined
   into far, mid and near horizons, then into one conclusion. Writing in layers means a mistake can be traced
   to one step, and that step alone can be redone.
4. **Check the numbers.** Every number in the notes must appear in the source data, or the note is rejected.
   Internal codes are not allowed either; notes use plain names.
5. **Build the page.** The page follows IBM's Carbon design system, works on phones and in dark mode, and
   shows every state with a color and a shape.

The writing guide is `playbook/en/style.md`: conclusion first, one claim per sentence, terms explained where
they first appear.

## Quick start

Requires Python 3.12 (tested with uv) and network access.

```
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # .venv/bin/python on macOS/Linux
cp .env.example .env        # set CONTACT_NAME and CONTACT_EMAIL (SEC requires them); SEMIS_LANG=en or zh
P=.venv/Scripts/python.exe
$P -m semis prepare         # fetch data, compute indicators, prepare each topic's input
$P -m semis backfill        # optional: compute the past 26 weeks
$P -m unittest discover -s tests
```

## A weekly run

The writing steps are designed for Claude Code: say "run this week's report" (or "出本周报告") and it follows
`.claude/skills/weekly-report/SKILL.md` end to end. By hand:

```
$P -m semis prepare
$P -m semis prompt --run 2026-W44 --channel C1    # the task for one AI model; one per topic, C1 to C7
$P -m semis check  --run 2026-W44                 # every number has a source, no internal codes
$P -m semis ingest --run 2026-W44                 # record the conclusions
#   then write far, mid, near and the conclusion per playbook/en/aggregation.md; check and ingest again
$P -m semis render --run 2026-W44                 # build reports/2026-W44.html
$P -m semis review                                 # calls from 4–8 weeks ago that are due for a look back
$P -m semis calibrate --run 2026-W44 --item 2:near:state --outcome right --note "..."
```

`--lang en|zh` (or `SEMIS_LANG` in `.env`) picks the language of the rulebook, the prompts and the page. One
report is in one language.

## Data sources and terms

Every source is free. Cboe's delayed option data and FinMind are public, but their terms do not clearly allow
automated fetching, so the registry marks them `check`; they are fetched once a day for personal research.

The SEC asks for a contact email in each request; that email goes only to sec.gov. Every other source gets an
honest `python-requests` user agent, which FRED requires.

## Known limitations

- **Dealer positioning is an estimate.** Option data does not say which side dealers are on, so we use the
  common industry assumption. Near the tipping point, the conclusion can flip.
- **Some data is out of reach, so proxies stand in.** There is no pre-issue trading data for Treasuries, so
  auction strength uses the bid-to-cover ratio. Implied volatility on rate options costs money, so realized
  volatility stands in.
- **Credit spread history covers only 3 years.** Percentiles rest on a short sample until local history builds
  up.
- **TSMC and ASML results are recognized from their text.** Their 6-K filings carry no item codes, so a release
  that does not mention the quarter and its results near the top would be missed.
- **Most tripwires are our own starting values.** They are reviewed against outcomes every 4–8 weeks.
- **Backfilled history uses today's data.** Later revisions cannot be undone, and option positioning has no
  history before the first snapshot.

## Layout

```
semis/        fetch, indicators, page, command line (python -m semis)
sources/      data registry (registry.yaml)
signals/      indicator definitions and tripwires (signals.yaml), with a change log
schema/       database schema (schema.sql)
playbook/     the rulebook, zh/ and en/; glossary.yaml maps internal codes to plain names
prompts/      task templates for the AI models (zh, en)
tests/        regression tests
```

Not in the repository: `.env`, `data/` (database and raw archive), `logs/`, `reports/`.

## License

MIT, see [LICENSE](LICENSE). Not investment advice.
