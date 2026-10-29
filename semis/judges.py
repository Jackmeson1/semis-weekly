"""One strong model judges the week on its own, from an index of everything it may read.

It gets INDEX.md (what each file is) and data.md (every series in one place), not a reading list, and decides what
to open. The rulebook and the past cases are one trader's reasoning, offered as reference, not rules. Two things
are kept out of the index so the judgment is its own: the rulebook's levels 2 and 3 for this week, and the case
cards from the same days (the author's current view). A person reviews the reading and makes the final call.
"""
import datetime as dt
import json
import re

from . import casebook, chains
from .config import ROOT, env, playbook_dir, registry
from .db import series

FILES = {'C1': 'C1-credit', 'C2': 'C2-rates', 'C3': 'C3-liquidity', 'C4': 'C4-positioning',
         'C5': 'C5-industry', 'C6': 'C6-company', 'C7': 'C7-policy'}
HELD_BACK_DAYS = 14  # a card this close to the run is the author's view of the same days, not a past case
WEEKS = 26
# Display units: what the database stores -> (divide by, label)
UNITS = {'usd': (1e9, '$bn'), 'usd_mn': (1e3, '$bn'), 'usd_bn': (1, '$bn'), 'twd': (1e9, 'TWD bn'),
         'pct': (1, '%'), 'index': (1, ''), 'price': (1, '$'), 'contracts': (1, 'contracts'),
         'usd_bn_per_1pct': (1, '$bn per 1% move'), 'thousands': (1, 'thousands'), 'usd_bbl': (1, '$/bbl'),
         'jpy': (1, 'yen per $')}


def judge_dir(rid):
    return ROOT / 'logs' / rid / 'judges'


def _rel(p):
    return p.relative_to(ROOT).as_posix()


def held_back(rid, cards=None):
    """Cards dated within HELD_BACK_DAYS before the run's Friday (or after it)."""
    cards = cards if cards is not None else _cards()
    edge = chains.run_date(rid) - dt.timedelta(days=HELD_BACK_DAYS)
    return [c for c in cards if dt.date.fromisoformat(c['date']) >= edge]


def _cards():
    p = casebook.CASES / 'index.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else []


def sources(rid):
    """Every file a judge may read for this run. The number check uses the same list."""
    run_dir = ROOT / 'logs' / rid
    pb = playbook_dir()
    out = [run_dir / f'{s}.md' for s in FILES.values()] + sorted((run_dir / 'inputs').glob('*.json'))
    out += [run_dir / 'inputs' / n for n in ('data.md', 'notes.md', 'INDEX.md')]
    out += [pb / n for n in ('playbook.md', 'aggregation.md', 'invariants.md', 'glossary.yaml')]
    out += sorted((pb / 'channels').glob('*.md'))
    out += [ROOT / 'sources' / 'registry.yaml', ROOT / 'signals' / 'signals.yaml', ROOT / 'signals' / 'chains.yaml']
    hold = {c['video'] for c in held_back(rid)}
    out += [casebook.CASES / f"{c['video']}.md" for c in _cards() if c['video'] not in hold]
    for p in sorted((ROOT / 'logs').glob('*/synthesis.md')):
        if p.parent.name < rid:
            out.append(p)
    return [p for p in out if p.exists()]


# ---------- data.md: every series in one place ----------

def _fmt(v, unit):
    div, _ = UNITS.get(unit, (1, unit))
    x = v / div
    return f'{x:,.0f}' if abs(x) >= 10000 else f'{x:,.1f}' if abs(x) >= 100 else f'{x:.2f}'


def _entities(con):
    return con.execute('SELECT DISTINCT series_id, entity FROM observations ORDER BY 1, 2').fetchall()


def data_md(con, rid):
    asof = chains.run_date(rid)
    reg = {s['id']: s for s in registry()['series']}
    fridays = [asof - dt.timedelta(weeks=i) for i in range(WEEKS - 1, -1, -1)]
    weekly, snaps, periodic = [], [], []
    for sid, ent in _entities(con):
        meta = reg.get(sid, {})
        rows = series(con, sid, ent, asof=asof)
        if not rows:
            continue
        col = f"{sid}{' ' + ent if ent else ''}"
        unit = meta.get('unit', '')
        if meta.get('freq') in ('quarterly', 'monthly'):
            periodic.append((meta['freq'], sid, ent, unit, rows[-(8 if meta['freq'] == 'quarterly' else 13):]))
        elif rows[0][0] <= fridays[0]:  # history covers the whole window
            vals = []
            for f in fridays:
                last = [v for d, v in rows if d <= f]
                vals.append(_fmt(last[-1], unit) if last else '')
            weekly.append((col, unit, vals))
        else:
            snaps.append((col, unit, rows[-1]))
    out = [f'# Data · {rid} (as of {asof})', '',
           'Every series in the database, read as of the run date (nothing published later). Where each comes from: '
           '`sources/registry.yaml`. Units in the headers; money is in billions.', '',
           f'## Weekly, {WEEKS} weeks: the last value on or before each date', '']
    for i in range(0, len(weekly), 8):  # eight series per table keeps rows readable
        part = weekly[i:i + 8]
        out += ['| Date | ' + ' | '.join(f'{c} ({UNITS.get(u, (1, u))[1] or u})' for c, u, _ in part) + ' |',
                '|---' * (len(part) + 1) + '|']
        out += [f'| {f} | ' + ' | '.join(v[k] for _, _, v in part) + ' |' for k, f in enumerate(fridays)]
        out.append('')
    if snaps:
        out += ['## Short history so far (the daily archive started recently)', '', '| Series | Date | Value |',
                '|---|---|---|']
        out += [f'| {c} ({UNITS.get(u, (1, u))[1] or u}) | {r[0]} | {_fmt(r[1], u)} |' for c, u, r in snaps]
        out.append('')
    for freq in ('quarterly', 'monthly'):
        groups = [p for p in periodic if p[0] == freq]
        if not groups:
            continue
        out += [f"## {freq.capitalize()}, by period end (released by {asof}; the latest version if restated)", '']
        for _, sid, ent, unit, rows in groups:
            out += [f"**{sid}{' ' + ent if ent else ''}** ({UNITS.get(unit, (1, unit))[1]}): "
                    + '; '.join(f'{d} {_fmt(v, unit)}' for d, v in rows), '']
    events = con.execute('SELECT kind, event_date, entity, payload FROM events WHERE event_date BETWEEN ? AND ? '
                         'ORDER BY 2, 1, 3', [asof - dt.timedelta(days=30), asof + dt.timedelta(days=60)]).fetchall()
    if events:
        out += ['## Events, 30 days back to 60 days ahead', '', '| Date | Kind | Entity | Detail |', '|---|---|---|---|']
        out += [f'| {d} | {k} | {e} | {_short(x)} |' for k, d, e, x in events]
        out.append('')
    return '\n'.join(out)


def _short(detail):
    if detail is None:
        return ''
    try:
        d = json.loads(detail) if isinstance(detail, str) else detail
    except ValueError:
        return str(detail)[:80]
    if isinstance(d, dict):
        # short fields only: long text (a press release) is in the channel packets
        return ', '.join(f'{k} {v}' for k, v in d.items()
                         if not isinstance(v, (dict, list)) and v not in (None, '') and len(str(v)) <= 40
                         and not re.search(r'Date|accession|exhibit|original', k))[:160]
    return str(d)[:120]


# ---------- INDEX.md ----------

def _level1(con, rid):
    rows = con.execute("SELECT scope, verdict FROM judgments WHERE run_id = ? AND level = 1 AND item = 'state'",
                       [rid]).fetchall()
    return dict(rows)


def _heads(p):
    """Section headings, leaving out the format examples inside code fences."""
    text = re.sub(r'^(`{3,}).*?^\1', '', p.read_text(encoding='utf-8'), flags=re.S | re.M)
    return [re.sub(r'^#+\s*', '', l) for l in text.splitlines() if re.match(r'^#{1,3} ', l)]


def index_md(con, rid):
    run_dir = ROOT / 'logs' / rid
    pb = playbook_dir()
    res, _ = chains.write(con, rid)
    now = {l['id']: l['status'] for c in res.values() for l in c['links']}
    keep = casebook._distinct()
    l1 = _level1(con, rid)
    out = [f'# Index · {rid} (data as of {chains.run_date(rid)})', '',
           f'Every file below can be opened; paths are relative to the project root `{ROOT.as_posix()}`. '
           'Read what you need, in any order, as deep as you like.', '',
           '## This week at a glance', '',
           '### Channel calls (level 1: one model per channel, each seeing only its own data)', '',
           '| Channel | State | One line | Log |', '|---|---|---|---|']
    for c, stem in FILES.items():
        state, _, line = (l1.get(c) or 'no log｜').partition('｜')
        p = run_dir / f'{stem}.md'
        out.append(f"| {c} | {state} | {line} | {_rel(p) if p.exists() else '—'} |")
    out += ['', '### Transmission-chain links (computed by code from the data)', '',
            'on = the test is met now; recent = met in one of the last 4 runs, not now; off = not met; '
            'unseen = no public data, judge it yourself. Full evidence: '
            f'`{_rel(run_dir / "inputs" / "chains.json")}`; tests: `signals/chains.yaml`.', '',
            '| Chain | Link | Status | Evidence |', '|---|---|---|---|']
    for cid, c in res.items():
        for l in c['links']:
            out.append(f"| {cid} {c['name']} | {l['id']} {l['name']} | {l['status']} | {l['evidence']} |")
    out += ['', '## Data', '',
            f"- `{_rel(run_dir / 'inputs' / 'data.md')}`: every series, weekly for {WEEKS} weeks; quarterly and "
            'monthly company figures; scheduled events',
            f"- `{_rel(run_dir / 'inputs')}/C1.json` to `C7.json`: each channel's computed signals, events, filings "
            'and press-release text',
            '- `signals/signals.yaml`: how each signal is computed, its thresholds, and their change log',
            '- `sources/registry.yaml`: what each series is and where it comes from']
    if (run_dir / 'inputs' / 'notes.md').exists():
        out.append(f"- `{_rel(run_dir / 'inputs' / 'notes.md')}`: news the user added this week")
    out += ['', "## Other people's reasoning (reference, not rules; you may disagree, say why)", '',
            "The rulebook was distilled from one experienced macro trader's posts and videos, 2024-05 to 2026-10. "
            'It records how they reasoned, not whether they were right.', '']
    for n in ('playbook.md', 'aggregation.md', 'invariants.md'):
        p = pb / n
        if p.exists():
            out.append(f"- `{_rel(p)}`: {' · '.join(_heads(p)[:20])}")
    out.append(f"- `{_rel(pb / 'channels')}/`: one file per channel (explainer, what the author thinks, signals, "
               'switching rules, pitfalls)')
    out.append(f"- `{_rel(pb / 'glossary.yaml')}`: plain names for every internal ID")
    cards = _cards()
    hold = held_back(rid, cards)
    past = [c for c in cards if c not in hold and c['data_run'] < rid]
    if past:
        ranked = sorted(past, key=lambda c: (*(-x for x in casebook.match(now, c['states'], keep)), c['date']))
        more = env().get('CASE_SOURCES')
        out += ['', f'### Past cases: {len(past)} weeks the trader talked through, most similar link states first', '',
                "Each card: what the links showed the Friday before, their reasoning step by step, and what happened "
                'next (facts). Overlap = lit links shared / lit links in either week.'
                + (f' Fuller notes with timestamps: `{more}/<NN>.md`.' if more else ''), '',
                '| Overlap | Card | Date | Tags | Their conclusion (start) | SOX next 20 days |', '|---|---|---|---|---|---|']
        for c in ranked:
            ov = casebook.match(now, c['states'], keep)[0]
            sox = c['outcomes'].get('sox_20d_pct')
            out.append(f"| {ov:.2f} | `{_rel(casebook.CASES / (c['video'] + '.md'))}` | {c['date']} | "
                       f"{'/'.join(c['tags'])} | {c['conclusion'][:50]}… | {'not yet' if sox is None else f'{sox:+g}%'} |")
    prev = sorted(p for p in (ROOT / 'logs').glob('*/synthesis.md') if p.parent.name < rid)
    if prev:
        out += ['', '## Past issues of this report', '']
        out += [f'- `{_rel(p)}`' for p in prev[-8:]]
    out += ['', '## Kept apart this week', '',
            f"`{_rel(run_dir)}/near.md`, `mid.md`, `far.md`, `synthesis.md` and `{_rel(judge_dir(rid))}/` are other "
            'readings of this same week'
            + (f", and {len(hold)} case card(s) from the same days are the trader's current view" if hold else '')
            + '. They are compared with yours afterwards; do not open them.', '']
    return '\n'.join(out)


def write_index(con, rid):
    d = ROOT / 'logs' / rid / 'inputs'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'data.md').write_text(data_md(con, rid), encoding='utf-8')
    (d / 'INDEX.md').write_text(index_md(con, rid), encoding='utf-8')
    return d / 'INDEX.md'
