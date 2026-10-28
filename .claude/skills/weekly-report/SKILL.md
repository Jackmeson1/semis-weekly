---
name: weekly-report
description: Build and publish the semis-weekly far-layer report (7 channels → far/mid/near → synthesis). Use when the user says "run this week's report", "weekly report", "rerun channel C4", or in Chinese "出本周报告", "出周报", "跑一下周报", "更新这周的远端周报", "重跑某个信道".
---

# Build this week's far-layer report

Project root: the `semis-weekly/` directory that contains this skill. Python is `.venv/Scripts/python.exe`
(3.12, managed with uv); `P` below means that interpreter. Run every command from the project root.

Language: `SEMIS_LANG` in `.env` (zh or en), or pass `--lang` before the subcommand, e.g. `P -m semis --lang en prepare`.
Use the same language for every step of one issue. Below, `<lang>` is that language.

Rules live in `playbook/<lang>/playbook.md` (three-level aggregation, log formats, evidence tags). Read the files
each time; do not work from memory.

## 0. Pick the issue

The issue id is the ISO week, e.g. `2026-W44` (`semis signals` prints it on its first line). If the user gave
news or an FOMC result for this week, write it to `logs/<week>/inputs/notes.md` first (C7 reads it).

## 1. Code

```
P -m semis prepare
```

Fetches everything, computes signals (also written to signal history), builds the 7 input packets. Check the
output: for fetch failures or `na` signals, find the cause (`P -m semis status` lists unresolved failures). Do not
skip a failing source to get the report out; the report says "no data" instead. If code changed, run
`P -m unittest discover -s tests` first.

FOMC statements come out at 2pm New York time on the last meeting day and `prepare` fetches them. If you run
before that, C7 says the result is pending; once it is out, rerun `P -m semis fetch --channels C7`,
`P -m semis packet --channels C7 --run <week>`, the C7 level-1 log, then levels 2 and 3.

## 2. Level 1: seven channels, judged separately

If `logs/<week>/` already has a log for a channel (a rerun), move it to `logs/<week>/superseded/` and add the
reason to the file name.

Launch 7 Sonnet subagents in parallel (Agent tool, model: sonnet), one per channel. The whole task is:

> You are a level-1 channel analyst for the semis-weekly semiconductor report. First run this command in Bash;
> its output is your complete task. Follow it:
> `cd "<project root, posix path>" && ./.venv/Scripts/python.exe -m semis --lang <lang> prompt --run <week> --channel C<n>`

If the user only wants one channel rerun, launch only that one.

## 3. Check and record level 1

```
P -m semis check  --run <week>
P -m semis ingest --run <week>
```

When `check` lists numbers without a source, compare them with the input packet: if it is a unit conversion,
add it to `_SCALES`; if the model invented it, have that channel rewrite (SendMessage to its agent, or relaunch).
`ingest` runs `check` first and refuses to record on failure.

## 4. Levels 2 and 3: written by the main model

Follow the formats in `playbook/<lang>/aggregation.md`:

- `logs/<week>/near.md`, `mid.md`, `far.md`: each reads only the channel logs listed for it in section 1, answers
  that horizon's question, and checks the transmission chains CH-A to CH-D.
- `logs/<week>/synthesis.md`: reads only the three horizon logs and `playbook/<lang>/invariants.md`, in this order:
  roles, exception checks, invariant check, action.

Numbers come only from the logs one level down. Cite rule IDs for every conclusion. Any departure from a rule
goes under "Deviations and uncertainty" and into the json `deviation`. If a rule itself is wrong (as CAL-03 was
in 2026-W44), fix the playbook in both languages and add a change-log row.

Then run `check` and `ingest` again.

## 5. Render and publish

```
P -m semis render --run <week>
```

Read `reports/artifacts.json`. If this issue already has a URL, publish `reports/<week>.html` with the Artifact
tool and pass that `url`. Otherwise publish a new artifact (icon: `report`) and write the new URL back to
`artifacts.json`.

Reply with the link and one paragraph: the synthesis action, the three horizon states, and the one transmission
chain or signal most worth watching.

## 6. Calibration

```
P -m semis review
```

Lists judgments from 4–8 weeks ago with no recorded outcome. If there are any, list them for the user, ask
which held, then:

```
P -m semis calibrate --run <week> --item 2:near:state --outcome right|wrong|unclear --note "..."
```

## Do not

- Change thresholds in `signals/signals.yaml` without the user's approval. Changes go in its change log.
- Write the author's words or link to their posts. Use only the paraphrases already in the playbook.
- Put the contact email anywhere except the SEC User-Agent (`.env`).
