// An animated walk through the five layers of the macro part, one scene per layer. Geometry matches
// docs/figures.py so the video and the README diagrams read as one set. Colors are the page's IBM Carbon tokens.
import React from 'react';
import {AbsoluteFill, Easing, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const C = {
  bg: '#ffffff', panel: '#f4f4f4', node: '#ffffff', fg: '#161616', fg2: '#525252', fg3: '#6f6f6f', line: '#c6c6c6',
  acc: '#0f62fe', accBg: '#edf5ff', ok: '#0e6027', okBg: '#defbe6', warn: '#684e00', warnBg: '#fcf4d6',
  bad: '#a2191f', badBg: '#fff1f1', na: '#525252', naBg: '#e0e0e0',
};
const FONT = '"Segoe UI", "Helvetica Neue", Arial, system-ui, sans-serif';
const MONO = 'Consolas, "IBM Plex Mono", ui-monospace, monospace';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// 0 -> 1 over `len` frames starting at `start`
const ramp = (f: number, start: number, len = 15) =>
  interpolate(f, [start, start + len], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});

const useSpring = (start: number) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: Math.max(0, f - start), fps, config: {damping: 200}});
};

type SceneProps = {dur: number};

const Scene: React.FC<{dur: number; layer: string; title: string; caption: string; vb: string; children: React.ReactNode}> =
  ({dur, layer, title, caption, vb, children}) => {
    const f = useCurrentFrame();
    const opacity = interpolate(f, [0, 12, dur - 12, dur], [0, 1, 1, 0], clamp);
    return (
      <AbsoluteFill style={{background: C.bg, fontFamily: FONT, color: C.fg, opacity, padding: '40px 72px 40px',
        display: 'flex', flexDirection: 'column'}}>
        <div style={{fontSize: 20, color: C.fg2, letterSpacing: 1}}>{layer}</div>
        <div style={{fontSize: 42, marginTop: 4}}>{title}</div>
        <div style={{fontSize: 24, color: C.fg2, marginTop: 8, opacity: ramp(f, 10, 20)}}>{caption}</div>
        <div style={{marginTop: 24, background: C.panel, padding: 20, flex: 1, minHeight: 0, display: 'flex'}}>
          <svg viewBox={vb} style={{width: '100%', height: '100%'}} fontFamily={FONT}>
            <defs>
              <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
                <path d="M0 0L10 5L0 10z" fill={C.fg3}/>
              </marker>
              <marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto">
                <path d="M0 0L10 5L0 10z" fill={C.bad}/>
              </marker>
            </defs>
            {children}
          </svg>
        </div>
      </AbsoluteFill>
    );
  };

// A path that draws itself as p goes 0 -> 1; the arrowhead appears once the line arrives
const Edge: React.FC<{d: string; p: number; strong?: boolean; dashed?: boolean; arrow?: boolean}> =
  ({d, p, strong = false, dashed = false, arrow = true}) => (
    <path d={d} fill="none" stroke={strong ? C.bad : C.fg3} strokeWidth={strong ? 3 : 1.6} pathLength={1}
      strokeDasharray={dashed ? '0.012 0.008' : 1} strokeDashoffset={dashed ? 0 : 1 - p} opacity={dashed ? p : 1}
      markerEnd={arrow && p > 0.97 ? `url(#${strong ? 'ahs' : 'ah'})` : undefined}/>
  );

const Txt: React.FC<{x: number; y: number; s: string; size?: number; color?: string; bold?: boolean;
  anchor?: 'start' | 'middle' | 'end'; mono?: boolean}> =
  ({x, y, s, size = 15, color = C.fg, bold = false, anchor = 'start', mono = false}) => (
    <text x={x} y={y} fontSize={size} fill={color} fontWeight={bold ? 700 : 400} textAnchor={anchor}
      fontFamily={mono ? MONO : FONT}>{s}</text>
  );

// ---------- scenes ----------

const Title: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  const opacity = interpolate(f, [0, 15, dur - 15, dur], [0, 1, 1, 0], clamp);
  const lift = interpolate(useSpring(0), [0, 1], [24, 0]);
  return (
    <AbsoluteFill style={{background: C.bg, fontFamily: FONT, opacity, justifyContent: 'center', padding: '0 120px'}}>
      <div style={{fontSize: 22, color: C.fg2, letterSpacing: 1}}>semis-weekly · a far-layer weekly for chip investors</div>
      <div style={{fontSize: 60, marginTop: 12, transform: `translateY(${lift}px)`}}>How the far-layer weekly works</div>
      <div style={{fontSize: 26, color: C.fg2, marginTop: 28, lineHeight: 1.6, opacity: ramp(f, 30, 25),
        borderLeft: `4px solid ${C.acc}`, paddingLeft: 24, background: C.accBg, padding: '16px 24px'}}>
        Macro is the brakes; earnings and the industry are the accelerator.<br/>While the brakes are off, earnings are enough. Once they are on, they decide.
      </div>
    </AbsoluteFill>
  );
};

const CHANNELS: [string, string, string][] = [
  ['C1', 'Credit', 'FRED · SEC'], ['C2', 'Rates', 'FRED · Treasury'], ['C3', 'Liquidity plumbing', 'FRED'],
  ['C4', 'Positioning', 'Cboe · CFTC'], ['C5', 'Industry', 'Taiwan revenue · SEC'], ['C6', 'Company results', 'SEC'],
  ['C7', 'Policy and events', 'Fed · Treasury'],
];
const HORIZONS: [string, string][] = [['Far · 6 months+', 'Does the direction still hold?'],
  ['Mid · one earnings season', 'How big, and hedged or not?'], ['Near · under 2 weeks', 'Is now a good time to act?']];
const CH_EDGES: [number, number][] = [[37, 62], [49, 186], [95, 200], [107, 334], [159, 214], [217, 356], [275, 92],
  [333, 228], [391, 242]];

const Channels: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  return (
    <Scene dur={dur} layer="Layer 1" title="Seven channels, each reading only its own data"
      caption="Each writes its own call, which then feeds the far, mid and near horizons." vb="0 0 960 424">
      {CHANNELS.map(([code, name, src], i) => {
        const y = 20 + 58 * i;
        const p = ramp(f, 15 + 8 * i, 12);
        return (
          <g key={code} opacity={p} transform={`translate(${(1 - p) * -20} 0)`}>
            <rect x={20} y={y} width={380} height={46} fill={C.node} stroke={C.line}/>
            <Txt x={34} y={y + 29} s={code} size={13} color={C.fg3} mono/>
            <Txt x={68} y={y + 29} s={name} size={17} bold/>
            <Txt x={388} y={y + 29} s={src} size={13} color={C.fg3} anchor="end"/>
          </g>
        );
      })}
      {HORIZONS.map(([title, q], i) => {
        const y = [24, 166, 308][i];
        return (
          <g key={title} opacity={ramp(f, 75, 15)}>
            <rect x={640} y={y} width={300} height={96} fill={C.accBg} stroke={C.acc} strokeWidth={1.5}/>
            <Txt x={656} y={y + 40} s={title} size={19} bold/>
            <Txt x={656} y={y + 70} s={q} size={15} color={C.fg2}/>
          </g>
        );
      })}
      {CH_EDGES.map(([y1, y2], k) => (
        <Edge key={k} d={`M400 ${y1}C520 ${y1} 520 ${y2} 636 ${y2}`} p={ramp(f, 95 + 7 * k, 22)}/>
      ))}
    </Scene>
  );
};

const RANK: [string, string, [string, number, 'acc' | 'n' | 'dim'][]][] = [
  ['Near · under 2 weeks', '', [['Positioning', 270, 'acc'], ['Everything else', 160, 'n'], ['Company, policy', 140, 'dim']]],
  ['Mid · one earnings season', '', [['Credit', 250, 'acc'], ['Liquidity', 250, 'acc'], ['Industry cycle', 250, 'acc'],
    ['AI demand', 250, 'acc'], ['Company results', 150, 'dim'], ['Macro policy', 130, 'dim']]],
  ['Far · 6 months+', '', [['Industry', 270, 'acc'], ['AI demand', 270, 'acc'], ['Treasury supply', 270, 'acc'],
    ['Company, policy', 140, 'dim']]],
];

const Bar: React.FC<{x: number; y: number; w: number; kind: 'acc' | 'n' | 'dim'; label: string; start: number}> =
  ({x, y, w, kind, label, start}) => {
    const s = useSpring(start);
    const fill = kind === 'acc' ? C.accBg : kind === 'n' ? C.node : 'none';
    const stroke = kind === 'acc' ? C.acc : C.line;
    return (
      <g>
        <rect x={x} y={y} width={Math.max(0.01, w * s)} height={30} fill={fill} stroke={stroke}
          strokeWidth={kind === 'acc' ? 1.5 : 1} strokeDasharray={kind === 'dim' ? '4 3' : undefined}/>
        <g opacity={s}><Txt x={x + 12} y={y + 21} s={label} size={15} bold={kind === 'acc'} color={kind === 'dim' ? C.fg2 : C.fg}/></g>
      </g>
    );
  };

const Horizons: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  return (
    <Scene dur={dur} layer="Layer 2" title="Who decides at each horizon"
      caption="The nearer you look, the more positioning matters; the further, the more the industry does." vb="0 0 960 326">
      {RANK.map(([head, , bars], c) => {
        const x = [20, 345, 670][c];
        return (
          <g key={head}>
            <g opacity={ramp(f, 10 + 25 * c, 12)}><Txt x={x} y={30} s={head} size={19} bold/></g>
            {bars.map(([label, w, kind], j) => (
              <Bar key={label + j} x={x} y={60 + 38 * j} w={w} kind={kind} label={label} start={25 + 25 * c + 6 * j}/>
            ))}
          </g>
        );
      })}
      <g opacity={ramp(f, 140, 20)}>
        <line x1={20} y1={296} x2={940} y2={296} stroke={C.fg3} strokeDasharray="4 3"/>
        <Txt x={20} y={318} s="Last at every horizon: the Fed's rate-cut path" size={15} color={C.fg2}/>
      </g>
    </Scene>
  );
};

const VETOES: [string, string, string][] = [['Funding break', 'Changes direction', C.bad], ['Rates rise too fast', 'For weeks', C.warn],
  ['Extreme positioning', 'Timing only', C.warn], ['Policy shock', 'Until expiry', C.warn]];
const NOVETO = ['Level of long rates', 'Rate-cut path', 'Bubble and crash talk', 'Minor industry delays'];
const YS = [36, 114, 192, 270];
const TARGETS = [158, 175, 192, 209];

const Vetoes: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  const center = useSpring(8);
  return (
    <Scene dur={dur} layer="Layer 3" title="What can overturn the direction"
      caption="Only a funding break changes it; the other three only pause it. The right side cannot." vb="0 0 960 346">
      <g opacity={ramp(f, 15, 12)}><Txt x={20} y={20} s="Can overturn it" size={15} bold/></g>
      <g opacity={ramp(f, 130, 12)}><Txt x={940} y={20} s="Cannot" size={15} bold anchor="end"/></g>
      <g transform={`translate(480 183) scale(${0.85 + 0.15 * center}) translate(-480 -183)`} opacity={center}>
        <rect x={370} y={146} width={220} height={74} fill={C.accBg} stroke={C.acc} strokeWidth={1.5}/>
        <Txt x={480} y={178} s="Chip direction" size={19} bold anchor="middle"/>
        <Txt x={480} y={204} s="Premise: AI demand holds" size={14} color={C.fg2} anchor="middle"/>
      </g>
      {VETOES.map(([name, how, color], i) => (
        <g key={name} opacity={ramp(f, 25 + 8 * i, 12)}>
          <rect x={20} y={YS[i]} width={290} height={58} fill={C.node} stroke={C.line}/>
          <Txt x={34} y={YS[i] + 35} s={name} size={17} bold/>
          <Txt x={296} y={YS[i] + 35} s={how} size={15} bold color={color} anchor="end"/>
        </g>
      ))}
      <Edge d="M310 65C350 65 345 158 364 158" p={ramp(f, 70, 22)} strong/>
      {[1, 2, 3].map((i) => (
        <Edge key={i} d={`M310 ${YS[i] + 29}C345 ${YS[i] + 29} 345 ${TARGETS[i]} 366 ${TARGETS[i]}`} p={ramp(f, 90 + 10 * i, 20)}/>
      ))}
      {NOVETO.map((name, i) => (
        <g key={name}>
          <g opacity={ramp(f, 140 + 8 * i, 12)}>
            <rect x={650} y={YS[i]} width={290} height={58} fill={C.node} stroke={C.line}/>
            <Txt x={664} y={YS[i] + 35} s={name} size={17} bold/>
          </g>
          <Edge d={`M650 ${YS[i] + 29}C615 ${YS[i] + 29} 620 ${TARGETS[i]} 602 ${TARGETS[i]}`} p={ramp(f, 180 + 8 * i, 15)} dashed arrow={false}/>
          <path d={`M598 ${TARGETS[i] - 6}V${TARGETS[i] + 6}`} stroke={C.fg2} strokeWidth={3} strokeLinecap="round"
            opacity={ramp(f, 195 + 8 * i, 6)}/>
        </g>
      ))}
    </Scene>
  );
};

const LANES = [['Rate volatility', 'Credit', 'Cloud funding', 'Industry'], ['Credit', 'Cloud capex', 'Industry'],
  ['Vol shock', 'Forced selling', 'Deleveraging'], ['Policy shock', 'Long rates', 'Credit']];
const XS = [20, 230, 440, 650];

const Chains: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  // lane B lights up one node at a time: credit, then capex (both near), then industry (not moved)
  const lit = [ramp(f, 80, 10), ramp(f, 105, 10), ramp(f, 130, 10)];
  const states: [string, string, string, string][] = [['Near', C.warnBg, C.warn, C.warn], ['Near · 0.85', C.warnBg, C.warn, C.warn],
    ['Not moved yet', C.okBg, C.ok, C.ok]];
  return (
    <Scene dur={dur} layer="Layer 4" title="How pressure passes between channels"
      caption="Upstream has tightened and downstream has not moved yet: the chain is transmitting." vb="0 0 960 296">
      <g opacity={ramp(f, 60, 10)}><Txt x={883} y={16} s="2026-W44" size={14} color={C.fg2} anchor="middle"/></g>
      {LANES.map((lane, i) => {
        const y = 28 + 68 * i;
        return (
          <g key={i} opacity={ramp(f, 10 + 10 * i, 12)}>
            {lane.map((name, j) => {
              const isB = i === 1;
              const l = isB ? lit[j] : 0;
              const [state, bg, stroke, tc] = isB ? states[j] : ['', C.node, C.line, C.fg];
              return (
                <g key={j}>
                  <rect x={XS[j]} y={y} width={150} height={46} fill={l > 0.5 ? bg : C.node} stroke={l > 0.5 ? stroke : C.line}
                    strokeWidth={l > 0.5 ? 1.5 : 1}/>
                  <Txt x={XS[j] + 75} y={isB && l > 0 ? y + 21 : y + 29} s={name} size={16} bold={isB && l > 0.5} anchor="middle"/>
                  {isB && <g opacity={l}><Txt x={XS[j] + 75} y={y + 39} s={state} size={13} color={tc} anchor="middle"/></g>}
                  {j > 0 && <Edge d={`M${XS[j - 1] + 150} ${y + 23}H${XS[j] - 4}`} p={ramp(f, 30 + 10 * i + 6 * j, 10)}/>}
                </g>
              );
            })}
          </g>
        );
      })}
      {[0, 2, 3].map((i) => (
        <g key={i} opacity={ramp(f, 60, 10)}>
          <rect x={826} y={38 + 68 * i} width={114} height={26} rx={13} fill={C.naBg}/>
          <circle cx={844} cy={51 + 68 * i} r={5} fill="none" stroke={C.na} strokeWidth={1.6}/>
          <Txt x={856} y={56 + 68 * i} s="Not seen" size={13} color={C.fg2}/>
        </g>
      ))}
      <g opacity={ramp(f, 150, 8)} transform={`translate(883 119) scale(${0.8 + 0.2 * ramp(f, 150, 12)}) translate(-883 -119)`}>
        <rect x={826} y={106} width={114} height={26} rx={13} fill={C.warnBg} stroke={C.warn} strokeWidth={1.2}/>
        <path d="M844 112.5L850 124H838z" fill={C.warn}/>
        <Txt x={856} y={124} s="Transmitting" size={13} bold color={C.warn}/>
      </g>
    </Scene>
  );
};

const ROLES: [string, string, string, string, number][] = [['Far sets the direction', 'Not binding', 'Direction holds', C.ok, 146],
  ['Mid sets size and hedging', 'Near', 'Hold size, no leverage', C.warn, 100],
  ['Near sets the timing', 'Binding', "Don't add yet", C.bad, 122]];

const Shape: React.FC<{i: number; cy: number}> = ({i, cy}) => {
  if (i === 0) return <circle cx={42} cy={cy} r={6} fill={C.ok}/>;
  if (i === 1) return <path d={`M42 ${cy - 6.5}L48.5 ${cy + 5}H35.5z`} fill={C.warn}/>;
  return <path d={`M42 ${cy - 6.5}L48.5 ${cy}L42 ${cy + 6.5}L35.5 ${cy}z`} fill={C.bad}/>;
};

const Action: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  const s = useSpring(140);
  return (
    <Scene dur={dur} layer="Layer 5" title="Three horizons, one action"
      caption="Far sets the direction, mid sets size and hedging, near sets the timing." vb="0 0 960 228">
      {ROLES.map(([role, state, result, color, rx], i) => {
        const y = 16 + 70 * i;
        return (
          <g key={role}>
            <g opacity={ramp(f, 10 + 15 * i, 12)}>
              <rect x={20} y={y} width={330} height={58} fill={C.node} stroke={C.line}/>
              <Txt x={36} y={y + 25} s={role} size={16} bold/>
            </g>
            <g opacity={ramp(f, 45 + 15 * i, 12)}>
              <Shape i={i} cy={y + 42}/>
              <Txt x={56} y={y + 47} s={state} size={14} bold color={color}/>
              <Txt x={rx} y={y + 47} s={result} size={14} color={C.fg2}/>
            </g>
          </g>
        );
      })}
      <Edge d="M350 45C470 45 470 98 596 98" p={ramp(f, 100, 20)}/>
      <Edge d="M350 115H596" p={ramp(f, 108, 20)}/>
      <Edge d="M350 185C470 185 470 132 596 132" p={ramp(f, 116, 20)}/>
      <g opacity={s} transform={`translate(770 115) scale(${0.9 + 0.1 * s}) translate(-770 -115)`}>
        <rect x={600} y={76} width={340} height={78} fill={C.accBg} stroke={C.acc} strokeWidth={2}/>
        <Txt x={770} y={113} s="Hold, add a small hedge" size={22} bold anchor="middle"/>
        <Txt x={770} y={140} s="Action for 2026-W44" size={14} color={C.fg2} anchor="middle"/>
      </g>
    </Scene>
  );
};

const PIPE: [string | null, string, string][] = [[null, 'Free data', 'fetched daily'], [null, '15 indicators', 'computed by code'],
  ['Level 1', '7 channel logs', 'one per channel'], ['Level 2', 'Far, mid, near', 'three horizon logs'],
  ['Level 3', 'Synthesis', 'one action'], [null, 'Web page', 'one per week']];
const PX = [10, 172, 334, 496, 658, 820];

const Pipeline: React.FC<SceneProps> = ({dur}) => {
  const f = useCurrentFrame();
  return (
    <Scene dur={dur} layer="Pipeline" title="Each level reads only the level below"
      caption="Every number needs a source; a log that fails the check goes back to be rewritten." vb="0 0 960 236">
      {PIPE.map(([level, title, sub], i) => {
        const x = PX[i];
        const cx = x + 65;
        const acc = level !== null;
        return (
          <g key={title}>
            <g opacity={ramp(f, 10 + 14 * i, 12)}>
              <rect x={x} y={60} width={130} height={74} fill={acc ? C.accBg : C.node} stroke={acc ? C.acc : C.line}
                strokeWidth={acc ? 1.5 : 1}/>
              {acc && <Txt x={cx} y={80} s={level as string} size={12} color={C.fg3} anchor="middle"/>}
              <Txt x={cx} y={acc ? 103 : 95} s={title} size={16} bold anchor="middle"/>
              <Txt x={cx} y={acc ? 124 : 118} s={sub} size={13} color={C.fg2} anchor="middle"/>
            </g>
            {i > 0 && <Edge d={`M${PX[i - 1] + 130} 97H${x - 4}`} p={ramp(f, 4 + 14 * i, 10)}/>}
          </g>
        );
      })}
      <g opacity={ramp(f, 110, 15)}>
        <rect x={334} y={178} width={454} height={40} fill={C.warnBg} stroke={C.warn} strokeWidth={1.2}/>
        <Txt x={561} y={204} s="Check: every number needs a source" size={15} bold color={C.warn} anchor="middle"/>
      </g>
      {[399, 561, 723].map((x, k) => (
        <Edge key={x} d={`M${x} 178V140`} p={ramp(f, 135 + 8 * k, 12)} dashed/>
      ))}
      <g opacity={ramp(f, 165, 12)}><Txt x={796} y={204} s="Fails → rewrite" size={14} color={C.fg2}/></g>
    </Scene>
  );
};

const SCENES: [React.FC<SceneProps>, number][] = [[Title, 150], [Channels, 270], [Horizons, 240], [Vetoes, 270],
  [Chains, 240], [Action, 210], [Pipeline, 240]];
export const TOTAL = SCENES.reduce((n, [, d]) => n + d, 0);

export const Explainer: React.FC = () => {
  let at = 0;
  return (
    <AbsoluteFill style={{background: C.bg}}>
      {SCENES.map(([Scene_, dur], i) => {
        const from = at;
        at += dur;
        return <Sequence key={i} from={from} durationInFrames={dur}><Scene_ dur={dur}/></Sequence>;
      })}
    </AbsoluteFill>
  );
};
