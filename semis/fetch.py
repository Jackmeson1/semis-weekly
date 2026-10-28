"""Fetch everything listed in registry.yaml and write observations / events.

observations are point-in-time: a new row is added only when the value for (series, entity, obs_date)
changes; old values are never overwritten.
"""
import csv
import datetime as dt
import html
import io
import json
import math
import re
import time
from collections import defaultdict
from urllib.parse import urlencode

from . import http
from .config import parse_date, registry

_MISSING = object()


def upsert_obs(con, s, entity, rows, first_seen, fetch_id):
    """rows: [(obs_date, value, released_at)]. Returns the number of new rows."""
    existing = dict(con.execute(
        'SELECT obs_date, value FROM obs_latest WHERE series_id = ? AND entity = ?',
        [s['id'], entity]).fetchall())
    new = []
    for d, v, released in rows:
        old = existing.get(d, _MISSING)
        if old is _MISSING or (old is None) != (v is None) or (v is not None and abs(old - v) > 1e-9):
            new.append([s['id'], entity, d, v, s['unit'], s['layer'], first_seen, released, fetch_id])
    if new:
        con.executemany('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?)', new)
    return len(new)


def fred_csv(con, s, src):
    url = src['url'].format(id=s['params']['id'])
    fid, now, body, err = http.get(con, 'fred_csv', s['id'], url, ext='csv')
    if err:
        return {'': err}
    rows = []
    for rec in csv.reader(io.StringIO(body.decode('utf-8'))):
        if len(rec) < 2 or rec[0] == 'observation_date':
            continue
        if rec[1] in ('', '.'):
            continue
        rows.append((parse_date(rec[0]), float(rec[1]), None))
    return {'': upsert_obs(con, s, '', rows, now, fid)}


TERMS = {'2-Year', '3-Year', '5-Year', '7-Year', '10-Year', '20-Year', '30-Year'}


def treasury_auctions(con, s, src):
    out = {}
    for typ in s['params']['type']:
        url = src['url'].format(type=typ, days=s['params']['days'])
        fid, now, body, err = http.get(con, 'treasurydirect_auctions', s['id'], url, entity=typ, ext='json')
        if err:
            out[typ] = err
            continue
        n = 0
        for a in json.loads(body):
            if a.get('tips') == 'Yes' or a.get('floatingRate') == 'Yes':
                continue
            if a.get('originalSecurityTerm') not in TERMS or not a.get('competitiveAuctionCloseDate'):
                continue
            day = parse_date(a['competitiveAuctionCloseDate'])
            payload = {k: a.get(k) for k in s['fields']}
            event_id = f"auction:{day}:{a.get('cusip')}"
            inserted = con.execute(
                'INSERT INTO events VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING RETURNING event_id',
                [event_id, 'auction', s['layer'], day, a['originalSecurityTerm'], json.dumps(payload), fid]
            ).fetchall()
            n += len(inserted)
        out[typ] = n
    return out


def _quarterly(units):
    """Turn SEC 3-month, year-to-date and annual facts into single quarters: {end_date: (value, filed_date)}."""
    best = {}
    for u in units:
        if 'start' not in u:
            continue
        k = (u['start'], u['end'])
        if k not in best or u['filed'] > best[k]['filed']:
            best[k] = u
    facts = list(best.values())
    span = lambda u: (parse_date(u['end']) - parse_date(u['start'])).days
    q = {}
    for u in facts:
        if 80 <= span(u) <= 100:
            q[u['end']] = (float(u['val']), u['filed'])
    by_start = defaultdict(list)
    for u in facts:
        by_start[u['start']].append(u)
    for lst in by_start.values():
        lst.sort(key=lambda u: u['end'])
        for prev, cur in zip(lst, lst[1:]):
            if cur['end'] in q:
                continue
            gap = (parse_date(cur['end']) - parse_date(prev['end'])).days
            if 80 <= gap <= 100 and span(prev) >= 80:
                q[cur['end']] = (float(cur['val']) - float(prev['val']), max(cur['filed'], prev['filed']))
    return q


def sec_concept(con, s, src, entities):
    out = {}
    for ticker, cik in entities.items():
        best_tag, best_units = None, None
        for tag in s['params']['tags']:
            url = src['url'].format(cik10=cik, tag=tag)
            fid, now, body, err = http.get(con, 'sec_concept', s['id'], url, entity=ticker, ext='json')
            if err:
                continue
            units = json.loads(body).get('units', {}).get('USD', [])
            if units and (best_units is None or max(u['end'] for u in units) > max(u['end'] for u in best_units)):
                best_tag, best_units, best_fid, best_now = tag, units, fid, now
        if best_units is None:
            out[ticker] = 'no data'
            continue
        rows = [(parse_date(end), v, dt.datetime.fromisoformat(filed))
                for end, (v, filed) in _quarterly(best_units).items()]
        out[ticker] = f'{upsert_obs(con, s, ticker, rows, best_now, best_fid)} new ({best_tag})'
    return out


def cboe_vix(con, s, src):
    fid, now, body, err = http.get(con, 'cboe_vix', s['id'], src['url'], ext='csv')
    if err:
        return {'': err}
    rows = []
    for rec in csv.reader(io.StringIO(body.decode('utf-8'))):
        if len(rec) < 5 or rec[0] == 'DATE':
            continue
        rows.append((dt.datetime.strptime(rec[0], '%m/%d/%Y').date(), float(rec[4]), None))
    return {'': upsert_obs(con, s, '', rows, now, fid)}


# ---------- GEX ----------
_OPT = re.compile(r'^([A-Z.]+?)(\d{6})([CP])(\d{8})$')
RATE = 0.04  # rough risk-free rate; only a second-order effect on the flip level


def _bs_gamma(spot, strike, t, iv):
    if t <= 0 or iv <= 0 or spot <= 0:
        return 0.0
    v = iv * math.sqrt(t)
    d1 = (math.log(spot / strike) + (RATE + iv * iv / 2) * t) / v
    return math.exp(-d1 * d1 / 2) / (math.sqrt(2 * math.pi) * spot * v)


def gex_from_chain(chain, today):
    """Return (net_gex_bn, flip, spot, n_options). Dealers are long call gamma and short put gamma
    (customers sell calls and buy puts, the SqueezeMetrics convention)."""
    data = chain['data']
    spot = float(data['current_price'])
    opts = []
    for o in data['options']:
        m = _OPT.match(o['option'])
        oi, iv = float(o.get('open_interest') or 0), float(o.get('iv') or 0)
        if not m or oi <= 0 or iv <= 0:
            continue
        expiry = dt.date(2000 + int(m.group(2)[:2]), int(m.group(2)[2:4]), int(m.group(2)[4:]))
        days = (expiry - today).days
        # The chain is treated as end-of-day data, so contracts expiring on the data date have already expired.
        # Keeping them flipped the sign of SPY net GEX on 2026-10-27 (a +$5.0bn error from at-the-money 0DTE).
        if days < 1 or days > 365:
            continue
        sign = 1.0 if m.group(3) == 'C' else -1.0
        opts.append((sign * oi * 100, int(m.group(4)) / 1000, days / 365, iv))

    def net_at(px):
        return sum(w * _bs_gamma(px, k, t, iv) for w, k, t, iv in opts) * px * px * 0.01

    grid = [spot * (0.85 + 0.005 * i) for i in range(61)]
    prof = [(px, net_at(px)) for px in grid]
    flips = []
    for (p0, g0), (p1, g1) in zip(prof, prof[1:]):
        if g0 == 0 or (g0 < 0) != (g1 < 0):
            flips.append(p0 + (p1 - p0) * (0 - g0) / (g1 - g0) if g1 != g0 else p0)
    flip = min(flips, key=lambda p: abs(p - spot)) if flips else None
    return net_at(spot) / 1e9, flip, spot, len(opts)


def cboe_chain(con, s, src):
    reg = {x['id']: x for x in registry()['series']}
    out = {}
    for ticker in s['entities']:
        url = src['url'].format(ticker=ticker)
        fid, now, body, err = http.get(con, 'cboe_chain', s['id'], url, entity=ticker, ext='json', compress=True)
        if err:
            out[ticker] = err
            continue
        chain = json.loads(body)
        last = chain['data'].get('last_trade_time') or chain.get('timestamp')
        day = parse_date(last)
        net, flip, spot, n = gex_from_chain(chain, day)
        added = upsert_obs(con, s, ticker, [(day, net, None)], now, fid)
        added += upsert_obs(con, reg['gex_flip'], ticker, [(day, flip, None)], now, fid)
        added += upsert_obs(con, reg['gex_spot'], ticker, [(day, spot, None)], now, fid)
        out[ticker] = f'{day} spot {spot:.2f} net GEX {net:+.2f}bn flip {flip and round(flip, 2)} ({n} options, {added} new)'
    return out


def cboe_iv30(con, s, src):
    out = {}
    for ticker in s['entities']:
        fid, now, body, err = http.get(con, 'cboe_iv30', s['id'], src['url'].format(ticker=ticker),
                                       entity=ticker, ext='json', compress=True)
        if err:
            out[ticker] = err
            continue
        data = json.loads(body)['data']
        day = parse_date(data.get('last_trade_time') or json.loads(body).get('timestamp'))
        iv = data.get('iv30')
        added = upsert_obs(con, s, ticker, [(day, float(iv) if iv else None, None)], now, fid)
        out[ticker] = f'{day} iv30 {iv} ({added} new)'
    return out


def cftc_tff(con, s, src):
    names = s['entities']
    where = ('market_and_exchange_names in (' + ','.join("'" + n + "'" for n in names.values()) + ')'
             " AND report_date_as_yyyy_mm_dd >= '2022-06-01'")
    url = src['url'] + '?' + urlencode({
        '$select': 'report_date_as_yyyy_mm_dd,market_and_exchange_names,lev_money_positions_long,lev_money_positions_short',
        '$where': where, '$limit': 5000})
    fid, now, body, err = http.get(con, 'cftc_tff', s['id'], url, ext='json')
    if err:
        return {'': err}
    rows = defaultdict(list)
    back = {v: k for k, v in names.items()}
    for r in json.loads(body):
        net = float(r['lev_money_positions_long']) - float(r['lev_money_positions_short'])
        rows[back[r['market_and_exchange_names']]].append((parse_date(r['report_date_as_yyyy_mm_dd']), net, None))
    return {k: upsert_obs(con, s, k, v, now, fid) for k, v in rows.items()}


def finmind(con, s, src):
    out = {}
    for sid in s['entities']:
        url = src['url'].format(dataset=s['params']['dataset'], id=sid, start='2022-01-01')
        fid, now, body, err = http.get(con, 'finmind', s['id'], url, entity=sid, ext='json')
        if err:
            out[sid] = err
            continue
        rows = []
        for r in json.loads(body).get('data', []):
            y, m = int(r['revenue_year']), int(r['revenue_month'])
            end = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
            rel = dt.datetime.fromisoformat(r['create_time']) if r.get('create_time') else None
            rows.append((end, float(r['revenue']), rel))
        out[sid] = upsert_obs(con, s, sid, rows, now, fid)
        time.sleep(0.4)
    return out


def _html_text(raw):
    t = re.sub(r'(?is)<(script|style).*?</\1>|<!--.*?-->', ' ', raw)
    t = re.sub(r'(?i)<br\s*/?>|</p>|</div>|</tr>', '\n', t)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    t = re.sub(r'[ \t\xa0]+', ' ', t)
    return re.sub(r'\n\s*\n+', '\n', t).strip()


# 6-K exhibits that look like a press release are tried first: ASML's pressreleasefinancialresul.htm
_RELEASE_NAME = re.compile(r'press|release|result|earn', re.I)
_QUARTER = re.compile(r'\b(first|second|third|fourth)[- ]quarter\b|\bQ[1-4]\b', re.I)
_RESULTS = re.compile(r'net income|net sales|earnings per|\bEPS\b|gross margin', re.I)


def _6k_candidates(names, primary):
    """HTML exhibits of a 6-K other than the cover document, likely press releases first.

    Monthly revenue reports and board notices have no exhibits, so they produce no candidates.
    """
    docs = [x for x in names if x.endswith('.htm') and x != primary and '-index' not in x]
    return sorted(docs, key=lambda x: not _RELEASE_NAME.search(x))


def _looks_like_results(text):
    head = text[:3000]
    return bool(_QUARTER.search(head) and _RESULTS.search(head))


def sec_earnings(con, s, src, since):
    """Recent results releases: 8-K Item 2.02 with its EX-99.1, or a 6-K whose exhibit is a quarterly release."""
    out = {}
    for ticker, cik in s['entities'].items():
        fid, now, body, err = http.get(con, 'sec_submissions', s['id'], src['url'].format(cik10=cik),
                                       entity=ticker, ext='json')
        if err:
            out[ticker] = err
            continue
        rec = json.loads(body)['filings']['recent']
        n = 0
        for i, form in enumerate(rec['form']):
            if rec['filingDate'][i] < str(since):
                continue
            if not (form == '8-K' and '2.02' in rec['items'][i]) and form != '6-K':
                continue
            acc = rec['accessionNumber'][i]
            event_id = f'earnings:{ticker}:{acc}'
            if con.execute('SELECT 1 FROM events WHERE event_id = ?', [event_id]).fetchone():
                continue
            base = f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace("-", "")}'
            f2, _, idx, e2 = http.get(con, 'sec_submissions', s['id'], base + '/index.json', entity=ticker, ext='json')
            names = [x['name'] for x in json.loads(idx)['directory']['item']] if idx else []
            ex, text = None, ''
            if form == '8-K':
                # Exhibit names vary by filer: ex99-1.htm, ex991.htm, exhibit991.htm, q3fy26ex991.htm
                ex = next((x for x in names if re.search(r'ex(hibit)?[-_.]?99[-_.]?0?1(?!\d)', x, re.I) and x.endswith('.htm')),
                          next((x for x in names if re.search(r'ex(hibit)?[-_.]?99', x, re.I) and x.endswith('.htm')), None))
                if ex:
                    f3, _, doc, e3 = http.get(con, 'sec_submissions', s['id'], f'{base}/{ex}', entity=ticker, ext='htm')
                    text = _html_text(doc.decode('utf-8', 'replace'))[:15000] if doc else ''
            else:
                # 6-K has no item codes: keep it only if an exhibit reads like a quarterly results release
                for name in _6k_candidates(names, rec['primaryDocument'][i])[:4]:
                    f3, _, doc, e3 = http.get(con, 'sec_submissions', s['id'], f'{base}/{name}', entity=ticker, ext='htm')
                    t = _html_text(doc.decode('utf-8', 'replace')) if doc else ''
                    if _looks_like_results(t):
                        ex, text = name, t[:15000]
                        break
                if not ex:
                    continue
            payload = {'ticker': ticker, 'form': form, 'filed': rec['filingDate'][i], 'report_date': rec['reportDate'][i],
                       'accession': acc, 'exhibit': ex, 'url': f'{base}/{ex}' if ex else base, 'text': text}
            con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING',
                        [event_id, 'earnings', s['layer'], parse_date(rec['filingDate'][i]), ticker,
                         json.dumps(payload, ensure_ascii=False), fid])
            n += 1
        out[ticker] = n
    return out


_MONTHS = ('January|February|March|April|May|June|July|August|September|October|November|December')
_MNUM = {m: i + 1 for i, m in enumerate(_MONTHS.split('|'))}


def fed_fomc(con, s, src):
    fid, now, body, err = http.get(con, 'fed_fomc', s['id'], src['url'], ext='htm')
    if err:
        return {'': err}
    t = _html_text(body.decode('utf-8', 'replace')).replace('\n', ' ')
    t = re.sub(r'\(Released[^)]*\)', ' ', t)
    n = 0
    years = sorted({int(y) for y in re.findall(r'(\d{4}) FOMC Meetings', t)}, reverse=True)[:2]
    for y in years:
        start = t.find(f'{y} FOMC Meetings')
        nxt = [t.find(f'{z} FOMC Meetings') for z in range(y - 1, y - 3, -1)]
        end = min([p for p in nxt if p > start] or [len(t)])
        for m in re.finditer(rf'({_MONTHS})(?:/({_MONTHS}))?\s+(\d{{1,2}})(?:-(\d{{1,2}}))?(\*?)', t[start:end]):
            if 'notation vote' in t[start + m.end():start + m.end() + 25].lower():
                continue
            m1, m2, d1, d2, star = m.groups()
            last = dt.date(y, _MNUM[m2 or m1], int(d2 or d1))
            first = dt.date(y, _MNUM[m1], int(d1))
            payload = {'start': str(first), 'end': str(last), 'projections': bool(star)}
            n += len(con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING RETURNING event_id',
                                 [f'fomc:{last}', 'fomc', s['layer'], last, '', json.dumps(payload), fid]).fetchall())
    return {'': n, 'statements': fomc_statements(con, s)}


# e.g. decided to raise the target range for the federal funds rate by 1/4 percentage point to 3-3/4 to 4 percent
_DECISION = re.compile(r'decided to (maintain|lower|raise) the target range for the federal funds rate'
                       r'(?: by ([\d/\-]+) percentage point)? (?:at|to) ([\d/\-]+ to [\d/\-]+ percent)')


def fomc_statements(con, s, lookback_days=45):
    """For FOMC meetings that have ended but have no statement yet, fetch the statement (monetaryYYYYMMDDa.htm)."""
    today = dt.date.today()
    got = []
    for event_id, day, payload in con.execute(
            "SELECT event_id, event_date, payload FROM events WHERE kind = 'fomc' AND event_date BETWEEN ? AND ?",
            [today - dt.timedelta(days=lookback_days), today]).fetchall():
        p = json.loads(payload)
        if p.get('statement'):
            continue
        url = f'https://www.federalreserve.gov/newsevents/pressreleases/monetary{day:%Y%m%d}a.htm'
        fid, now, body, err = http.get(con, 'fed_fomc', s['id'], url, entity=str(day), ext='htm')
        if err:
            got.append(f'{day} not published yet ({err})')
            continue
        text = re.sub(r'\s+', ' ', _html_text(body.decode('utf-8', 'replace')))
        start, end = text.find('For release at'), text.find('For media inquiries')
        statement = text[start:end].strip() if 0 <= start < end else text[:6000]
        m = _DECISION.search(statement)
        p.update({'statement': statement[:6000], 'statement_url': url,
                  'decision': m.group(1) if m else None, 'change': m.group(2) if m else None,
                  'target_range': m.group(3) if m else None})
        con.execute('UPDATE events SET payload = ? WHERE event_id = ?', [json.dumps(p, ensure_ascii=False), event_id])
        got.append(f'{day} fetched: {p["decision"]} {p["target_range"]}')
    return got


def treasury_upcoming(con, s, src):
    fid, now, body, err = http.get(con, 'treasurydirect_upcoming', s['id'], src['url'], ext='json')
    if err:
        return {'': err}
    n = 0
    for a in json.loads(body):
        if a.get('securityType') not in ('Note', 'Bond') or a.get('tips') == 'Yes' or a.get('floatingRate') == 'Yes':
            continue
        day = a.get('auctionDate') or a.get('competitiveAuctionCloseDate')
        if not day:
            continue
        payload = {k: a.get(k) for k in ('securityType', 'securityTerm', 'originalSecurityTerm', 'offeringAmount',
                                         'announcementDate', 'issueDate', 'reopening')}
        n += len(con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING RETURNING event_id',
                             [f"upcoming:{parse_date(day)}:{a.get('securityTerm')}", 'auction_upcoming', s['layer'],
                              parse_date(day), a.get('securityTerm') or '', json.dumps(payload), fid]).fetchall())
    return {'': n}


def run(con, series_ids, asof=None):
    reg = registry()
    by_id = {s['id']: s for s in reg['series']}
    asof = asof or dt.date.today()
    report = {}
    for sid in series_ids:
        s = by_id[sid]
        if s['source'] == 'derived':
            continue
        src = reg['sources'][s['source']]
        if s['source'] == 'fred_csv':
            report[sid] = fred_csv(con, s, src)
        elif s['source'] == 'treasurydirect_auctions':
            report[sid] = treasury_auctions(con, s, src)
        elif s['source'] == 'sec_concept':
            ents = s.get('entities') or by_id[s['entities_from']]['entities']
            report[sid] = sec_concept(con, s, src, ents)
        elif s['source'] == 'cboe_vix':
            report[sid] = cboe_vix(con, s, src)
        elif s['source'] == 'cboe_chain':
            report[sid] = cboe_chain(con, s, src)
        elif s['source'] == 'cftc_tff':
            report[sid] = cftc_tff(con, s, src)
        elif s['source'] == 'cboe_iv30':
            report[sid] = cboe_iv30(con, s, src)
        elif s['source'] == 'finmind':
            report[sid] = finmind(con, s, src)
        elif s['source'] == 'sec_submissions':
            report[sid] = sec_earnings(con, s, src, asof - dt.timedelta(days=21))
        elif s['source'] == 'fed_fomc':
            report[sid] = fed_fomc(con, s, src)
        elif s['source'] == 'treasurydirect_upcoming':
            report[sid] = treasury_upcoming(con, s, src)
        else:
            report[sid] = {'': f"source {s['source']} is not implemented"}
    return report
