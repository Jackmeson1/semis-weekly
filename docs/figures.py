"""Diagrams for the README: python docs/figures.py -> docs/img/<name>.svg

Labels live in L, keyed by language, so a translation is one more entry. Colors are the page's IBM Carbon tokens and follow the
reader's color scheme; fonts are system fonts because GitHub shows SVGs as images, which cannot load web fonts.
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / 'img'

STYLE = """<style>
svg { --bg: #f4f4f4; --node: #ffffff; --fg: #161616; --fg2: #525252; --fg3: #6f6f6f; --line: #c6c6c6;
  --acc: #0f62fe; --acc-bg: #edf5ff; --ok: #0e6027; --ok-bg: #defbe6; --warn: #684e00; --warn-bg: #fcf4d6;
  --bad: #a2191f; --na: #525252; --na-bg: #e0e0e0; }
@media (prefers-color-scheme: dark) { svg { --bg: #262626; --node: #161616; --fg: #f4f4f4; --fg2: #c6c6c6;
  --fg3: #a8a8a8; --line: #525252; --acc: #78a9ff; --acc-bg: #1c2a44; --ok: #6fdc8c; --ok-bg: #044317;
  --warn: #f1c21b; --warn-bg: #302400; --bad: #ff8389; --na: #c6c6c6; --na-bg: #393939; } }
.bg { fill: var(--bg); }
text { fill: var(--fg); font: 13px -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif; }
.b { font-weight: 600; } .big { font-size: 16px; } .t2 { fill: var(--fg2); font-size: 11.5px; } .t3 { fill: var(--fg3); font-size: 11px; }
.m { font-family: ui-monospace, Consolas, monospace; }
.n { fill: var(--node); stroke: var(--line); } .acc { fill: var(--acc-bg); stroke: var(--acc); stroke-width: 1.5; }
.dim { fill: none; stroke: var(--line); stroke-dasharray: 4 3; }
.watch { fill: var(--warn-bg); stroke: var(--warn); stroke-width: 1.2; } .slack { fill: var(--ok-bg); stroke: var(--ok); stroke-width: 1.2; }
.nabg { fill: var(--na-bg); }
.e { fill: none; stroke: var(--fg3); stroke-width: 1.3; } .dash { stroke-dasharray: 4 3; }
.strong { stroke: var(--bad); stroke-width: 2.4; } .stop { stroke: var(--fg2); stroke-width: 2.5; stroke-linecap: round; }
.ah { fill: var(--fg3); } .ahs { fill: var(--bad); }
.c-ok { fill: var(--ok); } .c-warn { fill: var(--warn); } .c-bad { fill: var(--bad); }
.o-na { fill: none; stroke: var(--na); stroke-width: 1.6; }
</style>"""

ARROWS = ('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
          '<path d="M0 0L10 5L0 10z" class="ah"/></marker>'
          '<marker id="s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
          '<path d="M0 0L10 5L0 10z" class="ahs"/></marker></defs>')


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def T(x, y, s, cls='', anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ''
    c = f' class="{cls}"' if cls else ''
    return f'<text x="{x}" y="{y}"{c}{a}>{esc(s)}</text>'


def R(x, y, w, h, cls='n', rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"' + (f' rx="{rx}"' if rx else '') + '/>'


def P(d, cls='e', end='a'):
    return f'<path d="{d}" class="{cls}"' + (f' marker-end="url(#{end})"' if end else '') + '/>'


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{esc(label)}">{STYLE}{ARROWS}<rect class="bg" width="{w}" height="{h}" rx="6"/>'
            f'{"".join(body)}</svg>\n')


# ---------- labels ----------

L = {
    'en': {
        'channels_label': 'The seven channels, their data sources, and which horizon each one feeds',
        'channels': [('C1', 'Credit', 'FRED · SEC', 'HY and IG spreads · cloud capex vs cash flow'),
                     ('C2', 'Rates', 'FRED · Treasury', '10-year yield · yield curve · Treasury auctions'),
                     ('C3', 'Liquidity plumbing', 'FRED', 'Fed assets · Treasury cash (TGA) · reverse repo'),
                     ('C4', 'Positioning', 'Cboe · CFTC', 'VIX · dealer gamma from option chains · futures'),
                     ('C5', 'Industry', 'Taiwan revenue · SEC', 'TSMC and AI-server revenue · cloud capex growth'),
                     ('C6', 'Company results', 'SEC', 'Results releases from 13 companies'),
                     ('C7', 'Policy and events', 'Fed · Treasury', 'FOMC statements · auction calendar')],
        'hz': [('Far · 6 months+', 'Does the direction still hold?', 'Industry, AI demand, funding'),
               ('Mid · one earnings season', 'How big, and hedged or not?', 'Credit, liquidity, results, policy'),
               ('Near · under 2 weeks', 'Is now a good time to act?', 'Positioning, speed of rates')],

        'rank_label': 'Who decides at each horizon: positioning near term; credit, liquidity, industry and AI demand in the '
                      'mid term; industry, AI demand and Treasury supply far out; the rate-cut path last everywhere',
        'rank_heads': ['Near · under 2 weeks', 'Mid · one earnings season', 'Far · 6 months+'],
        'rank_sub': 'Who decides (longer bar, more weight)',
        'rank': [[('Positioning', 270, 'acc'), ('Everything else', 150, 'n'), ('Company, policy', 120, 'dim')],
                 [('Credit', 250, 'acc'), ('Liquidity', 250, 'acc'), ('Industry cycle', 250, 'acc'),
                  ('AI demand', 250, 'acc'), ('Company results', 130, 'dim'), ('Macro policy', 110, 'dim')],
                 [('Industry', 270, 'acc'), ('AI demand', 270, 'acc'), ('Treasury supply', 270, 'acc'),
                  ('Company, policy', 120, 'dim')]],
        'rank_foot': "Last at every horizon: the Fed's rate-cut path",

        'veto_label': 'Four things that can overturn the direction and for how long, and four that cannot',
        'veto_heads': ('Can overturn the direction', 'Cannot overturn it'),
        'vetoes': [('Funding break', 'Credit tightens; capex outruns cash flow', 'Changes direction', 'c-bad'),
                   ('Rates rise too fast', 'Speed, not level', 'Vetoes for weeks', 'c-warn'),
                   ('Extreme positioning', 'Negative dealer gamma, vol shock', 'Timing only', 'c-warn'),
                   ('Policy shock', 'Tariffs, export controls', 'Until it expires', 'c-warn')],
        'center': ('Chip direction', "Premise: AI demand doesn't peak"),
        'noveto': [('Level of long rates', 'Solid assets fear speed, not level'), ('Rate-cut path', 'Last at every horizon'),
                   ('Bubble and crash talk', 'Ignored'), ('Minor industry delays', 'A matter of time; watch demand')],

        'chain_label': 'Four transmission chains; in 2026-W44 the second, credit into cloud capex, is transmitting',
        'chains': [['Rate volatility', 'Credit', 'Cloud funding', 'Industry'], ['Credit', 'Cloud capex', 'Industry'],
                   ['Vol shock', 'Forced selling', 'Deleveraging'], ['Policy shock', 'Long rates', 'Credit']],
        'chain_b_states': ['Near', 'Near · 0.85', 'Not moved yet'],
        'not_seen': 'Not seen', 'transmitting': 'Transmitting',

        'action_label': '2026-W44: the direction holds, no added leverage, no new buying yet; together, hold and add a small hedge',
        'roles': [('Far sets the direction', 'Not binding', 'Direction holds', 136),
                  ('Mid sets size and hedging', 'Near', 'Hold size, no leverage', 96),
                  ('Near sets the timing', 'Binding', "Don't add yet", 114)],
        'action': ('Hold, add a small hedge', 'Action for 2026-W44'),

        'pipe_label': 'Pipeline: free data, 15 indicators, 7 channel logs, far/mid/near logs, synthesis, web page; a '
                      'check after each of the three levels sends failures back',
        'pipe_edges': ['store', 'input packets', 'reads level below', 'reads level below', 'render'],
        'pipe': [(None, 'Free data', '7 sources, daily'), (None, '15 indicators', 'computed by code'),
                 ('Level 1', '7 channel logs', 'one model per channel'), ('Level 2', 'Far, mid, near', 'three horizon logs'),
                 ('Level 3', 'Synthesis', 'one action'), (None, 'Web page', 'one per week')],
        'gate': 'Check: every number has a source, no internal codes', 'gate_fail': 'Fails → rewrite',
    },
}


# ---------- figures ----------

def channels(t):
    b = []
    for i, (code, name, src, sub) in enumerate(t['channels']):
        y = 20 + 58 * i
        b += [R(20, y, 380, 46), f'<text x="34" y="{y + 19}" class="b"><tspan class="m t3">{code}</tspan>'
              f'<tspan dx="8">{esc(name)}</tspan></text>',
              T(388, y + 19, src, 't3 m', 'end'), T(34, y + 37, sub, 't2')]
    for (title, q, what), y in zip(t['hz'], (24, 166, 308)):
        b += [R(640, y, 300, 96, 'acc'), T(656, y + 28, title, 'b big'), T(656, y + 51, q, 't2'), T(656, y + 75, what, 't3')]
    # channel exit y -> horizon entry y
    for y1, y2 in ((37, 62), (49, 186), (95, 200), (107, 334), (159, 214), (217, 356), (275, 92), (333, 228), (391, 242)):
        b.append(P(f'M400 {y1}C520 {y1} 520 {y2} 636 {y2}'))
    return svg(960, 424, t['channels_label'], b)


def ranking(t):
    b = [T(20, 42, t['rank_sub'], 't2')]
    for x, head, bars in zip((20, 345, 670), t['rank_heads'], t['rank']):
        b.append(T(x, 22, head, 'b big'))
        for j, (label, w, cls) in enumerate(bars):
            y = 60 + 38 * j
            b += [R(x, y, w, 30, cls), T(x + 12, y + 20, label, 't2' if cls == 'dim' else ('b' if cls == 'acc' else ''))]
    b += ['<line x1="20" y1="296" x2="940" y2="296" class="e dash"/>', T(20, 314, t['rank_foot'], 't2')]
    return svg(960, 326, t['rank_label'], b)


def vetoes(t):
    left, right = t['veto_heads']
    b = [T(20, 20, left, 'b'), T(940, 20, right, 'b', 'end')]
    ys = (36, 114, 192, 270)
    for y, (title, sub, how, cls) in zip(ys, t['vetoes']):
        b += [R(20, y, 290, 58), T(34, y + 23, title, 'b'), T(296, y + 23, how, f'b {cls}', 'end'), T(34, y + 44, sub, 't2')]
    for y, (title, sub) in zip(ys, t['noveto']):
        b += [R(650, y, 290, 58), T(664, y + 23, title, 'b'), T(664, y + 44, sub, 't2')]
    big, small = t['center']
    b += [R(370, 146, 220, 74, 'acc'), T(480, 178, big, 'b big', 'middle'), T(480, 201, small, 't2', 'middle')]
    targets = (158, 175, 192, 209)
    b.append(P(f'M310 65C350 65 345 158 364 158', 'e strong', 's'))
    for y, ty in zip(ys[1:], targets[1:]):
        b.append(P(f'M310 {y + 29}C345 {y + 29} 345 {ty} 366 {ty}'))
    for y, ty in zip(ys, targets):
        b.append(P(f'M650 {y + 29}C615 {y + 29} 620 {ty} 602 {ty}', 'e dash', None))
    b.append('<path class="stop" d="M598 152V164M598 169V181M598 186V198M598 203V215"/>')
    return svg(960, 346, t['veto_label'], b)


def chains(t):
    b = [T(888, 16, '2026-W44', 't2', 'middle')]
    xs = (20, 230, 440, 650)
    for i, chain in enumerate(t['chains']):
        y = 28 + 68 * i
        for j, name in enumerate(chain):
            x = xs[j]
            if i == 1:
                state, cls, tcls = t['chain_b_states'][j], ('watch', 'watch', 'slack')[j], ('c-warn', 'c-warn', 'c-ok')[j]
                b += [R(x, y, 150, 46, cls), T(x + 75, y + 20, name, 'b', 'middle'), T(x + 75, y + 37, state, f't2 {tcls}', 'middle')]
            else:
                b += [R(x, y, 150, 46), T(x + 75, y + 28, name, '', 'middle')]
            if j:
                b.append(P(f'M{xs[j - 1] + 150} {y + 23}H{x - 4}'))
        if i == 1:
            b += [R(836, y + 10, 104, 26, 'watch', 13), f'<path d="M854 {y + 16.5}L860 {y + 28}H848z" class="c-warn"/>',
                  T(866, y + 27, t['transmitting'], 't2 c-warn b')]
        else:
            b += [R(836, y + 10, 104, 26, 'nabg', 13), f'<circle cx="854" cy="{y + 23}" r="5" class="o-na"/>',
                  T(866, y + 27, t['not_seen'], 't2')]
    return svg(960, 296, t['chain_label'], b)


def action(t):
    b = []
    shapes = ('<circle cx="42" cy="{c}" r="6" class="c-ok"/>', '<path d="M42 {a}L48.5 {d}H35.5z" class="c-warn"/>',
              '<path d="M42 {a}L48.5 {c}L42 {d}L35.5 {c}z" class="c-bad"/>')
    for i, (role, state, result, rx) in enumerate(t['roles']):
        y = 16 + 70 * i
        c = y + 42
        b += [R(20, y, 330, 58), T(36, y + 24, role, 'b'),
              shapes[i].format(c=c, a=c - 6.5, d=c + 6.5 if i == 2 else c + 5),
              T(56, y + 46, state, f't2 b {("c-ok", "c-warn", "c-bad")[i]}'), T(rx, y + 46, result, 't2')]
    b += [P('M350 45C470 45 470 98 596 98'), P('M350 115H596'), P('M350 185C470 185 470 132 596 132')]
    big, small = t['action']
    b += [R(600, 76, 340, 78, 'acc'), T(770, 112, big, 'b big', 'middle'), T(770, 136, small, 't2', 'middle')]
    return svg(960, 228, t['action_label'], b)


def pipeline(t):
    b = []
    xs = (10, 172, 334, 496, 658, 820)
    for x, label in zip((156, 318, 480, 642, 804), t['pipe_edges']):
        b.append(T(x, 46, label, 't3', 'middle'))
    for x, (level, title, sub) in zip(xs, t['pipe']):
        cx = x + 65
        if level:
            b += [R(x, 60, 130, 74, 'acc'), T(cx, 78, level, 't3 m', 'middle'), T(cx, 100, title, 'b', 'middle'),
                  T(cx, 120, sub, 't2', 'middle')]
        else:
            b += [R(x, 60, 130, 74), T(cx, 92, title, 'b', 'middle'), T(cx, 114, sub, 't2', 'middle')]
    b += [P(f'M{x + 130} 97H{nx - 4}') for x, nx in zip(xs, xs[1:])]
    b += [R(334, 178, 454, 38, 'watch'), T(561, 202, t['gate'], 't2 c-warn b', 'middle')]
    b += [P(f'M{x} 178V140', 'e dash') for x in (399, 561, 723)]
    b.append(T(796, 202, t['gate_fail'], 't2'))
    return svg(960, 236, t['pipe_label'], b)


FIGURES = {'channels': channels, 'horizons': ranking, 'vetoes': vetoes, 'chains': chains, 'action': action,
           'pipeline': pipeline}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for name, draw in FIGURES.items():
        (OUT / f'{name}.svg').write_text(draw(L['en']), encoding='utf-8')
        print(f'docs/img/{name}.svg')
