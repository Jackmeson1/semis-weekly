"""Render one issue's signals, logs and judgments into reports/<run>.html.

The page only lays things out and never makes a judgment of its own: conclusions come from logs/ and the
judgments table, numbers from the signals, signal_history, observations and events tables.
"""
import datetime as dt
import html
import json
import re

import markdown

from .config import ID_RE, ROOT, expand_id, glossary, lang, localized, registry, signal_defs
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
        'font': '"IBM Plex Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
        'lh': '1.7',
        'font_link': 'family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;600',
        'hist_head': '信号', 'stale': '可能过期',
        'series': {'cftc_net': 'CFTC 杠杆基金股指期货净头寸', 'csp_capex': '云厂资本开支', 'csp_ocf': '云厂经营现金流',
                   'fed_assets': '联储总资产', 'gex': '做市商净 GEX', 'gex_flip': 'gamma 翻转点', 'gex_spot': '期权链标的价格',
                   'hy_oas': '高收益债利差', 'ig_oas': '投资级债利差', 'on_rrp': '隔夜逆回购', 'tga': '财政部 TGA 账户',
                   'tlt_iv30': 'TLT 30 日隐含波动', 'tsmc_rev': '台积电月营收', 'tw_ai_chain_rev': '台湾 AI 服务器链月营收',
                   'ust10y': '10 年期美债收益率', 'ust2s10s': '2 年与 10 年期利差', 'vix': 'VIX', 'spx': '标普 500',
                   'earnings': '财报公告', 'auction': '国债拍卖结果', 'fomc': 'FOMC 会议', 'auction_upcoming': '即将进行的拍卖'},
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
        'font': '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
        'lh': '1.5',
        'font_link': 'family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;500',
        'hist_head': 'Signal', 'stale': 'May be stale',
        'series': {'cftc_net': 'CFTC leveraged-fund index futures, net', 'csp_capex': 'Cloud capex',
                   'csp_ocf': 'Cloud operating cash flow', 'fed_assets': 'Fed total assets', 'gex': 'Dealer net GEX',
                   'gex_flip': 'Gamma flip level', 'gex_spot': 'Option-chain spot', 'hy_oas': 'High-yield spread',
                   'ig_oas': 'Investment-grade spread', 'on_rrp': 'Overnight reverse repo', 'tga': 'Treasury General Account',
                   'tlt_iv30': 'TLT 30-day implied vol', 'tsmc_rev': 'TSMC monthly revenue',
                   'tw_ai_chain_rev': 'Taiwan AI-server chain revenue', 'ust10y': '10-year Treasury yield',
                   'ust2s10s': '2s10s curve', 'vix': 'VIX', 'spx': 'S&P 500', 'earnings': 'Results releases',
                   'auction': 'Treasury auction results', 'fomc': 'FOMC meetings', 'auction_upcoming': 'Upcoming auctions'},
        'html_lang': 'en',
    },
}
SPARKS = {'C1': [('hy_oas', ''), ('ig_oas', '')], 'C2': [('ust10y', ''), ('ust2s10s', '')],
          'C3': [('tga', ''), ('on_rrp', '')], 'C4': [('vix', ''), ('spx', '')], 'C5': [('tsmc_rev', '2330')]}

CSS = """
/* Layout: aligned with IBM Carbon. White ground, flat gray tiles in 1px-gutter groups, Plex type on Carbon's
   scale. First screen: the action, a verdict callout, three horizon tiles; then horizons, history, channels,
   calendar, data. Status always pairs color with a shape (circle, triangle, diamond, hollow circle). */
:root {
  --background: #ffffff; --layer-01: #f4f4f4; --layer-accent: #e0e0e0; --layer-hover: #e8e8e8;
  --text-primary: #161616; --text-secondary: #525252; --text-helper: #6f6f6f;
  --border-subtle: #c6c6c6; --border-subtle-00: #e0e0e0; --border-strong: #8d8d8d;
  --link: #0f62fe; --focus: #0f62fe; --info-border: #0043ce; --info-bg: #edf5ff; --chart-1: #6929c4;
  --st-slack-fg: #0e6027; --st-slack-bg: #defbe6; --st-watch-fg: #684e00; --st-watch-bg: #fcf4d6;
  --st-binding-fg: #a2191f; --st-binding-bg: #fff1f1; --st-na-fg: #525252; --st-na-bg: #e0e0e0;
  --font-sans: __SANS__; --font-mono: "IBM Plex Mono", ui-monospace, Consolas, monospace; --lh-body: __LH__;
  --sp-02: 4px; --sp-03: 8px; --sp-04: 12px; --sp-05: 16px; --sp-06: 24px; --sp-07: 32px; --sp-09: 48px;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --background: #161616; --layer-01: #262626; --layer-accent: #393939; --layer-hover: #333333;
  --text-primary: #f4f4f4; --text-secondary: #c6c6c6; --text-helper: #a8a8a8;
  --border-subtle: #525252; --border-subtle-00: #393939; --border-strong: #6f6f6f;
  --link: #78a9ff; --focus: #ffffff; --info-border: #4589ff; --info-bg: #262626; --chart-1: #a56eff;
  --st-slack-fg: #6fdc8c; --st-slack-bg: #044317; --st-watch-fg: #f1c21b; --st-watch-bg: #302400;
  --st-binding-fg: #ff8389; --st-binding-bg: #2d0709; --st-na-fg: #c6c6c6; --st-na-bg: #393939; color-scheme: dark; } }
:root[data-theme="dark"] {
  --background: #161616; --layer-01: #262626; --layer-accent: #393939; --layer-hover: #333333;
  --text-primary: #f4f4f4; --text-secondary: #c6c6c6; --text-helper: #a8a8a8;
  --border-subtle: #525252; --border-subtle-00: #393939; --border-strong: #6f6f6f;
  --link: #78a9ff; --focus: #ffffff; --info-border: #4589ff; --info-bg: #262626; --chart-1: #a56eff;
  --st-slack-fg: #6fdc8c; --st-slack-bg: #044317; --st-watch-fg: #f1c21b; --st-watch-bg: #302400;
  --st-binding-fg: #ff8389; --st-binding-bg: #2d0709; --st-na-fg: #c6c6c6; --st-na-bg: #393939; color-scheme: dark; }
* { box-sizing: border-box; }
html { scroll-padding-top: 56px; }
body { margin: 0; background: var(--background); color: var(--text-primary); font-family: var(--font-sans);
  font-size: 16px; line-height: var(--lh-body);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 0 var(--sp-09); }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10;
  background: var(--background); }
.wrap { max-width: 1056px; margin: 0 auto; display: grid; gap: var(--sp-09); }
h1, h2, h3 { margin: 0; text-wrap: balance; }
h2 { font-size: 20px; line-height: 1.4; font-weight: 400; }
h3 { font-size: 16px; line-height: 1.5; font-weight: 600; }
p { margin: 0; max-width: 70ch; }
a { color: var(--link); text-underline-offset: 3px; }
a:focus-visible, summary:focus-visible { outline: 2px solid var(--focus); outline-offset: -2px; }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.muted { color: var(--text-secondary); }
.small { font-size: 14px; }
.vh { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.eyebrow { font-size: 12px; letter-spacing: .32px; color: var(--text-secondary); }
section { display: grid; gap: var(--sp-05); }
.sec-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--sp-03) var(--sp-05); flex-wrap: wrap; }
.sec-head .small { color: var(--text-secondary); font-size: 12px; }

/* masthead */
.mast { display: grid; gap: var(--sp-05); padding-top: var(--sp-07); }
.mast-top { display: flex; justify-content: space-between; gap: var(--sp-03); flex-wrap: wrap; align-items: baseline; }
.issue { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }
.action { font-size: clamp(24px, 6vw, 32px); font-weight: 400; line-height: 1.25; }
.callout { background: var(--info-bg); border-left: 3px solid var(--info-border); padding: var(--sp-04) var(--sp-05); }
.track { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; }
.tile-link { display: grid; gap: var(--sp-02); align-content: start; justify-items: start; padding: var(--sp-05);
  background: var(--layer-01); color: var(--text-primary); text-decoration: none; }
.tile-link:hover { background: var(--layer-hover); }
.tile-link .hz-name { font-size: 20px; line-height: 1.4; }
.tile-link .hz-sub { font-size: 12px; color: var(--text-secondary); }
.tile-link .tag { margin-top: var(--sp-03); }
@media (max-width: 671px) { .track { grid-template-columns: 1fr; } }

/* sticky nav: one row; it scrolls sideways inside itself on narrow screens, the page never does */
nav.bar { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 9; background: var(--background);
  border-bottom: 1px solid var(--border-subtle-00);
  margin-left: calc(-1 * max(16px, env(safe-area-inset-left, 0px)));
  margin-right: calc(-1 * max(16px, env(safe-area-inset-right, 0px)));
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
nav.bar .in { max-width: 1056px; margin: 0 auto; display: flex; gap: var(--sp-06); align-items: center;
  justify-content: space-between; overflow-x: auto; scrollbar-width: none; font-size: 14px; }
nav.bar .chs, nav.bar .secs { display: flex; gap: var(--sp-05); flex: none; }
nav.bar a { color: var(--text-primary); text-decoration: none; display: inline-flex; align-items: center; gap: 6px;
  white-space: nowrap; min-height: 44px; }
nav.bar a:hover { color: var(--link); }
nav.bar .ic { color: var(--sfg); }

/* status: Carbon read-only tag with a shape icon and a text label */
.tag { display: inline-flex; align-items: center; gap: var(--sp-02); height: 24px; padding: 0 var(--sp-03) 0 6px;
  border-radius: 12px; font-size: 12px; line-height: 1; letter-spacing: .32px; white-space: nowrap;
  color: var(--sfg); background: var(--sbg); }
.s-ok { --sfg: var(--st-slack-fg); --sbg: var(--st-slack-bg); }
.s-warn { --sfg: var(--st-watch-fg); --sbg: var(--st-watch-bg); }
.s-bad { --sfg: var(--st-binding-fg); --sbg: var(--st-binding-bg); }
.s-na { --sfg: var(--st-na-fg); --sbg: var(--st-na-bg); }
.ic { flex: none; display: block; }
.ic .f { fill: currentColor; }
.ic .k { fill: none; stroke: var(--sbg); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.ic .o { fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; }
abbr[title] { text-decoration: none; border-bottom: 1px dotted var(--text-helper); cursor: help; }

/* tiles */
.box { background: var(--layer-01); padding: var(--sp-05); display: grid; gap: var(--sp-04); align-content: start; min-width: 0; }
.group { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 1px; }
.group.inv { grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); }
.inv .box { gap: var(--sp-03); }
.inv-name { font-size: 14px; font-weight: 600; }
.box > .tag { justify-self: start; }
.card-head { display: flex; flex-wrap: wrap; gap: var(--sp-03) var(--sp-04); align-items: center; }
.q { font-size: 14px; color: var(--text-secondary); }
.box ul.plain { margin: 0; padding-left: 1.1em; display: grid; gap: var(--sp-03); font-size: 14px; }
.src { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }
.chainlist { list-style: none; margin: 0; padding: var(--sp-04) 0 0; display: grid; gap: var(--sp-04); font-size: 14px;
  border-top: 1px solid var(--border-subtle); }
.chainlist li { display: grid; gap: var(--sp-02); justify-items: start; }
.caption { font-size: 12px; color: var(--text-secondary); max-width: none; }

/* signal history: a data table, signal names stay put while the weeks scroll */
.hist { border-collapse: separate; border-spacing: 2px; }
.hist th { font-weight: 400; text-align: left; white-space: nowrap; }
.hist thead th { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); padding-bottom: 2px; }
.hist th.lab { position: sticky; left: 0; z-index: 1; background: var(--layer-01); max-width: 240px; overflow: hidden;
  text-overflow: ellipsis; padding-right: var(--sp-04); font-size: 13px; }
.hist tr.grp th { padding-top: var(--sp-04); font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.hist td { width: 18px; height: 18px; padding: 0; }
.hist td .ic { margin: auto; color: var(--sfg); }
.hist td.now { box-shadow: inset 0 0 0 1.5px var(--text-primary); }
.legend { display: flex; flex-wrap: wrap; gap: var(--sp-03) var(--sp-05); font-size: 12px; color: var(--text-secondary); align-items: center; }
.legend span { display: inline-flex; gap: 6px; align-items: center; }
.legend .ic { color: var(--sfg); }
@media (max-width: 671px) { .hist th.lab { max-width: 132px; } }

/* channel cards */
.cards { display: grid; gap: var(--sp-05); }
.code { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }
.card.off { background: transparent; border: 1px dashed var(--border-subtle); }
.sparks { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr)); gap: var(--sp-05); }
.spark { display: grid; gap: var(--sp-02); font-size: 12px; color: var(--text-secondary); min-width: 0; }
.spark .lab { display: flex; justify-content: space-between; align-items: baseline; gap: var(--sp-03); }
.spark .lab .end { font-size: 14px; color: var(--text-primary); }
.spark svg { width: 100%; height: 48px; display: block; overflow: visible; }
.spark .line { fill: none; stroke: var(--chart-1); stroke-width: 1.5; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
.spark .area { fill: var(--chart-1); opacity: .08; }
.spark .end-dot { fill: none; stroke: var(--chart-1); stroke-width: 6; stroke-linecap: round; vector-effect: non-scaling-stroke; }

/* expandable logs: Carbon accordion row */
details { border-top: 1px solid var(--border-subtle); }
details > summary { list-style: none; cursor: pointer; display: flex; align-items: center; justify-content: space-between;
  gap: var(--sp-03); min-height: 44px; font-size: 14px; color: var(--text-primary); }
details > summary::-webkit-details-marker { display: none; }
details > summary::after { content: ""; flex: none; width: 7px; height: 7px; margin-right: 6px;
  border-right: 1.5px solid currentColor; border-bottom: 1.5px solid currentColor; transform: rotate(45deg);
  transition: transform .11s; }
details[open] > summary::after { transform: rotate(-135deg); }
details > summary:hover { background: var(--layer-hover); }
.log { display: grid; gap: var(--sp-04); padding-block: var(--sp-03) var(--sp-05); }
.log h2 { font-size: 16px; font-weight: 600; line-height: 1.5; margin-top: var(--sp-04); }
.log ul, .log ol { margin: 0; padding-left: 1.2em; display: grid; gap: var(--sp-02); }
.log table, table.t { border-collapse: collapse; width: 100%; font-size: 14px; line-height: 1.43; }
.log th, table.t th { background: var(--layer-accent); font-weight: 600; text-align: left; padding: var(--sp-03) var(--sp-05);
  white-space: nowrap; }
.log td, table.t td { text-align: left; padding: var(--sp-03) var(--sp-05); border-bottom: 1px solid var(--border-subtle);
  vertical-align: top; }
table.t td .tag { margin-left: var(--sp-03); vertical-align: middle; }
.scroll { overflow-x: auto; }
footer { font-size: 12px; line-height: 1.5; color: var(--text-secondary); display: grid; gap: var(--sp-02);
  border-top: 1px solid var(--border-subtle-00); padding-top: var(--sp-05); }
@media (prefers-reduced-motion: reduce) { details > summary::after { transition: none; } }
"""

def _t():
    return T[lang()]


_GLOSSARY = {}
# A citation that is only IDs in brackets, e.g. "（S-L3-03、INF-02）": the name next to it already says it
_PAREN_IDS = re.compile(r'\s?[（(]\s*(?:见|see)?\s*(?:{id})(?:\s*(?:[、,，/;；]|和|及|与|and)\s*(?:{id}))*\s*[）)]'
                        .format(id=ID_RE.pattern))


def _label(i):
    """Reader-facing name of a signal or rule ID (playbook/glossary.yaml); the ID itself if it has none."""
    if not _GLOSSARY:
        _GLOSSARY.update(glossary())
    g = _GLOSSARY.get(i)
    return g[lang()] if g else i


def _human(text):
    """Leftover internal IDs become their names, with the ID in a tooltip. Works on escaped HTML or Markdown."""
    def name(m):
        sep = '、' if lang() == 'zh' else ' and '
        return f'<abbr title="{m.group(0)}">{sep.join(_label(i) for i in expand_id(m.group(0)))}</abbr>'
    return ID_RE.sub(name, _PAREN_IDS.sub('', text))


def _h(text):
    return _human(html.escape(text))


# Four states, four shapes, so a state never depends on color alone: slack a filled circle, watch a triangle,
# binding a diamond, no data a hollow circle. The knock-out mark inside is drawn only at tag size.
_SHAPES = {
    'ok': ('<circle cx="8" cy="8" r="7" class="f"/>', '<path d="M4.6 8.3l2.2 2.2 4.6-4.8" class="k"/>'),
    'warn': ('<path d="M8 1.2 15.2 14.4H.8z" class="f"/>', '<path d="M8 6v3.6M8 11.8v.2" class="k"/>'),
    'bad': ('<path d="M8 .8 15.2 8 8 15.2.8 8z" class="f"/>', '<path d="M5.9 5.9l4.2 4.2M10.1 5.9l-4.2 4.2" class="k"/>'),
    'na': ('<circle cx="8" cy="8" r="6.2" class="o"/>', '<path d="M5.4 8h5.2" class="o"/>'),
}
INV_CLASS = {'稳': 'ok', 'Stable': 'ok', '受压': 'warn', 'Under pressure': 'warn', '动摇': 'bad', 'Shaken': 'bad'}


def _icon(cls, size=16, mark=True):
    shape, sym = _SHAPES.get(cls, _SHAPES['na'])
    return (f'<svg class="ic" viewBox="0 0 16 16" width="{size}" height="{size}" aria-hidden="true">'
            f'{shape}{sym if mark else ""}</svg>')


def _tag(cls, text):
    return f'<span class="tag s-{cls}">{_icon(cls)}{html.escape(text)}</span>'


def _pill(state):
    return _tag(STATE_CLASS.get(state, 'na'), _t()['state'].get(state, state))


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
    w, h, pad = 240, 48, 4
    pts = [(pad + i * (w - 2 * pad) / (len(vals) - 1), pad + (h - 2 * pad) * (1 - (v - lo) / span))
           for i, v in enumerate(vals)]
    line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    area = f'{pts[0][0]:.1f},{h - pad} ' + line + f' {pts[-1][0]:.1f},{h - pad}'
    x, y = pts[-1]
    fmt = (lambda v: f'{v:,.0f}') if abs(vals[-1]) >= 1000 else (lambda v: f'{v:.2f}')
    # The end dot is a zero-length round-capped stroke, so it stays round when the SVG stretches to the card width
    return (f'<div class="spark"><div class="lab"><span>{html.escape(label)}</span>'
            f'<span class="mono end">{fmt(vals[-1])}</span></div>'
            f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" role="img" '
            f'aria-label="{html.escape(label)}: {fmt(vals[0])} → {fmt(vals[-1])}, {t["range"]} {fmt(lo)}–{fmt(hi)}">'
            f'<polygon class="area" points="{area}"/><polyline class="line" points="{line}"/>'
            f'<path class="end-dot" d="M{x:.1f} {y:.1f}h0"/></svg>'
            f'<div class="lab mono"><span>{rows[0][0]} {t["since"]}</span>'
            f'<span>{t["range"]} {fmt(lo)}–{fmt(hi)}</span></div></div>')


def _log_body(text):
    text = re.sub(r'```json.*?```', '', text, flags=re.S)
    text = re.sub(r'^# .*\n', '', text, count=1)
    text = re.sub(r'^\*\*(状态|一句话|动作含义|State|One line|Action)\*\*\s*[:：].*\n', '', text, flags=re.M)
    out = markdown.markdown(_human(text), extensions=['tables'])
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
        cells.append(f'<a href="#hz-{h}" class="tile-link"><span class="hz-name">{name}</span>'
                     f'<span class="hz-sub">{sub}</span>{_pill(state)}</a>')
    return (f'<header class="mast"><div class="mast-top"><span class="eyebrow">{t["eyebrow"]}</span>'
            f'<span class="issue">{rid} · {t["asof"].format(asof=asof, today=dt.date.today())}</span></div>'
            f'<h1 class="action" id="synthesis">{_h(action)}</h1>'
            f'<div class="callout"><p>{_h(verdict)}</p></div>'
            f'<div class="track">{"".join(cells)}</div></header>')


def _nav(judg, defs):
    t = _t()
    chs = []
    for c in FILES:
        state = _split(judg[(1, c)]['state'])[0] if (1, c) in judg else 'na'
        label = t['state'].get(state, state)
        chs.append(f'<a href="#{c}" title="{label}" class="s-{STATE_CLASS.get(state, "na")}">'
                   f'{_icon(STATE_CLASS.get(state, "na"), 12, mark=False)}{localized(defs["channels"][c], "name")}'
                   f'<span class="vh">{label}</span></a>')
    secs = ''.join(f'<a href="#{k}">{v}</a>' for k, v in t['nav'].items())
    return f'<nav class="bar" aria-label="sections"><div class="in"><div class="chs">{"".join(chs)}</div><div class="secs">{secs}</div></div></nav>'


def _synthesis(judg, run_dir):
    t = _t()
    s = judg.get((3, 'all'))
    if not s:
        return f'<div class="callout">{t["no_l3"]}</div>'
    tiles = []
    for k, v in sorted(s.items()):
        if not k.startswith('invariant:'):
            continue
        state, why = _split(v)
        inv = k.split(':', 1)[1]
        tiles.append(f'<div class="box"><span class="inv-name" title="{inv}">{html.escape(_label(inv))}</span>'
                     f'{_tag(INV_CLASS.get(state, "na"), state)}<p class="small">{_h(why)}</p></div>')
    log = run_dir / 'synthesis.md'
    body = _log_body(log.read_text(encoding='utf-8')) if log.exists() else ''
    return (f'<div class="sec-head"><h2>{t["sec"]["invariants"]}</h2></div><div class="group inv">{"".join(tiles)}</div>'
            f'<div class="box"><details><summary>{t["full_synth"]}</summary><div class="log">{body}</div></details></div>')


def _horizons(judg, run_dir, defs):
    t = _t()
    cols = []
    for h in ('far', 'mid', 'near'):
        name, sub, question = t['hz'][h]
        s = judg.get((2, h))
        if s:
            state, verdict = _split(s['state'])
            chains = []
            for k, v in sorted(s.items()):
                if not k.startswith('chain:'):
                    continue
                status, why = _split(v)
                ch = k.split(':', 1)[1]
                cls = 'warn' if re.search(r'传导中|Transmitting', status) else 'na'
                chains.append(f'<li title="{ch}">{_tag(cls, status)}'
                              f'<span><strong>{html.escape(_label(ch))}</strong> {_h(why)}</span></li>')
            log = run_dir / f'{h}.md'
            body = _log_body(log.read_text(encoding='utf-8')) if log.exists() else ''
            cols.append(f'<div class="box" id="hz-{h}"><div class="card-head"><h3>{name} · {sub}</h3>{_pill(state)}</div>'
                        f'<p class="q">{question}</p><p class="small">{_h(verdict)}</p>'
                        + (f'<ul class="chainlist">{"".join(chains)}</ul>' if chains else '')
                        + f'<details><summary>{t["full_hz"]}</summary><div class="log">{body}</div></details></div>')
            continue
        items = [(c, judg[(1, c)][f'horizon:{h}']) for c in FILES if (1, c) in judg and f'horizon:{h}' in judg[(1, c)]]
        lis = ''.join(f'<li><span class="src">{c} {localized(defs["channels"][c], "name")}</span><br>{_h(v)}</li>'
                      for c, v in items) or f'<li class="muted">{t["no_hz"]}</li>'
        cols.append(f'<div class="box" id="hz-{h}"><div class="card-head"><h3>{name} · {sub}</h3></div>'
                    f'<p class="q">{t["no_l2"]}</p><ul class="plain">{lis}</ul></div>')
    sep = '；' if lang() == 'zh' else '; '
    colon = '：' if lang() == 'zh' else ': '
    chains_cap = sep.join(f'{_label(k)}{colon}{v}' for k, v in t['chains'].items())
    return f'<div class="group">{"".join(cols)}</div><p class="caption">{t["chains_cap"]}{colon}{chains_cap}</p>'


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
    # Week labels every 4 columns, so the header never widens the cells
    groups = ''.join(f'<th scope="colgroup" colspan="{len(runs[i:i + 4])}">{runs[i][-3:]}</th>' for i in range(0, len(runs), 4))
    rows = [f'<thead><tr><th class="lab" scope="col">{t["hist_head"]}</th>{groups}</tr></thead><tbody>']
    for c, meta in defs['channels'].items():
        if not meta['signals']:
            continue
        rows.append(f'<tr class="grp"><th class="lab" scope="rowgroup" colspan="{len(runs) + 1}">'
                    f'{c} {localized(meta, "name")}</th></tr>')
        for sid in meta['signals']:
            row = []
            for r in runs:
                st, v, m = cells.get((r, sid), ('na', None, ''))
                cls = STATE_CLASS.get(st, 'na')
                val = '' if v is None else f' · {v:,.2f}'
                tag = ' (backfill)' if m == 'backfill' and lang() == 'en' else '（回补）' if m == 'backfill' else ''
                label = t['state'].get(st, st)
                row.append(f'<td class="s-{cls}{" now" if r == rid else ""}" title="{r} {html.escape(_label(sid))}: '
                           f'{label}{val}{tag}">{_icon(cls, 12, mark=False)}<span class="vh">{r} {label}</span></td>')
            name = localized(by_id[sid], 'name')
            rows.append(f'<tr><th class="lab" scope="row" title="{sid} · {html.escape(name)}">{html.escape(_label(sid))}</th>'
                        f'{"".join(row)}</tr>')
    rows.append('</tbody>')
    first_live = con.execute("SELECT min(run_id) FROM signal_history WHERE mode = 'live'").fetchone()[0]
    legend = ''.join(f'<span class="s-{STATE_CLASS[k]}">{_icon(STATE_CLASS[k], 12, mark=False)}{v}</span>'
                     for k, v in t['state'].items())
    return (f'<div class="box"><div class="scroll"><table class="hist">{"".join(rows)}</table></div>'
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
                         f'<h3>{name}</h3>{_tag("na", t["no_log"])}</div></div>')
            continue
        state, verdict = _split(judg[(1, c)]['state'])
        sparks = ''.join(_spark(con, sid, ent, t['sparks'][sid], asof) for sid, ent in SPARKS.get(c, []))
        weight = f'<span class="muted small">{t["low_weight"]}</span>' if meta.get('weight') == 'low' else ''
        cards.append(
            f'<div class="box card" id="{c}"><div class="card-head"><span class="code">{c}</span>'
            f'<h3>{name}</h3>{_pill(state)}{weight}</div><p>{_h(verdict)}</p>'
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


# A series is flagged when its latest observation is older than this many days, by its registry frequency
STALE_DAYS = {'daily': 5, 'weekly': 12, 'monthly': 50, 'quarterly': 140}


def _freshness(con):
    t = _t()
    freq = {s['id']: s.get('freq') for s in registry()['series']}
    today = dt.date.today()
    rows = [(sid, t['series'].get(sid, sid), d, r, freq.get(sid)) for sid, d, r in con.execute("""
        SELECT o.series_id, max(o.obs_date), (SELECT max(retrieved_at) FROM raw_fetch f WHERE f.series_id = o.series_id)
        FROM obs_latest o GROUP BY 1 ORDER BY 1""").fetchall()]
    rows += [(k, t['event'] + t['series'].get(k, k), d, r, None) for k, d, r in con.execute("""
        SELECT kind, max(event_date), (SELECT max(retrieved_at) FROM raw_fetch f WHERE f.fetch_id = max(e.fetch_id))
        FROM events e GROUP BY 1 ORDER BY 1""").fetchall()]
    h = t['fresh_head']
    body = []
    for sid, name, d, r, f in rows:
        stale = f in STALE_DAYS and d is not None and (today - d).days > STALE_DAYS[f]
        body.append(f'<tr><td title="{sid}">{html.escape(name)}</td><td class="mono">{d}'
                    f'{_tag("warn", t["stale"]) if stale else ""}</td>'
                    f'<td class="mono">{(r.strftime("%Y-%m-%d %H:%M") + " UTC") if r else "—"}</td></tr>')
    return (f'<div class="box scroll"><table class="t"><thead><tr><th>{h[0]}</th><th>{h[1]}</th><th>{h[2]}</th></tr>'
            f'</thead><tbody>{"".join(body)}</tbody></table></div>')


def render(con, rid):
    t = _t()
    defs = signal_defs()
    run_dir = ROOT / 'logs' / rid
    asof = con.execute('SELECT max(as_of) FROM signals WHERE run_id = ?', [rid]).fetchone()[0] or dt.date.today()
    judg = _judgments(con, rid)
    css = CSS.replace('__SANS__', t['font']).replace('__LH__', t['lh'])
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
<div class="wrap" lang="{t['html_lang']}" style="margin-top: var(--sp-07)">
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
