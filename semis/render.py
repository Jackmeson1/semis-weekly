"""Render one issue's signals, logs and judgments into reports/<run>.html.

The page only lays things out and never makes a judgment of its own: conclusions come from logs/ and the
judgments table, numbers from the signals, signal_history, observations and events tables.
"""
import datetime as dt
import html
import json
import re

import markdown

from .config import ROOT, lang, localized, signal_defs
from .db import series

FILES = {'C1': 'C1-credit', 'C2': 'C2-rates', 'C3': 'C3-liquidity', 'C4': 'C4-positioning',
         'C5': 'C5-industry', 'C6': 'C6-company', 'C7': 'C7-policy'}
STATE_CLASS = {'slack': 'ok', 'watch': 'warn', 'binding': 'bad', 'na': 'na'}

T = {
    'zh': {
        'title': '远端周报 {rid}', 'eyebrow': '半导体远端周报', 'asof': '数据截至 {asof} · 生成于 {today}',
        'state': {'slack': '没收紧', 'watch': '接近', 'binding': '收紧', 'na': '数据缺失'},
        'hz': {'far': ('远', '半年以上', '方向还成立吗'), 'mid': ('中', '两周到一个财报周期', '仓位开多大、要不要对冲'),
               'near': ('近', '两周以内', '现在是进出的好时点吗')},
        'nav': {'synthesis': '综合', 'horizons': '远中近', 'history': '信号历史', 'channels': '信道',
                'calendar': '日程', 'data': '数据'},
        'sec': {'synthesis': '综合', 'invariants': '不变量体检', 'horizons': '远、中、近', 'history': '15 个信号，过去 27 周',
                'channels': '信道', 'calendar': '日程', 'data': '数据状态'},
        'no_l3': '第 3 级综合还没生成。先看下面的远中近；如果第 2 级也没有，那里是各信道“期限含义”的归组。',
        'no_l2': '第 2 级还没生成，这里是各信道的期限含义',
        'no_hz': '没有覆盖这个期限的信道', 'no_log': '本期没有日志', 'low_weight': '低权重',
        'full_synth': '完整综合日志：分工、例外检查、偏离汇总', 'full_hz': '完整期限日志', 'full_ch': '完整日志：依据、期限含义、讲解',
        'history_cap': '每格一周，按信道分组。悬停看数值，本周加粗外框。',
        'backfill_note': '{first} 之前为回补：用当前数据版本，按发布时间过滤，修订过的值无法还原',
        'chains': {'CH-A': 'C2 利率波动 → C1 信用 → 融资 → C5', 'CH-B': 'C1 信用 → 云厂 capex → C5',
                   'CH-C': 'C4 波动冲击 → 被动卖 → 去杠杆', 'CH-D': 'C7 政策冲击 → C2 长端 → C1 信用'},
        'chains_cap': '传导链',
        'cal_head': ('日期', '类型', '内容'), 'cal_fomc': 'FOMC', 'cal_auction': '国债拍卖', 'cal_earn': '已发财报',
        'cal_proj': '，带经济预测', 'cal_to': ' 至 ', 'cal_note': '云厂和芯片公司的财报日期不在数据里，发布后会出现在“已发财报”。',
        'cal_decision': {'raise': '加息', 'lower': '降息', 'maintain': '维持'},
        'fresh_head': ('序列', '最新数据', '最近抓取'), 'event': '事件：',
        'foot': ['三级聚合：信道（第 1 级）→ 远中近（第 2 级）→ 综合（第 3 级）。每一级只读下一级的结论，日志里的数字都经过出处校验。',
                 '判断规则提炼自一位在 X 上公开写作的宏观交易者三年的帖子（不公开其身份）。自用研究，不构成投资建议。'],
        'sparks': {'hy_oas': '高收益利差（%）', 'ig_oas': '投资级利差（%）', 'ust10y': '10 年期收益率（%）',
                   'ust2s10s': '2s10s（%）', 'tga': 'TGA（百万美元）', 'on_rrp': '逆回购（十亿美元）',
                   'vix': 'VIX', 'spx': '标普 500', 'tsmc_rev': '台积电月营收（新台币）'},
        'since': '起', 'range': '区间',
        'fonts': ('"Noto Serif SC", "Songti SC", "SimSun", serif',
                  '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, sans-serif'),
        'font_link': 'family=Noto+Serif+SC:wght@600;700&family=IBM+Plex+Mono:wght@400;500',
        'html_lang': 'zh-CN',
    },
    'en': {
        'title': 'Far-Layer Weekly {rid}', 'eyebrow': 'Semiconductor far-layer weekly', 'asof': 'Data to {asof} · built {today}',
        'state': {'slack': 'Not binding', 'watch': 'Near', 'binding': 'Binding', 'na': 'No data'},
        'hz': {'far': ('Far', '6 months and beyond', 'Does the direction still hold?'),
               'mid': ('Mid', '2 weeks to one earnings cycle', 'How big, and hedged or not?'),
               'near': ('Near', 'Under 2 weeks', 'Is now a good time to act?')},
        'nav': {'synthesis': 'Synthesis', 'horizons': 'Horizons', 'history': 'History', 'channels': 'Channels',
                'calendar': 'Calendar', 'data': 'Data'},
        'sec': {'synthesis': 'Synthesis', 'invariants': 'Invariant check', 'horizons': 'Far, mid, near',
                'history': '15 signals, past 27 weeks', 'channels': 'Channels', 'calendar': 'Calendar', 'data': 'Data status'},
        'no_l3': 'Level 3 has not been written yet. See the horizons below; if level 2 is missing too, they group the '
                 'channels\' horizon notes.',
        'no_l2': 'Level 2 has not been written yet; these are the channels\' horizon notes',
        'no_hz': 'No channel covers this horizon', 'no_log': 'No log this issue', 'low_weight': 'low weight',
        'full_synth': 'Full synthesis log: roles, exception checks, all deviations', 'full_hz': 'Full horizon log',
        'full_ch': 'Full log: evidence, horizon implications, explainer',
        'history_cap': 'One cell per week, grouped by channel. Hover for the value; this week has a heavy outline.',
        'backfill_note': 'Before {first}: backfilled with the current data vintage, filtered by release date; revisions cannot be restored',
        'chains': {'CH-A': 'C2 rate vol → C1 credit → funding → C5', 'CH-B': 'C1 credit → cloud capex → C5',
                   'CH-C': 'C4 vol shock → forced selling → deleveraging', 'CH-D': 'C7 policy shock → C2 long end → C1 credit'},
        'chains_cap': 'Transmission chains',
        'cal_head': ('Date', 'Type', 'Detail'), 'cal_fomc': 'FOMC', 'cal_auction': 'Treasury auction',
        'cal_earn': 'Results filed', 'cal_proj': ', with projections', 'cal_to': ' to ',
        'cal_note': 'Cloud and chip earnings dates are not in the data; releases appear under "Results filed" once out.',
        'cal_decision': {'raise': 'hike', 'lower': 'cut', 'maintain': 'hold'},
        'fresh_head': ('Series', 'Latest data', 'Last fetched'), 'event': 'event: ',
        'foot': ['Three-level aggregation: channels (level 1) → horizons (level 2) → synthesis (level 3). Each level reads '
                 'only the level below, and every number in a log is checked against its source.',
                 'The rules are distilled from three years of public posts by a macro trader on X, who is not identified '
                 'here. Personal research, not investment advice.'],
        'sparks': {'hy_oas': 'High-yield spread (%)', 'ig_oas': 'IG spread (%)', 'ust10y': '10-year yield (%)',
                   'ust2s10s': '2s10s (%)', 'tga': 'TGA ($mn)', 'on_rrp': 'Reverse repo ($bn)', 'vix': 'VIX',
                   'spx': 'S&P 500', 'tsmc_rev': 'TSMC monthly revenue (TWD)'},
        'since': 'from', 'range': 'range',
        'fonts': ('"Source Serif 4", "Iowan Old Style", Georgia, serif',
                  '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif'),
        'font_link': 'family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;600'
                     '&family=IBM+Plex+Mono:wght@400;500',
        'html_lang': 'en',
    },
}
SPARKS = {'C1': [('hy_oas', ''), ('ig_oas', '')], 'C2': [('ust10y', ''), ('ust2s10s', '')],
          'C3': [('tga', ''), ('on_rrp', '')], 'C4': [('vix', ''), ('spx', '')], 'C5': [('tsmc_rev', '2330')]}

CSS = """
/* Layout: a morning note. Action headline, a three-cell horizon track, a sticky channel nav, then detail
   in the order a reader drills down: horizons, signal history, channels, calendar, data. */
:root {
  --paper: #f2f4f7; --surface: #ffffff; --ink: #12161d; --ink-2: #4f5866; --rule: #dde2ea; --rule-2: #c9d0da;
  --accent: #2b3a8f; --accent-soft: #e7eaf7; --spark: #2a78d6;
  --ok: #0a7d0a; --ok-bg: #e2f2e2; --warn: #8a5a00; --warn-bg: #fcefd0; --bad: #b42323; --bad-bg: #fae2e2;
  --na: #5d6573; --na-bg: #eceff3;
  --font-display: __DISPLAY__; --font-body: __BODY__;
  --font-mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #0f1115; --surface: #171a20; --ink: #e8ebf0; --ink-2: #a0a8b6; --rule: #262b33; --rule-2: #353b45;
  --accent: #9aa7f4; --accent-soft: #212646; --spark: #4b95ea;
  --ok: #52c552; --ok-bg: #15301a; --warn: #f0b545; --warn-bg: #382a0c; --bad: #f27b7b; --bad-bg: #3b1717;
  --na: #9aa2af; --na-bg: #22262d; color-scheme: dark; } }
:root[data-theme="dark"] {
  --paper: #0f1115; --surface: #171a20; --ink: #e8ebf0; --ink-2: #a0a8b6; --rule: #262b33; --rule-2: #353b45;
  --accent: #9aa7f4; --accent-soft: #212646; --spark: #4b95ea;
  --ok: #52c552; --ok-bg: #15301a; --warn: #f0b545; --warn-bg: #382a0c; --bad: #f27b7b; --bad-bg: #3b1717;
  --na: #9aa2af; --na-bg: #22262d; color-scheme: dark; }
* { box-sizing: border-box; }
html { scroll-padding-top: 64px; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--font-body); font-size: 15px; line-height: 1.7;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 0 72px; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10;
  background: var(--paper); }
.wrap { max-width: 1060px; margin: 0 auto; display: grid; gap: 44px; }
h1, h2 { font-family: var(--font-display); margin: 0; line-height: 1.25; text-wrap: balance; letter-spacing: -0.005em; }
h2 { font-size: clamp(20px, 2.6vw, 24px); }
h3 { font-size: 15.5px; margin: 0; font-weight: 600; }
p { margin: 0; max-width: 72ch; }
a { color: var(--accent); text-underline-offset: 3px; }
a:focus-visible, summary:focus-visible, .cell:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.muted { color: var(--ink-2); }
.small { font-size: 13.5px; }
.eyebrow { font-family: var(--font-mono); font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
section { display: grid; gap: 16px; }
.sec-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  border-bottom: 1px solid var(--rule-2); padding-bottom: 8px; }

/* masthead */
.mast { display: grid; gap: 18px; padding-top: 36px; }
.mast-top { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: baseline; }
.issue { font-family: var(--font-mono); font-size: 13px; color: var(--ink-2); }
.action { font-family: var(--font-display); font-size: clamp(30px, 5.4vw, 50px); font-weight: 700; line-height: 1.15; }
.verdict { font-size: 17.5px; line-height: 1.65; max-width: 66ch; }
.track { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--rule); border-radius: 8px;
  overflow: hidden; background: var(--surface); }
.track a { display: grid; gap: 4px; padding: 12px 14px 13px; text-decoration: none; color: var(--ink);
  border-top: 4px solid var(--c); }
.track a + a { border-left: 1px solid var(--rule); }
.track .hz-name { font-family: var(--font-display); font-size: 19px; font-weight: 700; }
.track .hz-sub { font-size: 12.5px; color: var(--ink-2); }
@media (max-width: 620px) { .track { grid-template-columns: 1fr; } .track a + a { border-left: 0; border-top-width: 4px; } }

/* sticky nav */
nav.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 9; background: var(--paper);
  border-bottom: 1px solid var(--rule); margin-inline: calc(-1 * max(16px, env(safe-area-inset-left, 0px)));
  padding: 9px max(16px, env(safe-area-inset-left, 0px)); }
nav.bar .in { max-width: 1060px; margin: 0 auto; display: flex; gap: 6px 18px; flex-wrap: wrap; align-items: center;
  justify-content: space-between; font-size: 13px; }
nav.bar .chs, nav.bar .secs { display: flex; gap: 4px 12px; flex-wrap: wrap; }
nav.bar a { color: var(--ink); text-decoration: none; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
nav.bar a:hover { color: var(--accent); }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--c); flex: none; }

/* state pills */
.pill { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; padding: 3px 10px;
  border-radius: 999px; white-space: nowrap; color: var(--fg); background: var(--bg); }
.pill::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.s-ok { --fg: var(--ok); --bg: var(--ok-bg); --c: var(--ok); }
.s-warn { --fg: var(--warn); --bg: var(--warn-bg); --c: var(--warn); }
.s-bad { --fg: var(--bad); --bg: var(--bad-bg); --c: var(--bad); }
.s-na { --fg: var(--na); --bg: var(--na-bg); --c: var(--na); }

.box { background: var(--surface); border: 1px solid var(--rule); border-radius: 8px; padding: 18px; display: grid; gap: 12px; min-width: 0; }
.notice { border-left: 3px solid var(--accent); background: var(--accent-soft); padding: 12px 14px; border-radius: 4px; font-size: 14px; }

/* invariants */
.inv { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 12px; }
.inv .box { gap: 8px; padding: 14px 16px; }
.inv .id { font-family: var(--font-mono); font-size: 12px; color: var(--ink-2); }

/* horizons */
.hz { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 14px; }
.hz .q { font-size: 13px; color: var(--ink-2); }
.hz ul { margin: 0; padding-left: 1.1em; display: grid; gap: 8px; font-size: 14px; }
.src { font-family: var(--font-mono); font-size: 12px; color: var(--ink-2); }
.chainlist { display: grid; gap: 6px; font-size: 13px; border-top: 1px dashed var(--rule-2); padding-top: 10px; }
.chainlist div { display: grid; grid-template-columns: 50px 1fr; gap: 8px; align-items: start; }
.chainlist .id { font-family: var(--font-mono); font-size: 12px; padding: 1px 6px; border-radius: 4px; background: var(--bg); color: var(--fg); justify-self: start; }

/* history grid */
.hgrid { display: grid; gap: 3px; min-width: max-content; }
.hrow { display: grid; grid-template-columns: 250px auto; gap: 12px; align-items: center; }
.hgroup { font-size: 12px; font-weight: 600; color: var(--ink-2); padding-top: 8px; }
.hlab { font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hcells { display: flex; gap: 3px; }
.cell { display: inline-block; width: 15px; height: 15px; border-radius: 3px; background: var(--c); flex: none; }
.cell.s-ok { opacity: .5; }
.cell.s-na { background: var(--na-bg); box-shadow: inset 0 0 0 1px var(--rule-2); }
.cell.now { box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--ink); }
.wk { display: inline-block; width: 15px; flex: none; font-family: var(--font-mono); font-size: 10px; color: var(--ink-2); white-space: nowrap; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12.5px; color: var(--ink-2); align-items: center; }
.legend span { display: inline-flex; gap: 6px; align-items: center; }
@media (max-width: 560px) { .hrow { grid-template-columns: 130px auto; } }

/* channel cards */
.cards { display: grid; gap: 14px; }
.card-head { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; }
.code { font-family: var(--font-mono); font-size: 13px; color: var(--ink-2); }
.card.off { opacity: .6; }
.sparks { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr)); gap: 14px; }
.spark { display: grid; gap: 2px; font-size: 12.5px; }
.spark .lab { display: flex; justify-content: space-between; gap: 8px; }
.spark svg { width: 100%; height: 50px; display: block; }
.spark .line { fill: none; stroke: var(--spark); stroke-width: 1.6; vector-effect: non-scaling-stroke; }
.spark .area { fill: var(--spark); opacity: .09; }
.spark .dot2 { fill: var(--spark); stroke: var(--surface); stroke-width: 2; }
details > summary { cursor: pointer; color: var(--accent); font-size: 14px; width: fit-content; }
.log { display: grid; gap: 10px; font-size: 14.5px; padding-top: 6px; }
.log h2 { font-family: var(--font-body); font-size: 15px; margin-top: 10px; }
.log ul, .log ol { margin: 0; padding-left: 1.2em; display: grid; gap: 4px; }
.log table, table.t { border-collapse: collapse; width: 100%; font-size: 13px; }
.log th, .log td, table.t th, table.t td { text-align: left; padding: 7px 9px; border-bottom: 1px solid var(--rule); vertical-align: top; }
.log th, table.t th { font-size: 12px; color: var(--ink-2); font-weight: 600; }
.scroll { overflow-x: auto; }
footer { font-size: 13px; color: var(--ink-2); display: grid; gap: 6px; border-top: 1px solid var(--rule-2); padding-top: 16px; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
"""


def _t():
    return T[lang()]


def _pill(state):
    return f'<span class="pill s-{STATE_CLASS.get(state, "na")}">{_t()["state"].get(state, state)}</span>'


def _split(v):
    head, _, rest = v.partition('｜')
    return head, rest


def _spark(con, series_id, entity, label, asof):
    rows = series(con, series_id, entity, asof=asof)[-130:]
    if len(rows) < 2:
        return ''
    t = _t()
    vals = [v for _, v in rows]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    w, h, pad = 240, 50, 4
    pts = [(pad + i * (w - 2 * pad) / (len(vals) - 1), pad + (h - 2 * pad) * (1 - (v - lo) / span))
           for i, v in enumerate(vals)]
    line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    area = f'{pts[0][0]:.1f},{h - pad} ' + line + f' {pts[-1][0]:.1f},{h - pad}'
    x, y = pts[-1]
    fmt = (lambda v: f'{v:,.0f}') if abs(vals[-1]) >= 1000 else (lambda v: f'{v:.2f}')
    return (f'<div class="spark"><div class="lab"><span>{html.escape(label)}</span>'
            f'<span class="mono">{fmt(vals[-1])}</span></div>'
            f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" role="img" '
            f'aria-label="{html.escape(label)}: {fmt(vals[0])} → {fmt(vals[-1])}, {t["range"]} {fmt(lo)}–{fmt(hi)}">'
            f'<polygon class="area" points="{area}"/><polyline class="line" points="{line}"/>'
            f'<circle class="dot2" cx="{x:.1f}" cy="{y:.1f}" r="3"/></svg>'
            f'<div class="lab muted mono"><span>{rows[0][0]} {t["since"]}</span>'
            f'<span>{t["range"]} {fmt(lo)}–{fmt(hi)}</span></div></div>')


def _log_body(text):
    text = re.sub(r'```json.*?```', '', text, flags=re.S)
    text = re.sub(r'^# .*\n', '', text, count=1)
    text = re.sub(r'^\*\*(状态|一句话|动作含义|State|One line|Action)\*\*\s*[:：].*\n', '', text, flags=re.M)
    out = markdown.markdown(text, extensions=['tables'])
    return out.replace('<table>', '<div class="scroll"><table>').replace('</table>', '</table></div>')


def _judgments(con, rid):
    j = {}
    for level, scope, item, verdict in con.execute(
            'SELECT level, scope, item, verdict FROM judgments WHERE run_id = ?', [rid]).fetchall():
        j.setdefault((level, scope), {})[item] = verdict
    return j


def _masthead(judg, rid, asof):
    t = _t()
    s = judg.get((3, 'all'))
    action, verdict = _split(s['action']) if s else ('—', t['no_l3'])
    cells = []
    for h in ('far', 'mid', 'near'):
        name, sub, _ = t['hz'][h]
        state = _split(judg[(2, h)]['state'])[0] if (2, h) in judg else 'na'
        cls = STATE_CLASS.get(state, 'na')
        cells.append(f'<a href="#hz-{h}" class="s-{cls}" style="--c: var(--{cls})">'
                     f'<span class="hz-name">{name}</span>{_pill(state)}<span class="hz-sub">{sub}</span></a>')
    return (f'<header class="mast"><div class="mast-top"><span class="eyebrow">{t["eyebrow"]}</span>'
            f'<span class="issue">{rid} · {t["asof"].format(asof=asof, today=dt.date.today())}</span></div>'
            f'<h1 class="action" id="synthesis">{html.escape(action)}</h1>'
            f'<p class="verdict">{html.escape(verdict)}</p>'
            f'<div class="track">{"".join(cells)}</div></header>')


def _nav(judg, defs):
    t = _t()
    chs = []
    for c in FILES:
        state = _split(judg[(1, c)]['state'])[0] if (1, c) in judg else 'na'
        chs.append(f'<a href="#{c}" title="{t["state"].get(state, state)}"><span class="dot s-{STATE_CLASS.get(state, "na")}">'
                   f'</span><span class="mono">{c}</span> {localized(defs["channels"][c], "name")}</a>')
    secs = ''.join(f'<a href="#{k}">{v}</a>' for k, v in t['nav'].items())
    return f'<nav class="bar" aria-label="sections"><div class="in"><div class="chs">{"".join(chs)}</div><div class="secs">{secs}</div></div></nav>'


def _synthesis(judg, run_dir):
    t = _t()
    s = judg.get((3, 'all'))
    if not s:
        return f'<div class="notice">{t["no_l3"]}</div>'
    tiles = []
    for k, v in sorted(s.items()):
        if not k.startswith('invariant:'):
            continue
        state, why = _split(v)
        cls = {'稳': 'ok', 'Stable': 'ok', '受压': 'warn', 'Under pressure': 'warn', '动摇': 'bad', 'Shaken': 'bad'}.get(state, 'na')
        tiles.append(f'<div class="box"><span class="id">{k.split(":", 1)[1]}</span>'
                     f'<span class="pill s-{cls}">{html.escape(state)}</span><p class="small">{html.escape(why)}</p></div>')
    log = run_dir / 'synthesis.md'
    body = _log_body(log.read_text(encoding='utf-8')) if log.exists() else ''
    return (f'<div class="sec-head"><h2>{t["sec"]["invariants"]}</h2></div><div class="inv">{"".join(tiles)}</div>'
            f'<details><summary>{t["full_synth"]}</summary><div class="log">{body}</div></details>')


def _horizons(judg, run_dir, defs):
    t = _t()
    cols = []
    for h in ('far', 'mid', 'near'):
        name, sub, question = t['hz'][h]
        s = judg.get((2, h))
        head = f'<div class="card-head"><h3>{name} · {sub}</h3>'
        if s:
            state, verdict = _split(s['state'])
            chains = []
            for k, v in sorted(s.items()):
                if not k.startswith('chain:'):
                    continue
                status, why = _split(v)
                cls = 'warn' if re.search(r'传导中|Transmitting', status) else 'na'
                chains.append(f'<div><span class="id s-{cls}">{k.split(":", 1)[1]}</span>'
                              f'<span><strong>{html.escape(status)}</strong> {html.escape(why)}</span></div>')
            log = run_dir / f'{h}.md'
            body = _log_body(log.read_text(encoding='utf-8')) if log.exists() else ''
            cols.append(f'<div class="box" id="hz-{h}">{head}{_pill(state)}</div><p class="q">{question}</p>'
                        f'<p class="small">{html.escape(verdict)}</p>'
                        + (f'<div class="chainlist">{"".join(chains)}</div>' if chains else '')
                        + f'<details><summary>{t["full_hz"]}</summary><div class="log">{body}</div></details></div>')
            continue
        items = [(c, judg[(1, c)][f'horizon:{h}']) for c in FILES if (1, c) in judg and f'horizon:{h}' in judg[(1, c)]]
        lis = ''.join(f'<li><span class="src">{c} {localized(defs["channels"][c], "name")}</span><br>{html.escape(v)}</li>'
                      for c, v in items) or f'<li class="muted">{t["no_hz"]}</li>'
        cols.append(f'<div class="box" id="hz-{h}">{head}</div><p class="q">{t["no_l2"]}</p><ul>{lis}</ul></div>')
    chains_cap = '；'.join(f'{k} {v}' for k, v in t['chains'].items()) if lang() == 'zh' else \
        '; '.join(f'{k} {v}' for k, v in t['chains'].items())
    return f'<div class="hz">{"".join(cols)}</div><p class="muted small">{t["chains_cap"]}: {chains_cap}</p>'


def _history(con, rid, defs):
    t = _t()
    by_id = {s['id']: s for s in defs['signals']}
    runs = [r for (r,) in con.execute('SELECT DISTINCT run_id FROM signal_history WHERE run_id <= ? '
                                      'ORDER BY run_id DESC LIMIT 27', [rid]).fetchall()][::-1]
    if not runs:
        return ''
    cells = {(r, s): (st, v, m) for r, s, st, v, m in con.execute(
        'SELECT run_id, signal_id, state, value, mode FROM signal_history WHERE run_id IN (SELECT unnest(?))',
        [runs]).fetchall()}
    head = ''.join(f'<span class="wk">{r[-3:] if i % 4 == 0 or r == rid else ""}</span>' for i, r in enumerate(runs))
    rows = [f'<div class="hrow"><span></span><span class="hcells">{head}</span></div>']
    for c, meta in defs['channels'].items():
        if not meta['signals']:
            continue
        rows.append(f'<div class="hgroup">{c} {localized(meta, "name")}</div>')
        for sid in meta['signals']:
            row = []
            for r in runs:
                st, v, m = cells.get((r, sid), ('na', None, ''))
                val = '' if v is None else f' · {v:,.2f}'
                tag = ' (backfill)' if m == 'backfill' and lang() == 'en' else '（回补）' if m == 'backfill' else ''
                row.append(f'<span class="cell s-{STATE_CLASS.get(st, "na")}{" now" if r == rid else ""}" '
                           f'title="{r} {sid}: {t["state"].get(st, st)}{val}{tag}"></span>')
            name = localized(by_id[sid], 'name')
            rows.append(f'<div class="hrow"><span class="hlab" title="{html.escape(name)}"><span class="mono">{sid}</span> '
                        f'{html.escape(name)}</span><span class="hcells">{"".join(row)}</span></div>')
    first_live = con.execute("SELECT min(run_id) FROM signal_history WHERE mode = 'live'").fetchone()[0]
    legend = ''.join(f'<span><span class="cell s-{STATE_CLASS[k]}"></span>{v}</span>' for k, v in t['state'].items())
    return (f'<div class="box"><div class="scroll"><div class="hgrid">{"".join(rows)}</div></div>'
            f'<div class="legend">{legend}<span>{t["backfill_note"].format(first=first_live)}</span></div></div>')


def _cards(con, judg, run_dir, defs, asof):
    t = _t()
    cards = []
    for c, stem in FILES.items():
        meta = defs['channels'][c]
        name = localized(meta, 'name')
        log = run_dir / f'{stem}.md'
        if (1, c) not in judg or not log.exists():
            cards.append(f'<div class="box card off" id="{c}"><div class="card-head"><span class="code">{c}</span>'
                         f'<h3>{name}</h3><span class="pill s-na">{t["no_log"]}</span></div></div>')
            continue
        state, verdict = _split(judg[(1, c)]['state'])
        sparks = ''.join(_spark(con, sid, ent, t['sparks'][sid], asof) for sid, ent in SPARKS.get(c, []))
        weight = f'<span class="muted small">{t["low_weight"]}</span>' if meta.get('weight') == 'low' else ''
        cards.append(
            f'<div class="box card" id="{c}"><div class="card-head"><span class="code">{c}</span>'
            f'<h3>{name}</h3>{_pill(state)}{weight}</div><p>{html.escape(verdict)}</p>'
            + (f'<div class="sparks">{sparks}</div>' if sparks else '')
            + f'<details><summary>{t["full_ch"]}</summary>'
              f'<div class="log">{_log_body(log.read_text(encoding="utf-8"))}</div></details></div>')
    return ''.join(cards)


def _calendar(con, today):
    t = _t()

    def ev(kind, a, b):
        return con.execute('SELECT event_date, entity, payload FROM events WHERE kind = ? AND event_date BETWEEN ? AND ? '
                           'ORDER BY event_date', [kind, a, b]).fetchall()
    rows = []
    for d, _, p in ev('fomc', today - dt.timedelta(days=3), today + dt.timedelta(days=60)):
        p = json.loads(p)
        text = f"{p['start']}{t['cal_to']}{p['end']}" + (t['cal_proj'] if p.get('projections') else '')
        if p.get('decision'):
            text += f" · {t['cal_decision'].get(p['decision'], p['decision'])} {p.get('target_range') or ''}"
            if p.get('statement_url'):
                text = f'<a href="{html.escape(p["statement_url"])}">{text}</a>'
        rows.append((d, t['cal_fomc'], text))
    for d, e, p in ev('auction_upcoming', today, today + dt.timedelta(days=14)):
        p = json.loads(p)
        rows.append((d, t['cal_auction'], f"{e} ({p.get('securityType')})"))
    for d, e, p in ev('earnings', today - dt.timedelta(days=21), today):
        p = json.loads(p)
        rows.append((d, t['cal_earn'], f'<a href="{html.escape(p["url"])}">{e}</a>'))
    rows.sort()
    h = t['cal_head']
    body = ''.join(f'<tr><td class="mono">{d}</td><td>{k}</td><td>{v}</td></tr>' for d, k, v in rows)
    return (f'<div class="box scroll"><table class="t"><thead><tr><th>{h[0]}</th><th>{h[1]}</th><th>{h[2]}</th></tr></thead>'
            f'<tbody>{body}</tbody></table><p class="muted small">{t["cal_note"]}</p></div>')


def _freshness(con):
    t = _t()
    rows = con.execute("""
        SELECT o.series_id, max(o.obs_date), (SELECT max(retrieved_at) FROM raw_fetch f WHERE f.series_id = o.series_id)
        FROM obs_latest o GROUP BY 1 ORDER BY 1""").fetchall()
    rows += [(t['event'] + k, d, r) for k, d, r in con.execute("""
        SELECT kind, max(event_date), (SELECT max(retrieved_at) FROM raw_fetch f WHERE f.fetch_id = max(e.fetch_id))
        FROM events e GROUP BY 1 ORDER BY 1""").fetchall()]
    h = t['fresh_head']
    body = ''.join(f'<tr><td class="mono">{s}</td><td class="mono">{d}</td>'
                   f'<td class="mono">{(r.strftime("%Y-%m-%d %H:%M") + " UTC") if r else "—"}</td></tr>' for s, d, r in rows)
    return (f'<div class="box scroll"><table class="t"><thead><tr><th>{h[0]}</th><th>{h[1]}</th><th>{h[2]}</th></tr>'
            f'</thead><tbody>{body}</tbody></table></div>')


def render(con, rid):
    t = _t()
    defs = signal_defs()
    run_dir = ROOT / 'logs' / rid
    asof = con.execute('SELECT max(as_of) FROM signals WHERE run_id = ?', [rid]).fetchone()[0] or dt.date.today()
    judg = _judgments(con, rid)
    display, body = t['fonts']
    css = CSS.replace('__DISPLAY__', display).replace('__BODY__', body)
    sec = t['sec']
    foot = ''.join(f'<span>{line}</span>' for line in t['foot'])
    return f"""<title>{t['title'].format(rid=rid)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{t['font_link']}&display=swap">
<style>{css}</style>
<div class="wrap" lang="{t['html_lang']}">
{_masthead(judg, rid, asof)}
</div>
{_nav(judg, defs)}
<div class="wrap" lang="{t['html_lang']}" style="margin-top: 32px">
<section>{_synthesis(judg, run_dir)}</section>
<section id="horizons"><div class="sec-head"><h2>{sec['horizons']}</h2></div>{_horizons(judg, run_dir, defs)}</section>
<section id="history"><div class="sec-head"><h2>{sec['history']}</h2><span class="muted small">{t['history_cap']}</span></div>
{_history(con, rid, defs)}</section>
<section id="channels"><div class="sec-head"><h2>{sec['channels']}</h2></div><div class="cards">{_cards(con, judg, run_dir, defs, asof)}</div></section>
<section id="calendar"><div class="sec-head"><h2>{sec['calendar']}</h2></div>{_calendar(con, dt.date.today())}</section>
<section id="data"><div class="sec-head"><h2>{sec['data']}</h2></div>{_freshness(con)}</section>
<footer>{foot}</footer>
</div>
"""
