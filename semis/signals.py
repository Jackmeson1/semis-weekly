"""Compute the signals defined in signals.yaml and write them to the signals table.
Models never compute numbers themselves; they only read these results."""
import datetime as dt
import json
import statistics

from .config import registry, run_id as make_run_id, signal_defs
from .db import series

THREE_YEARS = 756  # trading days


def state_up(value, th):
    if value is None:
        return 'na'
    b, w = th.get('binding'), th.get('watch')
    if b is not None and value >= b:
        return 'binding'
    if w is not None and value >= w:
        return 'watch'
    return 'slack'


def _quantile(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def _change(rows, lag, scale=100.0):
    if len(rows) <= lag:
        return None, {}
    (d1, v1), (d0, v0) = rows[-1], rows[-1 - lag]
    return (v1 - v0) * scale, {'from': [str(d0), v0], 'to': [str(d1), v1]}


def change_signal(con, d, asof, series_id, lag, absolute=False):
    rows = series(con, series_id, asof=asof)
    value, detail = _change(rows, lag)
    prev, _ = _change(rows[:-5], lag) if len(rows) > lag + 5 else (None, {})
    if absolute and value is not None:
        detail['signed_bp'] = round(value, 2)
        value = abs(value)
        prev = None if prev is None else abs(prev)
    detail['unit'] = 'bp'
    detail['window'] = f'{lag} trading days'
    detail['prev_week_value'] = None if prev is None else round(prev, 2)
    return value, state_up(value, d['thresholds']), detail, rows[-1][0] if rows else None


def rate_vol(con, d, asof):
    rows = series(con, 'ust10y', asof=asof)
    diffs = [(rows[i][1] - rows[i - 1][1]) * 100 for i in range(1, len(rows))]
    if len(diffs) < 40:
        return None, 'na', {'note': 'not enough data'}, None
    roll = lambda end: statistics.stdev(diffs[end - 19:end + 1])
    n = len(diffs)
    hist = [roll(i) for i in range(max(19, n - THREE_YEARS), n)]
    cur, prev = roll(n - 1), roll(n - 6)
    p75, p90 = _quantile(hist, 0.75), _quantile(hist, 0.90)
    state = 'binding' if cur >= p90 else 'watch' if cur >= p75 else 'slack'
    detail = {'unit': 'bp/day', 'pct_3y': round(100 * sum(h <= cur for h in hist) / len(hist), 1),
              'p75_3y': round(p75, 2), 'p90_3y': round(p90, 2), 'prev_week_value': round(prev, 2),
              'history_obs': len(hist)}
    return cur, state, detail, rows[-1][0]


def capex_ocf(con, d, asof):
    ents = next(s for s in registry()['series'] if s['id'] == 'csp_capex')['entities']
    per, cap_sum, ocf_sum, prev_cap, prev_ocf, latest = {}, 0.0, 0.0, 0.0, 0.0, None
    for t in ents:
        cap = dict(series(con, 'csp_capex', t, asof=asof))
        ocf = dict(series(con, 'csp_ocf', t, asof=asof))
        common = sorted(set(cap) & set(ocf))
        if len(common) < 5 or (common[-1] - common[-4]).days > 300:
            per[t] = 'not enough consecutive quarters'
            continue
        last4, prev4 = common[-4:], common[-5:-1]
        c, o = sum(cap[x] for x in last4), sum(ocf[x] for x in last4)
        cap_sum, ocf_sum = cap_sum + c, ocf_sum + o
        prev_cap += sum(cap[x] for x in prev4)
        prev_ocf += sum(ocf[x] for x in prev4)
        latest = max(latest or common[-1], common[-1])
        per[t] = {'quarters': f'{last4[0]} → {last4[-1]}', 'capex_4q_bn': round(c / 1e9, 1),
                  'ocf_4q_bn': round(o / 1e9, 1), 'ratio': round(c / o, 3)}
    if not ocf_sum:
        return None, 'na', {'companies': per}, None
    value = cap_sum / ocf_sum
    detail = {'companies': per, 'capex_4q_bn': round(cap_sum / 1e9, 1), 'ocf_4q_bn': round(ocf_sum / 1e9, 1),
              'prev_quarter_value': round(prev_cap / prev_ocf, 3) if prev_ocf else None,
              'note': 'fiscal years differ; each company uses its own latest 4 quarters'}
    return value, state_up(value, d['thresholds']), detail, latest


AUCTION_TERMS = {'2-Year', '5-Year', '7-Year', '10-Year', '20-Year', '30-Year'}
MIN_BTC_GAP = 0.05  # v0.3: bid-to-cover must sit at least this far below the prior-6 mean to count as weak


def rate_speed(con, d, asof):
    """S-L1-01 is directional: rises use watch/binding; falls are capped at watch."""
    value, state, detail, data_asof = change_signal(con, d, asof, 'ust10y', 5)
    if value is None:
        return value, state, detail, data_asof
    th = d['thresholds']
    if value >= 0:
        state = state_up(value, th)
    else:
        state = 'watch' if -value >= th['watch'] else 'slack'
        detail['direction_note'] = 'falling: capped at watch; the meaning depends on the cause'
    detail['direction'] = 'up' if value >= 0 else 'down'
    return value, state, detail, data_asof


def auctions(con, d, asof):
    start = asof - dt.timedelta(days=6)
    rows = con.execute(
        "SELECT event_date, entity, payload FROM events WHERE kind = 'auction' "
        'AND event_date BETWEEN ? AND ? ORDER BY event_date', [start, asof]).fetchall()
    y10 = series(con, 'ust10y', asof=asof)
    y10_by_day = dict(y10)
    out, flags = [], []
    for day, term, payload in rows:
        if term not in AUCTION_TERMS:
            continue
        p = json.loads(payload)
        btc = float(p['bidToCoverRatio'])
        hist = [float(json.loads(h[0])['bidToCoverRatio']) for h in con.execute(
            "SELECT payload FROM events WHERE kind = 'auction' AND entity = ? AND event_date < ? "
            'ORDER BY event_date DESC LIMIT 6', [term, day]).fetchall()]
        weak = None
        if len(hist) >= 3:
            mean = statistics.mean(hist)
            weak = btc < mean - statistics.stdev(hist) and mean - btc >= MIN_BTC_GAP
        jump_bp = None
        if day in y10_by_day:
            before = [v for dd, v in y10 if dd < day]
            if before:
                jump_bp = round((y10_by_day[day] - before[-1]) * 100, 1)
        jump = None if jump_bp is None else jump_bp >= 5
        flags.append((bool(weak), bool(jump)))
        out.append({'date': str(day), 'term': term, 'security': p.get('securityTerm'),
                    'high_yield': p.get('highYield'), 'bid_to_cover': btc,
                    'btc_prev6_mean': round(statistics.mean(hist), 2) if hist else None,
                    'btc_prev6_std': round(statistics.stdev(hist), 2) if len(hist) >= 2 else None,
                    'weak': weak, 'y10_change_bp': jump_bp, 'jump': jump})
    if not out:
        return 0, 'slack', {'note': f'no 2/5/7/10/20/30-year auctions between {start} and {asof}'}, asof
    state = ('binding' if any(w and j for w, j in flags)
             else 'watch' if any(w or j for w, j in flags) else 'slack')
    detail = {'auctions': out}
    if any(a['y10_change_bp'] is None for a in out):
        detail['note'] = 'the 10-year close for some auction days is not out yet (FRED lags a day); jump not judged'
    return sum(w or j for w, j in flags), state, detail, max(r[0] for r in rows)


def _asof_value(rows, day):
    """rows ascending; return the latest value on or before day."""
    best = None
    for d, v in rows:
        if d > day:
            break
        best = v
    return best


def net_liquidity(con, d, asof):
    """S-L2-02: Wednesday levels, assets - TGA - reverse repo, in $bn."""
    assets = series(con, 'fed_assets', asof=asof)
    tga = dict(series(con, 'tga', asof=asof))
    rrp = series(con, 'on_rrp', asof=asof)
    pts = []
    for day, a in assets:
        if day in tga:
            r = _asof_value(rrp, day)
            if r is not None:
                pts.append((day, (a - tga[day]) / 1000 - r))
    if len(pts) < 6:
        return None, 'na', {'note': 'not enough data'}, None
    (d1, n1), (d0, n0), (dp, npv) = pts[-1], pts[-5], pts[-6]
    value = n1 - n0
    th = d['thresholds']
    state = 'binding' if value <= th['binding'] else 'watch' if value <= th['watch'] else 'slack'
    detail = {'unit': '$bn', 'window': '4 weeks', 'net_liquidity_bn': round(n1, 1), 'from': [str(d0), round(n0, 1)],
              'to': [str(d1), round(n1, 1)], 'prev_week_value': round(pts[-2][1] - npv, 1),
              'components_latest_bn': {'assets': round(assets[-1][1] / 1000, 1),
                                       'tga': round(tga.get(d1, 0) / 1000, 1),
                                       'on_rrp': round(_asof_value(rrp, d1), 3)}}
    return value, state, detail, d1


def _pct_rank(hist, x):
    return 100 * sum(h <= x for h in hist) / len(hist)


def vix_calm(con, d, asof):
    rows = series(con, 'vix', asof=asof)
    if len(rows) < 260:
        return None, 'na', {'note': 'not enough data'}, None
    hist = [v for _, v in rows[-THREE_YEARS:]]
    pct = _pct_rank(hist, rows[-1][1])
    state = 'watch' if pct <= d['thresholds']['watch'] else 'slack'
    return pct, state, {'unit': '3-year percentile', 'vix': rows[-1][1], 'prev_week_value': round(_pct_rank(hist, rows[-6][1]), 1),
                        'note': 'watch only: low volatility means low tolerance for shocks, not a sell signal'}, rows[-1][0]


def vix_shock(con, d, asof):
    rows = series(con, 'vix', asof=asof)
    if len(rows) < 6:
        return None, 'na', {'note': 'not enough data'}, None
    v, chg = rows[-1][1], rows[-1][1] - rows[-6][1]
    state = 'binding' if v >= 25 or chg >= 6 else 'watch' if v >= 20 or chg >= 4 else 'slack'
    return v, state, {'unit': 'VIX', 'change_5d': round(chg, 2), 'prev_week_value': rows[-6][1],
                      'rule': 'binding: VIX>=25 or +6 in 5 days; watch: VIX>=20 or +4 in 5 days'}, rows[-1][0]


def gex_state(con, d, asof):
    per, net, day, near_flip = {}, 0.0, None, []
    for t in ('SPY', 'QQQ', 'SMH'):
        g = series(con, 'gex', t, asof=asof)
        f = dict(series(con, 'gex_flip', t, asof=asof))
        sp = dict(series(con, 'gex_spot', t, asof=asof))
        if not g:
            per[t] = 'no data'
            continue
        gd, gv = g[-1]
        flip, spot = f.get(gd), sp.get(gd)
        dist = None if flip is None or not spot else round(100 * (spot - flip) / spot, 2)
        per[t] = {'date': str(gd), 'net_gex_bn_per_1pct': round(gv, 2), 'spot': spot,
                  'flip': None if flip is None else round(flip, 2), 'spot_vs_flip_pct': dist,
                  'history_days': len(g), 'used_in_state': t != 'SMH'}
        if t != 'SMH':
            net += gv
            day = max(day or gd, gd)
            if dist is not None and abs(dist) <= 1.5:
                near_flip.append(t)
    if day is None:
        return None, 'na', {'tickers': per}, None
    state = 'binding' if net < 0 else 'watch' if near_flip else 'slack'
    return net, state, {'unit': '$bn per 1% move (SPY+QQQ)', 'tickers': per, 'near_flip': near_flip,
                        'assumption': 'customers sell calls and buy puts (SqueezeMetrics convention)'}, day


def cftc_pct(con, d, asof):
    per, flags, day = {}, [], None
    for t in ('SPX', 'NDX'):
        rows = series(con, 'cftc_net', t, asof=asof)
        if len(rows) < 52:
            per[t] = 'not enough data'
            continue
        hist = [v for _, v in rows[-156:]]
        pct = _pct_rank(hist, rows[-1][1])
        per[t] = {'date': str(rows[-1][0]), 'net_contracts': rows[-1][1], 'pct_3y': round(pct, 1),
                  'prev_week_pct': round(_pct_rank(hist, rows[-2][1]), 1)}
        day = rows[-1][0]
        th = d['thresholds']
        if pct <= th['watch_low']:
            flags.append(f'{t} crowded short')
        elif pct >= th['watch_high']:
            flags.append(f'{t} crowded long')
    if day is None:
        return None, 'na', {'contracts': per}, None
    value = per['SPX']['pct_3y'] if isinstance(per.get('SPX'), dict) else None
    return value, ('watch' if flags else 'slack'), {
        'unit': '3-year percentile (SPX)', 'contracts': per, 'flags': flags,
        'note': 'low percentile = crowded short (the author reads this as hard to fall far); Tuesday positions, published Friday'}, day


def _month_end(y, m):
    return dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)


def _rolling3_yoy(rows):
    """rows: [(month_end, value)]. Returns [(month_end, 3-month rolling year-over-year %)]."""
    by = dict(rows)
    out = []
    for day, _ in rows:
        months = [_month_end(day.year - (day.month - k <= 0), (day.month - k - 1) % 12 + 1) for k in range(3)]
        year_ago = [_month_end(m.year - 1, m.month) for m in months]
        if all(m in by for m in months + year_ago):
            out.append((day, 100 * (sum(by[m] for m in months) / sum(by[m] for m in year_ago) - 1)))
    return out


def _yoy_signal(rows, label):
    yoy = _rolling3_yoy(rows)
    if len(yoy) < 3:
        return None, 'na', {'note': 'not enough data'}, None
    (d2, y2), (d1, y1), (d0, y0) = yoy[-1], yoy[-2], yoy[-3]
    falling = y2 < y1 < y0
    return y2, ('watch' if falling else 'slack'), {
        'unit': '% (3-month rolling YoY)', 'series': label, 'last3': [[str(d0), round(y0, 1)], [str(d1), round(y1, 1)],
                                                                [str(d2), round(y2, 1)]],
        'prev_month_value': round(y1, 1), 'rule': 'watch after 2 consecutive monthly declines'}, d2


def tsmc_yoy(con, d, asof):
    return _yoy_signal(series(con, 'tsmc_rev', '2330', asof=asof), 'TSMC')


def chain_yoy(con, d, asof):
    ents = next(s for s in registry()['series'] if s['id'] == 'tw_ai_chain_rev')['entities']
    per = [dict(series(con, 'tw_ai_chain_rev', e, asof=asof)) for e in ents]
    common = sorted(set.intersection(*(set(p) for p in per))) if per else []
    rows = [(m, sum(p[m] for p in per)) for m in common]
    value, state, detail, day = _yoy_signal(rows, '+'.join(ents))
    detail['companies'] = ents
    return value, state, detail, day


def capex_yoy(con, d, asof):
    ents = next(s for s in registry()['series'] if s['id'] == 'csp_capex')['entities']
    now_sum, ago_sum, per, latest = 0.0, 0.0, {}, None
    for t in ents:
        q = series(con, 'csp_capex', t, asof=asof)
        if not q:
            continue
        last_d, last_v = q[-1]
        ago = [(dd, v) for dd, v in q if 350 <= (last_d - dd).days <= 380]
        if not ago:
            per[t] = 'missing the year-ago quarter'
            continue
        now_sum += last_v
        ago_sum += ago[-1][1]
        latest = max(latest or last_d, last_d)
        per[t] = {'quarter': str(last_d), 'capex_bn': round(last_v / 1e9, 1), 'year_ago_bn': round(ago[-1][1] / 1e9, 1),
                  'yoy_pct': round(100 * (last_v / ago[-1][1] - 1), 1)}
    if not ago_sum:
        return None, 'na', {'companies': per}, None
    value = 100 * (now_sum / ago_sum - 1)
    state = 'watch' if value < d['thresholds']['watch'] else 'slack'
    return value, state, {'unit': '% (sum of each company latest quarter, YoY)', 'companies': per,
                          'now_bn': round(now_sum / 1e9, 1), 'year_ago_bn': round(ago_sum / 1e9, 1)}, latest


IMPL = {
    'S-L3-01': lambda con, d, a: change_signal(con, d, a, 'hy_oas', 20),
    'S-L3-02': lambda con, d, a: change_signal(con, d, a, 'ig_oas', 20),
    'S-L3-03': capex_ocf,
    'S-L1-01': rate_speed,
    'S-L1-02': rate_vol,
    'S-L1-03': lambda con, d, a: change_signal(con, d, a, 'ust2s10s', 20, absolute=True),
    'S-L2-01': auctions,
    'S-L2-02': net_liquidity,
    'S-L4-01': vix_calm,
    'S-L4-02': vix_shock,
    'S-L4-03': gex_state,
    'S-L4-04': cftc_pct,
    'S-L5-01': tsmc_yoy,
    'S-L5-02': chain_yoy,
    'S-L5-03': capex_yoy,
}


def _one(con, defs, by_id, c, sid, asof):
    d = by_id[sid]
    if sid in IMPL:
        value, state, detail, data_asof = IMPL[sid](con, d, asof)
    else:
        value, state, detail, data_asof = None, 'na', {'note': 'not implemented'}, None
    detail['channel'] = c
    return d, value, state, detail, data_asof


def _history_row(con, rid, sid, d, value, state, detail, data_asof, asof, mode):
    con.execute('INSERT OR REPLACE INTO signal_history VALUES (?,?,?,?,?,?,?,?,?)',
                [rid, sid, d['layer'], data_asof or asof, value, state,
                 json.dumps(detail, ensure_ascii=False, default=str), dt.datetime.now(), mode])


def compute(con, channels, asof):
    defs = signal_defs()
    by_id = {s['id']: s for s in defs['signals']}
    rid = make_run_id(asof)
    results = []
    for c in channels:
        for sid in defs['channels'][c]['signals']:
            d, value, state, detail, data_asof = _one(con, defs, by_id, c, sid, asof)
            con.execute('INSERT OR REPLACE INTO signals VALUES (?,?,?,?,?,?,?)',
                        [rid, sid, d['layer'], data_asof or asof, value, state,
                         json.dumps(detail, ensure_ascii=False, default=str)])
            _history_row(con, rid, sid, d, value, state, detail, data_asof, asof, 'live')
            results.append((sid, d['name'], value, state, data_asof))
    return rid, results


def backfill(con, weeks, today=None):
    """Backfill signal history at each past Friday. Weeks with live rows are left alone."""
    defs = signal_defs()
    by_id = {s['id']: s for s in defs['signals']}
    today = today or dt.date.today()
    done = []
    for k in range(1, weeks + 1):
        day = today - dt.timedelta(weeks=k)
        friday = day - dt.timedelta(days=day.weekday()) + dt.timedelta(days=4)
        rid = make_run_id(friday)
        live = {r[0] for r in con.execute("SELECT signal_id FROM signal_history WHERE run_id = ? AND mode = 'live'",
                                          [rid]).fetchall()}
        for c, meta in defs['channels'].items():
            for sid in meta['signals']:
                if sid in live:
                    continue
                d, value, state, detail, data_asof = _one(con, defs, by_id, c, sid, friday)
                detail['vintage'] = 'backfill: current data vintage, filtered by release date'
                _history_row(con, rid, sid, d, value, state, detail, data_asof, friday, 'backfill')
        done.append(rid)
    return done
