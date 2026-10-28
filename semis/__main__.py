"""Command line entry point.

  python -m semis [--lang en] prepare               fetch -> signals -> level-1 input packets (all channels)
  python -m semis prompt  --run 2026-W44 --channel C4   print the level-1 task for one channel
  python -m semis check   --run 2026-W44            every number in a log must have a source
  python -m semis ingest  --run 2026-W44            record judgments (runs check first)
  python -m semis render  --run 2026-W44            build reports/2026-W44.html
  python -m semis status                            data freshness and unresolved fetch failures
  python -m semis daily                             fetch everything once, log to data/fetch-logs/ (for a scheduler)

Single steps: fetch, signals, packet (all take --channels C1,C2). History: backfill, review, calibrate.
"""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import sys
import traceback

from . import fetch, signals
from .config import ID_RE, ROOT, lang, locale, localized, playbook_dir, run_id, signal_defs
from .db import connect

CHANNEL_FILES = {'C1': 'C1-credit', 'C2': 'C2-rates', 'C3': 'C3-liquidity', 'C4': 'C4-positioning',
                 'C5': 'C5-industry', 'C6': 'C6-company', 'C7': 'C7-policy'}
ALL = ','.join(CHANNEL_FILES)


def _channels(arg):
    return [c.strip() for c in arg.split(',') if c.strip()]


def _series_for(channels):
    defs = signal_defs()
    by_id = {s['id']: s for s in defs['signals']}
    out = []
    for c in channels:
        inputs = [i for sid in defs['channels'][c]['signals'] for i in by_id[sid]['inputs']]
        inputs += defs['channels'][c].get('inputs', []) + defs['channels'][c].get('archive', [])
        for inp in inputs:
            if inp not in out:
                out.append(inp)
    return out


def cmd_fetch(a):
    con = connect()
    for sid, res in fetch.run(con, _series_for(_channels(a.channels))).items():
        print(f'{sid:18s} {res}')


def cmd_daily(a):
    """Fetch every source once and append the report to data/fetch-logs/<date>.log. Meant for a scheduled task:
    option chains and implied vol can only be archived on the day they are published, so run it every weekday."""
    log = ROOT / 'data' / 'fetch-logs' / f'{dt.date.today()}.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    failed = False
    with open(log, 'a', encoding='utf-8') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        print(f'--- {dt.datetime.now():%Y-%m-%d %H:%M:%S} daily fetch')
        try:
            cmd_fetch(argparse.Namespace(channels=ALL))
        except Exception:
            traceback.print_exc()
            failed = True
    print(f'-> {log.relative_to(ROOT)}')
    if failed:
        sys.exit(1)


def cmd_signals(a):
    con = connect()
    asof = dt.date.fromisoformat(a.asof) if a.asof else dt.date.today()
    rid, results = signals.compute(con, _channels(a.channels), asof)
    print(f'run {rid}  as of {asof}')
    for sid, name, value, state, data_asof in results:
        v = '—' if value is None else f'{value:,.3f}'
        print(f'  {sid}  {state:8s} {v:>12s}  data to {data_asof}  {name}')


# ---------- level-1 input packets ----------

def _events(con, kind, start, end):
    return [{'date': str(d), 'entity': e, **json.loads(p)} for d, e, p in con.execute(
        'SELECT event_date, entity, payload FROM events WHERE kind = ? AND event_date BETWEEN ? AND ? '
        'ORDER BY event_date', [kind, start, end]).fetchall()]


def _channel_events(con, c, rid):
    today = dt.date.today()
    if c == 'C6':
        return {'earnings_last_21d': _events(con, 'earnings', today - dt.timedelta(days=21), today),
                'note': 'Results releases: 8-K Item 2.02 (text is the EX-99.1 press release) and 6-K results exhibits for '
                        'TSM (NT$) and ASML (EUR); first 15000 characters. Keep each company in its own currency.'}
    if c == 'C7':
        notes = ROOT / 'logs' / rid / 'inputs' / 'notes.md'
        return {'fomc': _events(con, 'fomc', today - dt.timedelta(days=60), today + dt.timedelta(days=60)),
                'auctions_next_14d': _events(con, 'auction_upcoming', today, today + dt.timedelta(days=14)),
                'user_notes': notes.read_text(encoding='utf-8') if notes.exists() else None,
                'note': 'When an fomc event has a statement, the statement text is authoritative (decision, change and '
                        'target_range are parsed from it by code). If a meeting has ended with no statement and no '
                        'user note, write that the result is pending.'}
    return None


def cmd_packet(a):
    con = connect()
    defs = signal_defs()
    by_id = {s['id']: s for s in defs['signals']}
    rid = a.run or run_id(dt.date.today())
    language = lang()
    out_dir = ROOT / 'logs' / rid / 'inputs'
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = con.execute('SELECT signal_id, as_of, value, state, detail FROM signals WHERE run_id = ?', [rid]).fetchall()
    for c in _channels(a.channels):
        meta = defs['channels'][c]
        sigs = []
        for sid, as_of, value, state, detail in rows:
            if sid not in meta['signals']:
                continue
            d = by_id[sid]
            hist = con.execute('SELECT run_id, state, value, mode FROM signal_history WHERE signal_id = ? AND run_id < ? '
                               'ORDER BY run_id DESC LIMIT 8', [sid, rid]).fetchall()
            basis = d.get('basis')
            sigs.append({'id': sid, 'name': localized(d, 'name', language), 'state': state, 'value': value,
                         'data_as_of': str(as_of), 'thresholds': d.get('thresholds'),
                         'basis': locale(language).get('basis', {}).get(basis, basis),
                         'note': localized(d, 'note', language), 'detail': json.loads(detail),
                         'history_8w': [{'run': r, 'state': s, 'value': None if v is None else round(v, 3), 'mode': m}
                                        for r, s, v, m in hist]})
        packet = {'run_id': rid, 'language': language, 'channel': c, 'name': localized(meta, 'name', language),
                  'horizons': meta['horizons'], 'weight': meta.get('weight', 'normal'),
                  'rules_file': (playbook_dir(language) / 'channels' / f'{CHANNEL_FILES[c]}.md').relative_to(ROOT).as_posix(),
                  'log_file': f'logs/{rid}/{CHANNEL_FILES[c]}.md', 'signals': sigs}
        ev = _channel_events(con, c, rid)
        if ev is not None:
            packet['events'] = ev
        p = out_dir / f'{c}.json'
        p.write_text(json.dumps(packet, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
        print(f'{c}: {len(sigs)} signals -> {p.relative_to(ROOT).as_posix()}')


def cmd_prompt(a):
    """The level-1 task for one channel: the language's prompt-level1.md with its per-channel notes filled in."""
    language = lang()
    meta = signal_defs()['channels'][a.channel]
    pb = playbook_dir(language)
    tpl = (pb / 'prompt-level1.md').read_text(encoding='utf-8')
    loc = locale(language)['prompt']
    text = (tpl.replace('{name}', localized(meta, 'name', language)).replace('{channel}', a.channel)
            .replace('{run}', a.run).replace('{stem}', CHANNEL_FILES[a.channel])
            .replace('{horizons}', loc['enum_sep'].join(loc['horizons'][h] for h in meta['horizons']))
            .replace('{extra}', loc['notes'].get(a.channel, '')).replace('{playbook}', str(pb))
            .replace('{root_posix}', ROOT.as_posix()).replace('{root}', str(ROOT))
            .replace('{{', '{').replace('}}', '}'))
    print(text)


# ---------- check and ingest ----------

SCOPES = {**{v: (1, k) for k, v in CHANNEL_FILES.items()},
          'near': (2, 'near'), 'mid': (2, 'mid'), 'far': (2, 'far'), 'synthesis': (3, 'all')}

# Identifiers, dates and counted units are not checked as numbers.
_ID_PATTERNS = [
    r'\d{4}-\d{2}-\d{2}', r'\d{4}-W\d{2}', r'\b(?:S-L\d-\d{2}|[A-Z]{2,7}-[A-Za-z]?-?\d{2}|CH-[A-D])\b',
    r'\bL\d(?:\.\w+)?\b', r'\bC\d\b',
    r'\b\d+\s*(?:trading days?|days?|weeks?|months?|quarters?|years?|auctions?|companies|snapshots?)\b']
# A language adds its own counted units in locale.yaml (check.counted_units)

# Allowed unit conversions: percent <-> bp (x100, /100); $bn <-> units of 1e8 (x10, /10), which some languages
# count in; dollars -> 1e8 units, $mn, $bn (/1e8, /1e6, /1e9)
_SCALES = (1, 100, 0.01, 10, 0.1, 1e-6, 1e-8, 1e-9)


def _numbers_in(obj, pool):
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        pool.append(float(obj))
    elif isinstance(obj, str):
        for m in re.findall(r'-?\d+(?:\.\d+)?', obj.replace(',', '')):
            pool.append(float(m))
        # Fed statements write rates as fractions: "3-3/4 to 4 percent", "by 1/4 percentage point"
        for whole, num, den in re.findall(r'(?<![\d/])(?:(\d+)-)?(\d+)/(\d+)(?![\d/])', obj):
            if int(den):
                pool.append(int(whole or 0) + int(num) / int(den))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in(v, pool)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers_in(v, pool)


def _unmatched(log, pool):
    pool = {s * v * x for x in pool for v in (1, -1) for s in _SCALES}
    text = log.read_text(encoding='utf-8').split('```json')[0].replace(',', '')
    for pat in _ID_PATTERNS + [p for p in [locale().get('check', {}).get('counted_units')] if p]:
        text = re.sub(pat, ' ', text, flags=re.I)
    out = []
    for m in re.finditer(r'(?<![\w.])-?\d+(?:\.(\d+))?', text):
        n, dec = float(m.group(0)), len(m.group(1) or '')
        if not any(abs(round(x, dec) - n) < 1e-9 for x in pool):
            out.append(m.group(0))
    return out


def _ids_shown(text):
    """Internal IDs a reader would see: in the prose, and in the json strings the page displays.
    signal_refs, rule_refs and input_refs are for tracing and may hold IDs; so may json keys."""
    shown = [text.split('```json')[0]]
    blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.S)
    try:
        j = json.loads(blocks[-1]) if blocks else {}
    except ValueError:
        j = {}

    def walk(o):
        if isinstance(o, str):
            shown.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk({k: v for k, v in j.items() if k not in ('signal_refs', 'rule_refs', 'input_refs')})
    return sorted({m.group(0) for t in shown for m in ID_RE.finditer(t)})


def _report(name, bad, ids=()):
    print(f"{name}: {'every number has a source' if not bad else 'numbers without a source: ' + ', '.join(sorted(set(bad)))}")
    if ids:
        print(f"{name}: internal IDs in the text (write the names from the glossary): {', '.join(ids)}")


def cmd_check(a):
    """Every number in a level-1 log must appear in its input packet or rule files (rounding, sign and the unit
    conversions above are allowed). Numbers in level-2 and level-3 logs must appear in the logs one level down."""
    run_dir = ROOT / 'logs' / a.run
    pb = playbook_dir()
    bad_total = 0
    rules = [pb / 'playbook.md', pb / 'aggregation.md', pb / 'invariants.md']
    upper = [(run_dir / f'{s}.md', 2) for s in ('near', 'mid', 'far')] + [(run_dir / 'synthesis.md', 3)]
    for log, level in upper:
        if not log.exists():
            continue
        pool = []
        lower = [run_dir / f'{s}.md' for s in CHANNEL_FILES.values()]
        if level == 3:
            lower += [run_dir / f'{s}.md' for s in ('near', 'mid', 'far')]
        for f in lower + rules:
            if f.exists():
                _numbers_in(f.read_text(encoding='utf-8'), pool)
        bad, ids = _unmatched(log, pool), _ids_shown(log.read_text(encoding='utf-8'))
        bad_total += len(bad) + len(ids)
        _report(log.name, bad, ids)
    for c, stem in CHANNEL_FILES.items():
        log, packet = run_dir / f'{stem}.md', run_dir / 'inputs' / f'{c}.json'
        if not log.exists() or not packet.exists():
            continue
        pool = []
        _numbers_in(json.loads(packet.read_text(encoding='utf-8')), pool)
        for f in (pb / 'channels' / f'{stem}.md', pb / 'playbook.md'):
            if f.exists():
                _numbers_in(f.read_text(encoding='utf-8'), pool)
        bad, ids = _unmatched(log, pool), _ids_shown(log.read_text(encoding='utf-8'))
        bad_total += len(bad) + len(ids)
        _report(log.name, bad, ids)
    sys.exit(1 if bad_total else 0)


def cmd_ingest(a):
    if not a.force:
        try:
            cmd_check(a)
        except SystemExit as e:
            if e.code:
                print('Check failed: numbers without a source or internal IDs in the text. Fix the logs first '
                      '(or pass --force if you have checked them).')
                sys.exit(1)
    con = connect()
    run_dir = ROOT / 'logs' / a.run
    for p in sorted(run_dir.glob('*.md')):
        if p.stem not in SCOPES:
            continue
        level, scope = SCOPES[p.stem]
        text = p.read_text(encoding='utf-8')
        blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.S)
        if not blocks:
            print(f'{p.name}: no json judgment block, skipped')
            continue
        j = json.loads(blocks[-1])
        head = 'action' if level == 3 else 'state'
        items = [(head, j[head] + '｜' + j['verdict'])]
        for key, prefix in (('horizons', 'horizon'), ('chains', 'chain'), ('invariants', 'invariant')):
            items += [(f'{prefix}:{k}', v) for k, v in (j.get(key) or {}).items()]
        for item, verdict in items:
            con.execute('INSERT OR REPLACE INTO judgments VALUES (?,?,?,?,?,?,?,?,?,?)',
                        [a.run, level, scope, item, verdict, j.get('signal_refs') or [],
                         j.get('rule_refs') or [], j.get('input_refs') or [], j.get('deviation') or None,
                         j.get('confidence')])
        con.execute('INSERT OR REPLACE INTO logs VALUES (?,?,?,?,?,?,?)',
                    [a.run, level, scope, p.relative_to(ROOT).as_posix(),
                     hashlib.sha256(text.encode('utf-8')).hexdigest(), dt.datetime.now(), j.get('model')])
        print(f'{p.name}: level {level} {scope}, {len(items)} judgments recorded')


# ---------- history and calibration ----------

def cmd_backfill(a):
    con = connect()
    done = signals.backfill(con, a.weeks)
    print(f'backfilled {len(done)} weeks: {done[-1]} to {done[0]}')
    for sid, n, na in con.execute("SELECT signal_id, count(*), count(*) FILTER (WHERE state = 'na') FROM signal_history "
                                  'GROUP BY 1 ORDER BY 1').fetchall():
        print(f'  {sid}  {n} weeks, {na} without data')


def cmd_review(a):
    """List judgments from 4 to 8 weeks ago that have no outcome recorded yet."""
    con = connect()
    today = dt.date.today()
    lo, hi = run_id(today - dt.timedelta(weeks=8)), run_id(today - dt.timedelta(weeks=4))
    rows = con.execute("""
        SELECT j.run_id, j.level, j.scope, j.item, j.verdict FROM judgments j
        WHERE j.run_id BETWEEN ? AND ? AND j.item IN ('state', 'action') AND NOT EXISTS (
          SELECT 1 FROM calibration c WHERE c.run_id = j.run_id
            AND c.item = CAST(j.level AS VARCHAR) || ':' || j.scope || ':' || j.item)
        ORDER BY j.run_id, j.level DESC, j.scope""", [lo, hi]).fetchall()
    if not rows:
        print(f'nothing to review between {lo} and {hi}')
    for rid, level, scope, item, verdict in rows:
        print(f'{rid}  {level}:{scope}:{item}  {verdict}')


OUTCOMES = ('right', 'wrong', 'unclear')


def cmd_calibrate(a):
    con = connect()
    outcome = {**{o: o for o in OUTCOMES}, **locale().get('outcomes', {})}.get(a.outcome)
    if outcome is None:
        sys.exit(f'--outcome must be one of {", ".join(OUTCOMES)}')
    con.execute('INSERT OR REPLACE INTO calibration VALUES (?,?,?,?,?,?)',
                [a.run, a.item, dt.date.today(), outcome, a.note, a.threshold_change])
    print(f'recorded {a.run} {a.item}: {outcome}')


# ---------- pipeline ----------

def cmd_prepare(a):
    """The code half in one step: fetch -> signals -> level-1 packets. Models write the logs after this."""
    cmd_fetch(a)
    cmd_signals(a)
    a.run = run_id(dt.date.fromisoformat(a.asof) if a.asof else dt.date.today())
    cmd_packet(a)
    print(f'\nnext: level 1 writes logs/{a.run}/C*.md, then check -> ingest -> levels 2 and 3 -> check -> ingest -> render')


def cmd_render(a):
    from .render import render
    con = connect()
    out = ROOT / 'reports' / f'{a.run}.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(con, a.run), encoding='utf-8')
    print(f'-> {out.relative_to(ROOT).as_posix()}')


def cmd_status(a):
    con = connect()
    print('data freshness:')
    for sid, ent, last, n in con.execute(
            'SELECT series_id, entity, max(obs_date), count(*) FROM obs_latest GROUP BY 1, 2 ORDER BY 1, 2').fetchall():
        print(f'  {sid:16s} {ent:10s} latest {last}  {n} rows')
    for kind, last, n in con.execute('SELECT kind, max(event_date), count(*) FROM events GROUP BY 1').fetchall():
        print(f'  event {kind:16s} latest {last}  {n} rows')
    # A failure is resolved if the same series succeeded within 10 minutes (SEC tag probing returns 404 by design)
    # or at any later time.
    errs = con.execute("""
        SELECT f.series_id, f.entity, f.error, f.retrieved_at FROM raw_fetch f
        WHERE f.error IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM raw_fetch s WHERE s.series_id = f.series_id AND s.entity = f.entity
            AND s.error IS NULL AND s.retrieved_at BETWEEN f.retrieved_at - INTERVAL 10 MINUTE
                                                 AND f.retrieved_at + INTERVAL 10 MINUTE)
          AND NOT EXISTS (
          SELECT 1 FROM raw_fetch s WHERE s.series_id = f.series_id AND s.entity = f.entity
            AND s.error IS NULL AND s.retrieved_at > f.retrieved_at)
        ORDER BY f.retrieved_at DESC LIMIT 10""").fetchall()
    print('unresolved fetch failures:' if errs else 'no unresolved fetch failures')
    for e in errs:
        print('  ', *e)


def main(argv=None):
    if sys.stdout:  # None under pythonw.exe, which the scheduled task uses
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(prog='semis')
    p.add_argument('--lang', help='report language: a folder in playbook/ or private/playbook/ '
                                   '(default: SEMIS_LANG in .env, else en)')
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('fetch', 'signals', 'packet', 'prepare'):
        s = sub.add_parser(name)
        s.add_argument('--channels', default=ALL)
        if name in ('signals', 'prepare'):
            s.add_argument('--asof')
        if name == 'packet':
            s.add_argument('--run')
    ing = sub.add_parser('ingest')
    ing.add_argument('--run', required=True)
    ing.add_argument('--force', action='store_true')
    sub.add_parser('review')
    sub.add_parser('backfill').add_argument('--weeks', type=int, default=26)
    cal = sub.add_parser('calibrate')
    cal.add_argument('--run', required=True)
    cal.add_argument('--item', required=True, help='e.g. 2:near:state, 3:all:action, 1:C4:state')
    cal.add_argument('--outcome', required=True, help='right, wrong or unclear')
    cal.add_argument('--note')
    cal.add_argument('--threshold-change', dest='threshold_change')
    sub.add_parser('check').add_argument('--run', required=True)
    sub.add_parser('render').add_argument('--run', required=True)
    pr = sub.add_parser('prompt')
    pr.add_argument('--run', required=True)
    pr.add_argument('--channel', required=True)
    sub.add_parser('status')
    sub.add_parser('daily')
    a = p.parse_args(argv)
    if a.lang:
        os.environ['SEMIS_LANG'] = a.lang
    {'fetch': cmd_fetch, 'signals': cmd_signals, 'packet': cmd_packet, 'prepare': cmd_prepare, 'prompt': cmd_prompt,
     'ingest': cmd_ingest, 'check': cmd_check, 'render': cmd_render, 'status': cmd_status,
     'review': cmd_review, 'calibrate': cmd_calibrate, 'backfill': cmd_backfill, 'daily': cmd_daily}[a.cmd](a)


if __name__ == '__main__':
    main()
