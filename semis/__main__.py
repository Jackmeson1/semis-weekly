"""Command line entry point.

  python -m semis [--lang zh|en] prepare            fetch -> signals -> level-1 input packets (all channels)
  python -m semis prompt  --run 2026-W44 --channel C4   print the level-1 task for one channel
  python -m semis check   --run 2026-W44            every number in a log must have a source
  python -m semis ingest  --run 2026-W44            record judgments (runs check first)
  python -m semis render  --run 2026-W44            build reports/2026-W44.html
  python -m semis status                            data freshness and unresolved fetch failures

Single steps: fetch, signals, packet (all take --channels C1,C2). History: backfill, review, calibrate.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys

from . import fetch, signals
from .config import ID_RE, ROOT, lang, localized, playbook_dir, run_id, signal_defs
from .db import connect

CHANNEL_FILES = {'C1': 'C1-credit', 'C2': 'C2-rates', 'C3': 'C3-liquidity', 'C4': 'C4-positioning',
                 'C5': 'C5-industry', 'C6': 'C6-company', 'C7': 'C7-policy'}
ALL = ','.join(CHANNEL_FILES)
BASIS_EN = {'作者': 'author', '推断': 'inferred', '补充': 'added'}


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
                         'basis': BASIS_EN.get(basis, basis) if language == 'en' else basis,
                         'note': localized(d, 'note', language), 'detail': json.loads(detail),
                         'history_8w': [{'run': r, 'state': s, 'value': None if v is None else round(v, 3), 'mode': m}
                                        for r, s, v, m in hist]})
        packet = {'run_id': rid, 'language': language, 'channel': c, 'name': localized(meta, 'name', language),
                  'horizons': meta['horizons'], 'weight': meta.get('weight', 'normal'),
                  'rules_file': f'playbook/{language}/channels/{CHANNEL_FILES[c]}.md',
                  'log_file': f'logs/{rid}/{CHANNEL_FILES[c]}.md', 'signals': sigs}
        ev = _channel_events(con, c, rid)
        if ev is not None:
            packet['events'] = ev
        p = out_dir / f'{c}.json'
        p.write_text(json.dumps(packet, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
        print(f'{c}: {len(sigs)} signals -> {p.relative_to(ROOT).as_posix()}')


EXTRA = {
    'zh': {
        'C2': '- S-L1-01 是带符号的 5 日变化（v0.3）：上涨按阈值判，下跌最多 watch。下跌时讲清含义取决于原因，输入包没有原因就写没有。\n'
              '- S-L2-01 认购倍数“偏弱”需比前 6 场均值低 0.05 以上（v0.3）。拍卖日 10 年期变化为 null 时写明没判定。',
        'C3': '- 本信道权重低（作者 2025-11 起认为不必再盯 TGA）。单独 binding 也不足以判中期收紧。\n'
              '- 逆回购余额接近 0 时，讲清楚“缓冲已用完”意味着什么。',
        'C4': '- 输入包里 GEX 的 history_days 是快照天数。只有 1 天时不能说“和上周比”，要写“第一次快照”。\n'
              '- GEX 依赖做市商方向假设（客户卖 call、买 put），gamma flip 不是事实价位，要在“偏离与不确定”里说明。\n'
              '- 另加一项：按修复顺序（gamma → CTA → 长线资金），现在在第几步。',
        'C5': '- 月营收和 capex 是月度、季度数据，本周没有新数据时写“沿用上期”，注明数据日期。各公司 capex 季度不对齐，要说明。',
        'C6': '- 输入包 events.earnings_last_21d 里有新闻稿正文（text）。只从正文里取数字和管理层表述，重点是营收、毛利、capex 指引、对 AI 需求的说法。\n'
              '- 没有出现在输入包里的公司，写“最近 21 天没有业绩公告”，不要猜它们的发布日期或结果。\n'
              '- 本信道的“状态”表示财报对 C5 的问题（云厂 capex 回报、芯片需求）是加分、减分还是无信息：加分写 slack，减分写 watch 或 binding，无信息写 na。',
        'C7': '- FOMC 事件里有 statement（声明原文）时，按原文写决议和措辞变化；最近一次决议也要写，作为背景。'
              '会议已结束但没有 statement、user_notes 也没写时，写“结果待补”，不要猜。\n'
              '- 列出未来 60 天的 FOMC（标出带经济预测的那次）和未来 14 天的国债拍卖。\n'
              '- 本信道的“状态”表示有没有政策冲击在生效：没有写 slack；有但在到期前写 watch；冲击刚出现写 binding。',
    },
    'en': {
        'C2': '- S-L1-01 is the signed 5-day change (v0.3): rises are judged against the thresholds, falls are capped at '
              'watch. For a fall, explain that the meaning depends on the cause; if the packet has no cause, say so.\n'
              '- S-L2-01 counts bid-to-cover as weak only when it is at least 0.05 below the prior-6 mean (v0.3). '
              'If the 10-year change on an auction day is null, say it was not judged.',
        'C3': '- This channel is low weight (from 2025-11 the author stopped watching the TGA closely). Even binding on '
              'its own is not enough to call the mid horizon tight.\n'
              '- If the reverse repo balance is near zero, explain what an exhausted buffer means.',
        'C4': '- history_days for GEX is the number of snapshots. With 1 day you cannot compare with last week; write '
              '"first snapshot".\n'
              '- GEX rests on an assumption about dealer side (customers sell calls, buy puts); the gamma flip is not '
              'a fact. Say so under Deviations and uncertainty.\n'
              '- Add one item: in the repair sequence (gamma -> CTA -> long-only money), which step are we at.',
        'C5': '- Monthly revenue and capex are monthly and quarterly data. If nothing new arrived this week, write '
              '"carried over" with the data date. Company capex quarters do not line up; say so.',
        'C6': '- events.earnings_last_21d holds the press release text (text). Take numbers and management statements '
              'only from that text: revenue, margin, capex guidance, comments on AI demand.\n'
              '- For companies not in the packet, write "no results release in the last 21 days"; do not guess dates '
              'or results.\n'
              '- The channel state says whether results add to, subtract from, or say nothing about the C5 question '
              '(cloud capex returns, chip demand): adds = slack, subtracts = watch or binding, nothing = na.',
        'C7': '- When an FOMC event has a statement, write the decision and wording changes from the statement text; '
              'also give the most recent decision as background. If a meeting has ended with no statement and no '
              'user note, write "result pending"; do not guess.\n'
              '- List FOMC meetings in the next 60 days (mark the one with projections) and Treasury auctions in the '
              'next 14 days.\n'
              '- The channel state says whether a policy shock is in force: none = slack; in force but before expiry '
              '= watch; just appeared = binding.',
    },
}
HORIZON_LABEL = {'zh': {'near': 'near（近）', 'mid': 'mid（中）', 'far': 'far（远）'},
                 'en': {'near': 'near', 'mid': 'mid', 'far': 'far'}}


def cmd_prompt(a):
    language = lang()
    meta = signal_defs()['channels'][a.channel]
    tpl = (ROOT / 'prompts' / f'level1.{language}.md').read_text(encoding='utf-8')
    sep = '、' if language == 'zh' else ', '
    text = (tpl.replace('{name}', localized(meta, 'name', language)).replace('{channel}', a.channel)
            .replace('{run}', a.run).replace('{stem}', CHANNEL_FILES[a.channel])
            .replace('{horizons}', sep.join(HORIZON_LABEL[language][h] for h in meta['horizons']))
            .replace('{extra}', EXTRA[language].get(a.channel, '')).replace('{root_posix}', ROOT.as_posix())
            .replace('{root}', str(ROOT)).replace('{{', '{').replace('}}', '}'))
    print(text)


# ---------- check and ingest ----------

SCOPES = {**{v: (1, k) for k, v in CHANNEL_FILES.items()},
          'near': (2, 'near'), 'mid': (2, 'mid'), 'far': (2, 'far'), 'synthesis': (3, 'all')}

# Identifiers, dates and counted units are not checked as numbers.
_ID_PATTERNS = [
    r'\d{4}-\d{2}-\d{2}', r'\d{4}-W\d{2}', r'\b(?:S-L\d-\d{2}|[A-Z]{2,7}-[A-Za-z]?-?\d{2}|CH-[A-D])\b',
    r'\bL\d(?:\.\w+)?\b', r'\bC\d\b', r'\d+(?:\.\d+)?\s*(?:亿|万)?\s*(?:个交易日|个月|个季度|季|年|周|天|日|场|家)',
    r'\b\d+\s*(?:trading days?|days?|weeks?|months?|quarters?|years?|auctions?|companies|snapshots?)\b']

# Allowed unit conversions: percent <-> bp (x100, /100); Chinese 亿: $bn -> 亿 (x10), 亿 -> $bn (/10),
# dollars -> 亿 (/1e8); dollars -> $mn, $bn (/1e6, /1e9)
_SCALES = (1, 100, 0.01, 10, 0.1, 1e-6, 1e-8, 1e-9)


def _numbers_in(obj, pool):
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        pool.append(float(obj))
    elif isinstance(obj, str):
        for m in re.findall(r'-?\d+(?:\.\d+)?', obj.replace(',', '')):
            pool.append(float(m))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in(v, pool)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers_in(v, pool)


def _unmatched(log, pool):
    pool = {s * v * x for x in pool for v in (1, -1) for s in _SCALES}
    text = log.read_text(encoding='utf-8').split('```json')[0].replace(',', '')
    for pat in _ID_PATTERNS:
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
        print(f"{name}: internal IDs in the text (write the names from playbook/glossary.yaml): {', '.join(ids)}")


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


OUTCOMES = {'right': 'right', 'wrong': 'wrong', 'unclear': 'unclear', '对': 'right', '错': 'wrong', '说不清': 'unclear'}


def cmd_calibrate(a):
    con = connect()
    outcome = OUTCOMES[a.outcome]
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
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(prog='semis')
    p.add_argument('--lang', choices=['zh', 'en'], help='report language (default: SEMIS_LANG in .env, else zh)')
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
    cal.add_argument('--outcome', required=True, choices=list(OUTCOMES))
    cal.add_argument('--note')
    cal.add_argument('--threshold-change', dest='threshold_change')
    sub.add_parser('check').add_argument('--run', required=True)
    sub.add_parser('render').add_argument('--run', required=True)
    pr = sub.add_parser('prompt')
    pr.add_argument('--run', required=True)
    pr.add_argument('--channel', required=True)
    sub.add_parser('status')
    a = p.parse_args(argv)
    if a.lang:
        os.environ['SEMIS_LANG'] = a.lang
    {'fetch': cmd_fetch, 'signals': cmd_signals, 'packet': cmd_packet, 'prepare': cmd_prepare, 'prompt': cmd_prompt,
     'ingest': cmd_ingest, 'check': cmd_check, 'render': cmd_render, 'status': cmd_status,
     'review': cmd_review, 'calibrate': cmd_calibrate, 'backfill': cmd_backfill}[a.cmd](a)


if __name__ == '__main__':
    main()
