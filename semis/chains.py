"""Compute the status of every transmission-chain link (signals/chains.yaml) for a weekly run.

Status comes from data only: on, recent (met in one of the previous runs, not now), off, or unseen.
"""
import datetime as dt
import json
from functools import lru_cache

import yaml

from .config import ROOT
from .db import series
from .signals import THREE_YEARS, _pct_rank

RANK = {'slack': 0, 'watch': 1, 'binding': 2}


@lru_cache
def chain_defs():
    return yaml.safe_load((ROOT / 'signals' / 'chains.yaml').read_text(encoding='utf-8'))


def run_date(rid):
    """The Friday of an ISO week, capped at today: the date a run's data is read as of."""
    y, w = rid.split('-W')
    return min(dt.date.fromisocalendar(int(y), int(w), 5), dt.date.today())


def _signal_state(con, rid, sid):
    row = con.execute('SELECT state, value FROM signal_history WHERE run_id = ? AND signal_id = ?', [rid, sid]).fetchone()
    return (row[0], row[1]) if row else ('na', None)


def _series_change(con, sid, asof, n, relative):
    rows = series(con, sid, asof=asof)
    if len(rows) <= n + 260:
        return None, None
    vals = [v for _, v in rows[-(THREE_YEARS + n):]]
    if relative:
        changes = [100 * (vals[i] / vals[i - n] - 1) for i in range(n, len(vals)) if vals[i - n]]
    else:
        changes = [100 * (vals[i] - vals[i - n]) for i in range(n, len(vals))]
    return changes[-1], _pct_rank(changes, changes[-1])


def _test(con, t, rid, asof, conv):
    """Return (met: True/False/None, evidence: str). None means the link cannot be seen."""
    if 'any' in t or 'all' in t:
        parts = [_test(con, x, rid, asof, conv) for x in t.get('any', t.get('all'))]
        seen = [p for p in parts if p[0] is not None]
        ev = '; '.join(p[1] for p in parts)
        if not seen:
            return None, ev
        return (any(p[0] for p in seen) if 'any' in t else all(p[0] for p in seen)), ev
    if 'manual' in t:
        return None, f"manual: {t['manual']}"
    if 'signal' in t:
        state, value = _signal_state(con, rid, t['signal'])
        if state == 'na':
            return None, f"{t['signal']} no data"
        v = '' if value is None else f' {value:.3g}'
        return RANK.get(state, 0) >= RANK[t['state']], f"{t['signal']} {state}{v}"
    if 'series' in t:
        chg, pct = _series_change(con, t['series'], asof, t['change'], t.get('relative'))
        if chg is None:
            return None, f"{t['series']} not enough history"
        unit = '%' if t.get('relative') else 'bp'
        ev = f"{t['series']} {t['change']}d {chg:+.1f}{unit}, 3y pct {pct:.0f}"
        if 'pct_at_least' in t:
            return pct >= t['pct_at_least'], ev
        return pct <= t['pct_at_most'], ev
    if 'ratio' in t:
        a, b = (series(con, s, asof=asof) for s in t['ratio'])
        if not a or not b:
            return None, f"{t['ratio'][0]}/{t['ratio'][1]} no data"
        r = a[-1][1] / b[-1][1]
        return r >= t['at_least'], f"{t['ratio'][0]}/{t['ratio'][1]} {r:.2f} ({a[-1][0]})"
    if 'event' in t:
        n = t['within_days']
        rows = con.execute('SELECT event_date FROM events WHERE kind = ? AND event_date BETWEEN ? AND ?',
                           [t['event'], asof - dt.timedelta(days=n), asof + dt.timedelta(days=n)]).fetchall()
        return bool(rows), (f"{t['event']} {', '.join(str(r[0]) for r in rows)}" if rows else f"no {t['event']} within {n}d")
    raise ValueError(f'unknown test {t}')


def evaluate(con, rid):
    defs = chain_defs()
    conv = defs['conventions']
    runs = [r[0] for r in con.execute('SELECT DISTINCT run_id FROM signal_history WHERE run_id <= ? ORDER BY run_id DESC',
                                      [rid]).fetchall()][:conv['recent_runs'] + 1]
    out = {}
    for cid, c in defs['chains'].items():
        links = []
        for link in c['links']:
            now, ev = _test(con, link['test'], rid, run_date(rid), conv)
            past = [(r, *_test(con, link['test'], r, run_date(r), conv)) for r in runs[1:]]
            hit = [r for r, met, _ in past if met]
            if now is None:
                status = 'unseen'
            elif now:
                status = 'on'
            elif hit:
                status = 'recent'
            else:
                status = 'off'
            links.append({'id': link['id'], 'name': link['name'], 'status': status, 'evidence': ev,
                          'recent_runs_met': hit})
        out[cid] = {'name': c['name'], 'basis': c.get('basis'), 'links': links,
                    'count': {s: sum(l['status'] == s for l in links) for s in ('on', 'recent', 'off', 'unseen')}}
    return out


def write(con, rid):
    res = evaluate(con, rid)
    path = ROOT / 'logs' / rid / 'inputs' / 'chains.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'run_id': rid, 'as_of': str(run_date(rid)), 'chains': res}, ensure_ascii=False, indent=1),
                    encoding='utf-8')
    return res, path
