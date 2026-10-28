"""Regression tests for the core calculations. Run: .venv/Scripts/python.exe -m unittest discover -s tests

Each test pins down a bug that actually happened or a rule that is easy to get wrong.
"""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from semis import fetch, signals
from semis.__main__ import _unmatched
from semis.config import ROOT

D = dt.date


def _db():
    con = duckdb.connect(':memory:')
    con.execute((ROOT / 'schema' / 'schema.sql').read_text(encoding='utf-8'))
    return con


def _obs(con, sid, rows, entity='', released=None):
    for d, v in rows:
        con.execute('INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?)',
                    [sid, entity, d, v, 'x', 'L0.other', dt.datetime(2026, 10, 28), released, 'test'])


class QuarterlyFromYtd(unittest.TestCase):
    """SEC cash flow facts are year-to-date: quarters come from differences, Q4 from annual minus 9 months."""

    def test_ytd_and_annual(self):
        units = [
            {'start': '2025-07-01', 'end': '2025-09-30', 'val': 10, 'filed': '2025-10-30'},
            {'start': '2025-07-01', 'end': '2025-12-31', 'val': 25, 'filed': '2026-01-30'},
            {'start': '2025-07-01', 'end': '2026-03-31', 'val': 45, 'filed': '2026-04-30'},
            {'start': '2025-07-01', 'end': '2026-06-30', 'val': 70, 'filed': '2026-07-30'},
        ]
        q = fetch._quarterly(units)
        self.assertEqual({k: v for k, (v, _) in q.items()},
                         {'2025-09-30': 10, '2025-12-31': 15, '2026-03-31': 20, '2026-06-30': 25})

    def test_ttm_column_ignored(self):
        # Amazon's 10-Q has a trailing-12-month column that must not be read as a quarter
        units = [
            {'start': '2026-04-01', 'end': '2026-06-30', 'val': 54, 'filed': '2026-07-31'},
            {'start': '2025-07-01', 'end': '2026-06-30', 'val': 173, 'filed': '2026-07-31'},
        ]
        self.assertEqual(fetch._quarterly(units)['2026-06-30'][0], 54)

    def test_latest_filing_wins(self):
        units = [{'start': '2026-01-01', 'end': '2026-03-31', 'val': 9, 'filed': '2026-04-30'},
                 {'start': '2026-01-01', 'end': '2026-03-31', 'val': 11, 'filed': '2026-07-30'}]
        self.assertEqual(fetch._quarterly(units)['2026-03-31'][0], 11)


class Gex(unittest.TestCase):
    def chain(self, options, spot=100.0):
        return {'data': {'current_price': spot, 'options': options}}

    def opt(self, expiry, cp, strike, oi=1000, iv=0.2):
        return {'option': f'SPY{expiry:%y%m%d}{cp}{int(strike * 1000):08d}', 'open_interest': oi, 'iv': iv}

    def test_same_day_expiry_excluded(self):
        # 2026-10-27: after the close, same-day expiries are dead; keeping them flipped the sign of SPY net GEX
        today = D(2026, 10, 27)
        only_today = self.chain([self.opt(today, 'C', 100)])
        net, flip, spot, n = fetch.gex_from_chain(only_today, today)
        self.assertEqual(n, 0)
        self.assertEqual(net, 0)

    def test_sign_convention(self):
        # Customers sell calls and buy puts: dealers are long call gamma, short put gamma
        today = D(2026, 10, 27)
        exp = today + dt.timedelta(days=30)
        calls, _, _, _ = fetch.gex_from_chain(self.chain([self.opt(exp, 'C', 100)]), today)
        puts, _, _, _ = fetch.gex_from_chain(self.chain([self.opt(exp, 'P', 100)]), today)
        self.assertGreater(calls, 0)
        self.assertLess(puts, 0)

    def test_flip_between_put_and_call_walls(self):
        today = D(2026, 10, 27)
        exp = today + dt.timedelta(days=30)
        net, flip, spot, n = fetch.gex_from_chain(
            self.chain([self.opt(exp, 'P', 95, oi=5000), self.opt(exp, 'C', 105, oi=5000)]), today)
        self.assertIsNotNone(flip)
        self.assertTrue(95 < flip < 105)


class ForeignFilerResults(unittest.TestCase):
    """6-K has no item codes: a results release is recognized by its exhibits (file layouts seen in Oct 2026)."""

    def test_monthly_revenue_report_has_no_candidates(self):
        names = ['0001046179-26-000680-index-headers.html', '0001046179-26-000680-index.html',
                 '0001046179-26-000680.txt', 'a1.jpg', 'tsm-revenue20261008.htm']
        self.assertEqual(fetch._6k_candidates(names, 'tsm-revenue20261008.htm'), [])

    def test_press_release_named_first(self):
        names = ['a2026_10x14xpresentation.htm', 'financial_statementsxusx.htm', 'form6-kquarterlyfilings.htm',
                 'logo6ka.jpg', 'pressreleasefinancialresul.htm']
        got = fetch._6k_candidates(names, 'form6-kquarterlyfilings.htm')
        self.assertEqual(got[0], 'pressreleasefinancialresul.htm')
        self.assertNotIn('form6-kquarterlyfilings.htm', got)

    def test_results_text(self):
        self.assertTrue(fetch._looks_like_results('ASML reports total net sales of 7.5 billion in Q3 2026'))
        self.assertTrue(fetch._looks_like_results('TSMC Reports Third Quarter EPS of NT$17.2'))
        self.assertFalse(fetch._looks_like_results('TSMC September 2026 Revenue Report'))
        self.assertFalse(fetch._looks_like_results('Board approved capital appropriations; Q3 dividend'))


class MonthMath(unittest.TestCase):
    def test_rolling_yoy_across_year_boundary(self):
        rows = []
        for y in (2024, 2025, 2026):
            for m in range(1, 13):
                rows.append((signals._month_end(y, m), 150.0 if y == 2026 else 100.0))
        yoy = dict(signals._rolling3_yoy(rows))
        # The 2026-01 window spans the year end: 2025-11, 2025-12, 2026-01 against 2024-11, 2024-12, 2025-01
        self.assertAlmostEqual(yoy[D(2026, 1, 31)], 100 * (350 / 300 - 1))
        self.assertAlmostEqual(yoy[D(2026, 3, 31)], 50.0)
        self.assertNotIn(D(2024, 12, 31), yoy)              # no year-ago data

    def test_month_end(self):
        self.assertEqual(signals._month_end(2024, 2), D(2024, 2, 29))
        self.assertEqual(signals._month_end(2026, 12), D(2026, 12, 31))


class NumberCheck(unittest.TestCase):
    def check(self, text, pool):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.md'
            p.write_text(text, encoding='utf-8')
            return _unmatched(p, pool)

    def test_chinese_yi_conversions(self):
        # Chinese units: $bn -> 亿 (x10), dollars -> 亿 (/1e8)
        self.assertEqual(self.check('负 21.2 亿美元，440 亿美元', [-2.12, 44000000000]), [])

    def test_english_units(self):
        self.assertEqual(self.check('free cash flow of -$2.12bn over 5 trading days, $44bn auction', [-2.12, 44e9]), [])

    def test_ids_and_dates_ignored(self):
        self.assertEqual(self.check('S-L3-03 和 VETO-01，2026-10-26，CH-B，C4，L5.csp_capex', []), [])

    def test_invented_number_caught(self):
        self.assertEqual(self.check('利差扩大 33bp', [28]), ['33'])

    def test_json_block_ignored(self):
        self.assertEqual(self.check('正文 28\n```json\n{"x": 999}\n```', [28]), [])


class SignalRules(unittest.TestCase):
    def defs(self, sid):
        return next(s for s in signals.signal_defs()['signals'] if s['id'] == sid)

    def test_rate_speed_down_capped_at_watch(self):
        con = _db()
        days = [D(2026, 10, 19) + dt.timedelta(days=i) for i in range(6)]
        _obs(con, 'ust10y', zip(days, [5.30, 5.25, 5.20, 5.15, 5.10, 5.05]))   # -25bp
        v, state, _, _ = signals.rate_speed(con, self.defs('S-L1-01'), days[-1])
        self.assertAlmostEqual(v, -25)
        self.assertEqual(state, 'watch')

    def test_rate_speed_up_can_bind(self):
        con = _db()
        days = [D(2026, 10, 19) + dt.timedelta(days=i) for i in range(6)]
        _obs(con, 'ust10y', zip(days, [5.00, 5.05, 5.10, 5.15, 5.20, 5.25]))   # +25bp
        _, state, _, _ = signals.rate_speed(con, self.defs('S-L1-01'), days[-1])
        self.assertEqual(state, 'binding')

    def test_auction_weak_needs_min_gap(self):
        # 2026-W44: with prior-6 std of only 0.02, 2.59 vs 2.64 must not count as weak (v0.3 needs a 0.05 gap)
        con = _db()
        hist = [2.64, 2.66, 2.62, 2.65, 2.63, 2.64]
        for i, b in enumerate(hist):
            con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',
                        [f'a{i}', 'auction', 'L2', D(2026, 4, 1) + dt.timedelta(days=30 * i), '2-Year',
                         json.dumps({'bidToCoverRatio': str(b)}), None])
        con.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?)',
                    ['now', 'auction', 'L2', D(2026, 10, 26), '2-Year', json.dumps({'bidToCoverRatio': '2.60'}), None])
        _, state, detail, _ = signals.auctions(con, self.defs('S-L2-01'), D(2026, 10, 27))
        self.assertFalse(detail['auctions'][0]['weak'])
        self.assertEqual(state, 'slack')

    def test_unreleased_data_excluded_in_backfill(self):
        # Backfill must not see a quarterly report that had not been published yet
        con = _db()
        _obs(con, 'csp_capex', [(D(2026, 9, 30), 1.0)], entity='META', released=dt.datetime(2026, 10, 21))
        from semis.db import series
        self.assertEqual(series(con, 'csp_capex', 'META', asof=D(2026, 10, 9)), [])
        self.assertEqual(len(series(con, 'csp_capex', 'META', asof=D(2026, 10, 23))), 1)


if __name__ == '__main__':
    unittest.main()
