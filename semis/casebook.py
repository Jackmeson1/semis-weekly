"""Case cards: the author's reasoning in one week, next to what the data showed then and what happened after.

Cards live in private/casebook/cards/<NN>.json, one per video or post, and hold only the author's reasoning as
given. Code adds the rest, so no card sees its own outcome when it is written:
  - link states, computed for the last Friday before the video (nothing after the video is used)
  - outcomes over the next 10 and 20 trading days, as plain facts
`similar` ranks cards by how closely their link states match a given run (`match`).
"""
import datetime as dt
import json

from .chains import chain_defs, evaluate
from .config import ROOT, locale, localized, run_id
from .db import series

CASES = ROOT / 'private' / 'casebook'
LIT = {'on', 'recent'}


def friday_before(day):
    """The last Friday strictly before day: the latest data the author could have seen."""
    back = (day.weekday() - 4) % 7 or 7
    return day - dt.timedelta(days=back)


def _forward(con, sid, day, n, relative):
    rows = [r for r in series(con, sid) if r[0] >= day]
    if len(rows) <= n:
        return None
    v0, v1 = rows[0][1], rows[n][1]
    return round(100 * (v1 / v0 - 1), 1) if relative else round(100 * (v1 - v0), 0)


def _drawdown(con, sid, day, n):
    rows = [r for r in series(con, sid) if r[0] >= day][:n + 1]
    if len(rows) <= n:
        return None
    peak, worst = rows[0][1], 0.0
    for _, v in rows:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return round(100 * worst, 1)


def outcomes(con, day):
    return {'sox_10d_pct': _forward(con, 'sox', day, 10, True), 'sox_20d_pct': _forward(con, 'sox', day, 20, True),
            'sox_maxdd_20d_pct': _drawdown(con, 'sox', day, 20),
            'ust10y_20d_bp': _forward(con, 'ust10y', day, 20, False),
            'hy_oas_20d_bp': _forward(con, 'hy_oas', day, 20, False),
            'vix_10d_pts': (lambda c: None if c is None else round(c / 100, 1))(_forward(con, 'vix', day, 10, False))}


def states(con, rid):
    return {link['id']: link['status'] for c in evaluate(con, rid).values() for link in c['links']}


def _distinct():
    """One link id per distinct test: the same reading appears in several chains and should count once."""
    seen, keep = set(), []
    for c in chain_defs()['chains'].values():
        for link in c['links']:
            sig = json.dumps(link['test'], sort_keys=True)
            if sig not in seen:
                seen.add(sig)
                keep.append(link['id'])
    return keep


def build(con, language=None):
    """Write <NN>.md for every card, in the cards' language, and index.json for `similar`."""
    cards = sorted((CASES / 'cards').glob('*.json'))
    names = {link['id']: localized(link, 'name', language) for c in chain_defs()['chains'].values() for link in c['links']}
    index = []
    for f in cards:
        card = json.loads(f.read_text(encoding='utf-8'))
        day = dt.date.fromisoformat(card['date'])
        rid = run_id(friday_before(day))
        st = states(con, rid)
        out = outcomes(con, day)
        index.append({'video': card['video'], 'date': card['date'], 'data_run': rid, 'tags': card.get('tags', []),
                      'conclusion': card.get('conclusion', ''), 'states': st, 'outcomes': out})
        (CASES / f"{card['video']}.md").write_text(_render(card, rid, st, out, names, language), encoding='utf-8')
    (CASES / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    return index


def _render(card, rid, st, o, names, language):
    t = locale(language)['case']
    colon = locale(language)['ui']['colon']
    keep = _distinct()
    lit = [t['lit_item'].format(name=names[k], state=t[st[k]]) for k in keep if st.get(k) in LIT]
    unseen = list(dict.fromkeys(names[k] for k in keep if st.get(k) == 'unseen'))  # two manual checks can share a name
    fmt = lambda v, u: t['no_data'] if v is None else f'{v:+g}{u}'
    lines = [
        f"# {t['title'].format(video=card['video'], date=card['date'])}",
        '',
        t['tags'].format(tags=t['join'].join(card.get('tags', []))),
        '',
        t['data'].format(rid=rid),
        '',
        t['lit'].format(links=t['sep'].join(lit) or t['none']),
        '',
        t['unseen'].format(links=t['join'].join(unseen) or t['none']),
        '',
        t['view'],
        '',
        card.get('situation', ''),
        '',
        *[f"{i}. {s}" for i, s in enumerate(card.get('chain', []), 1)],
    ]
    for key, label in t['fields'].items():
        if card.get(key):
            lines += ['', f"**{label}**{colon}{card[key]}"]
    lines += ['', t['after'], '',
              t['sox'].format(d10=fmt(o['sox_10d_pct'], '%'), d20=fmt(o['sox_20d_pct'], '%'),
                              dd=fmt(o['sox_maxdd_20d_pct'], '%')),
              t['rates'].format(y=fmt(o['ust10y_20d_bp'], 'bp'), hy=fmt(o['hy_oas_20d_bp'], 'bp'),
                                vix=fmt(o['vix_10d_pts'], t['pts'])),
              '', t['source'].format(video=card['video'], refs=t['join'].join(card.get('refs', []))), '']
    return '\n'.join(lines)


def match(now, then, keep):
    """(overlap, agreement) between two sets of link states, over distinct links seen in both.

    overlap is shared lit links over lit links in either (two calm weeks count as 1.0); it ranks first because a
    quiet link matching a quiet link says little. agreement is the share of links in the same state, lit counting
    double; it breaks ties.
    """
    both = [k for k in keep if now.get(k) not in (None, 'unseen') and then.get(k) not in (None, 'unseen')]
    a = {k for k in both if now[k] in LIT}
    b = {k for k in both if then[k] in LIT}
    overlap = len(a & b) / len(a | b) if a | b else 1.0
    weight = {k: 2 if k in a else 1 for k in both}
    agreement = sum(w for k, w in weight.items() if (k in a) == (k in b)) / max(sum(weight.values()), 1)
    return overlap, agreement


def similar(con, rid, top=5):
    """Cards from before this run whose link states best match it."""
    now = states(con, rid)
    keep = _distinct()
    index = json.loads((CASES / 'index.json').read_text(encoding='utf-8'))
    ranked = [(*match(now, case['states'], keep), case) for case in index if case['data_run'] < rid]
    ranked.sort(key=lambda x: (-x[0], -x[1], x[2]['date']))
    return {k: now[k] for k in keep}, ranked[:top]
