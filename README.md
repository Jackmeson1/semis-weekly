# semis-weekly

[![tests](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/Jackmeson1/semis-weekly/actions/workflows/tests.yml)

A weekly report for semiconductor investors that looks past earnings: interest rates, credit, market liquidity,
positioning and policy.

## What is missing

Chip stocks often move for reasons other than earnings: rates jump, borrowing gets more expensive, or too many
investors are crowded into the same trade. Most of what you can find does not help with that:

- **Free information is almost all about earnings and the industry.** Data on rates, credit, liquidity and
  positioning sits in paid terminals or is scattered across commentary.
- **Commentary gives conclusions, not tradeoffs.** When rising rates and strong AI demand show up together,
  which one wins? Why is the answer different at two weeks and at six months? Few people say.
- **Dashboards just lay the data out.** Dozens of charts side by side, with no word on which one matters this
  week.
- **AI-written market summaries are dense and hard to read.** And their numbers are not always traceable.

## What this project adds

- **Free data only, with stand-ins for paid data.** Dealer gamma (which way options dealers must hedge) is
  usually a paid feed; here it is computed from Cboe's public delayed option data. Single-company credit
  insurance prices are out of reach, so market-wide credit spreads stand in.
- **Tradeoffs written down as rules.** Which factor decides at each horizon, what can overturn the direction
  and what cannot: all of it is in the rulebook in `playbook/`, where each rule can be checked and changed.
- **One call each week.** Which forces are tightening, what that means for the next two weeks, the next
  earnings season and six months out, and whether to add, hold, trim or hedge.
- **Written for people, and checkable.** The analysis is written in layers, every number must appear in the
  source data, and the text carries no internal codes.
- **Something to learn from.** Every topic explains one concept with this week's real numbers.

## The idea

Think of macro as the brakes and earnings as the accelerator. While the brakes are off, earnings and the
industry are enough. Once the brakes are on, they decide. Which brake matters most depends on how far ahead you
look. Here is how the system is built, in five layers.

![A one-minute walk through the five layers](docs/img/explainer.gif)

### Layer 1: seven channels, each reading only its own data

Macro is messy, so it is split into seven channels. Each answers one question and writes its own call. No channel
is swayed by another, and when one goes wrong, only that one is redone. The seven calls then feed the far, mid
and near horizons.

![The seven channels, their data sources, and which horizon each one feeds](docs/img/channels.svg)

### Layer 2: who decides at each horizon

The same data means different things at two weeks and at six months. Under two weeks, positioning outweighs
everything: when options dealers chase the market, good companies fall with everything else. Over one earnings
season, credit, liquidity, the industry and AI demand carry equal weight. Beyond six months, the industry, AI
demand and Treasury supply decide. The Fed's rate-cut path ranks last everywhere, because it has to reach long
rates and liquidity before it moves stocks.

![Who decides at each horizon](docs/img/horizons.svg)

### Layer 3: what can overturn the direction, and what cannot

The far horizon sets the direction, starting from the premise that AI demand does not peak. Only four things can
override it. A funding break is the only one that changes the direction: credit tightens while cloud companies
spend more than they earn. The other three only call a pause. The four on the right are common bearish arguments
that cannot overturn the direction under these rules.

![Four things that can overturn the direction, and four that cannot](docs/img/vetoes.svg)

### Layer 4: how channels pass pressure along

The channels are judged separately, so none of them sees pressure passing from one to another. Nine known chains
are written down as data in `signals/chains.yaml`, each a list of links with a test, such as "rate volatility
rising", then "credit spreads widening", then "chip stocks sold". Code marks every link as on, recently on, off,
or not visible in public data. If the upstream end has tightened and the downstream end has not moved yet, the
chain is "transmitting." That early warning is what separate judgments miss.

![Four of the transmission chains and their state in 2026-W44](docs/img/chains.svg)

### Layer 5: three horizons, one action

The far horizon sets the direction, the mid horizon sets position size and hedging, and the near horizon sets the
timing. When they disagree, they are not averaged; each decides its own part. Three exceptions are checked last:
Is funding blocked? Is strong industry data hiding a funding risk? Are rate volatility and credit spreads in
trouble at the same time?

![How the three horizons combined into one action in 2026-W44](docs/img/action.svg)

## What a report contains

- A one-line conclusion and action at the top, such as "hold, add a small hedge."
- A view for each horizon (far, mid, near) and whether they conflict.
- The weekly state of all 15 indicators over the past six months: not binding, near, or binding.
- One card per topic: credit, rates, liquidity, positioning, industry, company results, policy. Each card
  explains one concept with this week's real numbers, so you can learn macro as you read.
- Upcoming Fed meetings and Treasury auctions, and when each data series was last updated.

## How it works

![Pipeline: data, indicators, three levels of judgment, and the number check](docs/img/pipeline.svg)

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

## A daily fetch

Some data can only be saved on the day it is published, such as option chains and implied volatility. So besides
the weekly report, fetch once every weekday:

```
$P -m semis daily        # fetch everything once; the report is appended to data/fetch-logs/<date>.log
```

On Windows, use Task Scheduler and run it after the US close on weekdays (pythonw.exe opens no window):

```powershell
$root = "<project folder>"
$action = New-ScheduledTaskAction -Execute "$root\.venv\Scripts\pythonw.exe" -Argument '-m semis daily' -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '14:30'   # local time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName 'semis-weekly daily fetch' -Action $action -Trigger $trigger -Settings $settings
```

On macOS or Linux, use cron: `30 21 * * 1-5 cd <project folder> && .venv/bin/python -m semis daily` (UTC).

## A weekly run

The writing steps are designed for Claude Code: say "run this week's report" and it follows
`.claude/skills/weekly-report/SKILL.md` end to end. By hand:

```
$P -m semis prepare
$P -m semis prompt --run 2026-W44 --channel C1    # the task for one AI model; one per topic, C1 to C7
$P -m semis check  --run 2026-W44                 # every number has a source, no internal codes
$P -m semis ingest --run 2026-W44                 # record the conclusions
$P -m semis chains --run 2026-W44                 # the state of every chain link
$P -m semis cases  --run 2026-W44                 # past cases whose link states look most like this week
$P -m semis index  --run 2026-W44                 # an index of every file a model may read, and every series in one table
$P -m semis prompt --run 2026-W44 --judge <name>  # the task for one strong model to judge the whole week from that index
#   then write far, mid, near and the conclusion per playbook/en/aggregation.md; check and ingest again
$P -m semis render --run 2026-W44                 # build reports/2026-W44.html
$P -m semis review                                 # calls from 4–8 weeks ago that are due for a look back
$P -m semis calibrate --run 2026-W44 --item 2:near:state --outcome right --note "..."
```

Everything language-specific lives in one folder, `playbook/<lang>/`: the rulebook, the style guide, the
glossary, the level-1 prompt template (`prompt-level1.md`) and the page text (`locale.yaml`). English ships here.
Past cases are cards you write yourself, one per week you want to learn from: the reasoning of someone whose
judgment you trust, as they gave it. They go in `private/casebook/cards/` (git-ignored); `semis cases --build`
adds what the data showed the Friday before and what happened in the next 20 trading days. None ship here.

To run in another language, add a folder (`private/playbook/<lang>/` is git-ignored for one you keep local) and
pass `--lang <lang>` or set `SEMIS_LANG` in `.env`. One report is in one language.

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
semis/        fetch, indicators, chain links, past cases, page, command line (python -m semis)
sources/      data registry (registry.yaml)
signals/      indicator definitions and tripwires (signals.yaml), with a change log; chains (chains.yaml)
schema/       database schema (schema.sql)
playbook/en/  everything in English: rulebook, style guide, glossary, prompt template, page text (locale.yaml)
tests/        regression tests
docs/         the README diagrams, generated by python docs/figures.py
video/        the animated explainer above, made with Remotion (npm install, then npm run render)
```

Not in the repository: `.env`, `data/` (database and raw archive), `logs/`, `reports/`, `private/`.

## Acknowledgments

The framework draws on a macro trader's public commentary.

## License

MIT, see [LICENSE](LICENSE). Not investment advice.
