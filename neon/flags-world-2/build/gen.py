"""Generates index.html (single composition) from build/timeline.json."""
import json, math, os
import numpy as np

D = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(D, '..')
TL = json.load(open(os.path.join(D, 'timeline.json')))
END = TL['end']; S = TL['sent']
rng = np.random.default_rng(11)

MAG, CYAN, GOLD, ORANGE, VIOLET, GREEN = '#ff2fa8', '#3ff0ff', '#ffcf3a', '#ff8a24', '#8b5cff', '#3dff8a'

def star(cx, cy, R, ang=-90, fill='#ffde00'):
    pts = []
    for k in range(10):
        r = R if k % 2 == 0 else R * 0.382
        a = math.radians(ang + k * 36)
        pts.append(f"{cx + r*math.cos(a):.2f},{cy + r*math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'

# ---------------- flags (each returns (svg, w, h)) ----------------
def china():
    u = 20; s = f'<rect width="600" height="400" fill="#EE1C25"/>' + star(5*u, 5*u, 3*u)
    for (x, y) in [(10, 2), (12, 4), (12, 7), (10, 9)]:
        a = math.degrees(math.atan2(5 - y, 5 - x))
        s += star(x*u, y*u, u, a)
    return s, 600, 400

def greece():
    h = 400; st = h/9; s = ''
    for i in range(9):
        s += f'<rect y="{i*st:.2f}" width="600" height="{st+0.5:.2f}" fill="{"#0D5EAF" if i%2==0 else "#FFFFFF"}"/>'
    c = 5*st
    s += f'<rect width="{c:.2f}" height="{c:.2f}" fill="#0D5EAF"/>'
    s += f'<rect x="{2*st:.2f}" width="{st:.2f}" height="{c:.2f}" fill="#fff"/><rect y="{2*st:.2f}" width="{c:.2f}" height="{st:.2f}" fill="#fff"/>'
    return s, 600, 400

def philippines():
    s = '<rect width="600" height="150" fill="#0038A8"/><rect y="150" width="600" height="150" fill="#CE1126"/>'
    tx = 150*math.sqrt(3)
    s += f'<polygon points="0,0 0,300 {tx:.1f},150" fill="#fff"/>'
    cx, cy = tx/3, 150; Y = '#FCD116'
    for k in range(8):
        a = math.radians(k*45 + 22.5)
        for off in (-9, 0, 9):
            b = a + math.radians(off)
            x1, y1 = cx + 30*math.cos(b), cy + 30*math.sin(b)
            x2, y2 = cx + 58*math.cos(b), cy + 58*math.sin(b)
            s += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{Y}" stroke-width="{5 if off==0 else 3}" stroke-linecap="round"/>'
    s += f'<circle cx="{cx:.1f}" cy="{cy}" r="27" fill="{Y}"/>'
    for (x, y, a) in [(22, 26, -90), (22, 274, -90), (tx-34, 150, -90)]:
        s += star(x, y, 15, a, Y)
    return s, 600, 300

def tower(cx, base, top, w):
    # lotus-bud tower: stacked tiers narrowing to a point
    tiers = 5; s = ''; h = base - top
    for i in range(tiers):
        y0 = base - i*h/tiers*0.85; y1 = base - (i+1)*h/tiers*0.85
        ww = w*(1 - i*0.16)
        s += f'<path d="M{cx-ww/2:.1f},{y0:.1f} Q{cx-ww/2:.1f},{y1+4:.1f} {cx-ww*0.42:.1f},{y1:.1f} L{cx+ww*0.42:.1f},{y1:.1f} Q{cx+ww/2:.1f},{y1+4:.1f} {cx+ww/2:.1f},{y0:.1f} Z" fill="#fff" stroke="#111" stroke-width="1.6"/>'
    s += f'<polygon points="{cx-w*0.18:.1f},{base-h*0.85:.1f} {cx:.1f},{top:.1f} {cx+w*0.18:.1f},{base-h*0.85:.1f}" fill="#fff" stroke="#111" stroke-width="1.6"/>'
    return s

def cambodia():
    s = '<rect width="600" height="384" fill="#032EA1"/><rect y="96" width="600" height="192" fill="#E00025"/>'
    k = '#111'; W = '#fff'
    s += f'<rect x="150" y="262" width="300" height="16" fill="{W}" stroke="{k}" stroke-width="1.6"/>'
    s += f'<rect x="165" y="246" width="270" height="16" fill="{W}" stroke="{k}" stroke-width="1.6"/>'
    s += f'<rect x="178" y="200" width="244" height="46" fill="{W}" stroke="{k}" stroke-width="1.6"/>'
    for i in range(11):
        x = 188 + i*21.5
        s += f'<rect x="{x:.1f}" y="212" width="9" height="26" fill="{k}" opacity="0.85"/>'
    s += f'<polygon points="262,200 300,180 338,200" fill="{W}" stroke="{k}" stroke-width="1.6"/>'
    s += tower(212, 200, 140, 40) + tower(388, 200, 140, 40)
    s += tower(300, 200, 110, 54)
    s += f'<rect x="286" y="246" width="28" height="32" fill="{k}" opacity="0.85"/>'
    return s, 600, 384

def mongolia():
    R, B, G = '#DA2032', '#015197', '#FFD900'
    s = f'<rect width="200" height="300" fill="{R}"/><rect x="200" width="200" height="300" fill="{B}"/><rect x="400" width="200" height="300" fill="{R}"/>'
    cx = 100
    # fire: three tongues
    s += f'<path d="M{cx},28 C{cx+10},44 {cx+9},56 {cx},66 C{cx-9},56 {cx-10},44 {cx},28 Z" fill="{G}"/>'
    s += f'<path d="M{cx-14},44 C{cx-7},54 {cx-7},62 {cx-12},68 C{cx-19},62 {cx-19},54 {cx-14},44 Z" fill="{G}"/>'
    s += f'<path d="M{cx+14},44 C{cx+19},54 {cx+19},62 {cx+12},68 C{cx+7},62 {cx+7},54 {cx+14},44 Z" fill="{G}"/>'
    s += f'<circle cx="{cx}" cy="86" r="13" fill="{G}"/>'
    s += f'<path d="M{cx-20},100 A20,20 0 0 0 {cx+20},100 A20,13 0 0 1 {cx-20},100 Z" fill="{G}"/>'
    s += f'<polygon points="{cx-20},128 {cx+20},128 {cx},146" fill="{G}"/>'
    s += f'<rect x="{cx-20}" y="151" width="40" height="8" fill="{G}"/>'
    s += f'<circle cx="{cx}" cy="186" r="20" fill="{G}"/>'
    s += f'<path d="M{cx},166 A10,10 0 0 1 {cx},186 A10,10 0 0 0 {cx},206 A20,20 0 0 1 {cx},166 Z" fill="{R}"/>'
    s += f'<circle cx="{cx}" cy="176" r="3.5" fill="{G}"/><circle cx="{cx}" cy="196" r="3.5" fill="{R}"/>'
    s += f'<rect x="{cx-20}" y="213" width="40" height="8" fill="{G}"/>'
    s += f'<polygon points="{cx-20},226 {cx+20},226 {cx},244" fill="{G}"/>'
    s += f'<rect x="{cx-33}" y="128" width="8" height="116" fill="{G}"/><rect x="{cx+25}" y="128" width="8" height="116" fill="{G}"/>'
    return s, 600, 300

QS = [
    dict(flag=china, opts=['Vietnam', 'China', 'North Korea'], ans=1, level='EASY', fact='5 gold stars on red', col=CYAN),
    dict(flag=greece, opts=['Finland', 'Uruguay', 'Greece'], ans=2, level='EASY', fact='9 blue & white stripes', col=MAG),
    dict(flag=philippines, opts=['Philippines', 'Czechia', 'Cuba'], ans=0, level='MEDIUM', fact='Red on top = wartime', col=GOLD),
    dict(flag=cambodia, opts=['Thailand', 'Laos', 'Cambodia'], ans=2, level='HARD', fact='Angkor Wat is on the flag', col=GREEN),
    dict(flag=mongolia, opts=['Mongolia', 'Kazakhstan', 'Kyrgyzstan'], ans=0, level='EXPERT', fact='The gold symbol: Soyombo', col=ORANGE),
]
LVLCOL = {'EASY': GREEN, 'MEDIUM': GOLD, 'HARD': ORANGE, 'EXPERT': MAG}

def T(x, y, txt, fs, fill='#fff', glow=MAG, anchor='middle', extra='', ident=''):
    idattr = f' id="{ident}"' if ident else ''
    return (f'<text{idattr} x="{x}" y="{y}" font-size="{fs}" fill="{fill}" text-anchor="{anchor}" '
            f'class="disp" style="filter: drop-shadow(0 9px 0 #1a0638) drop-shadow(0 0 18px {glow});" {extra}>{txt}</text>')

def pill(cx, cy, txt, fs, bg, fg='#0b0420', ident='', glow=None):
    w = len(txt)*fs*0.76 + 70; h = fs*1.9
    idattr = f' id="{ident}"' if ident else ''
    return (f'<g{idattr} style="filter: drop-shadow(0 0 16px {glow or bg});"><rect x="{cx-w/2:.1f}" y="{cy-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" fill="{bg}"/>'
            f'<rect x="{cx-w/2+h*0.3:.1f}" y="{cy-h/2+5:.1f}" width="{w-h*0.6:.1f}" height="{h*0.22:.1f}" rx="{h*0.11:.1f}" fill="#fff" opacity="0.28"/>'
            f'<text x="{cx}" y="{cy+fs*0.36:.1f}" font-size="{fs}" fill="{fg}" text-anchor="middle" class="disp">{txt}</text></g>')

# ---------------- background ----------------
bg = f'''
<defs>
 <linearGradient id="gbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0420"/><stop offset="0.55" stop-color="#170a3f"/><stop offset="1" stop-color="#2a0f6e"/></linearGradient>
 <radialGradient id="gm" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{MAG}" stop-opacity="0.45"/><stop offset="1" stop-color="{MAG}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gc" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{CYAN}" stop-opacity="0.35"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gv" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.5"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
 <radialGradient id="gblob" cx="0.38" cy="0.32" r="0.75"><stop offset="0" stop-color="#ff7fd0"/><stop offset="0.6" stop-color="{MAG}"/><stop offset="1" stop-color="#9a1c8c"/></radialGradient>
 <linearGradient id="gshine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.32"/><stop offset="0.45" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.22"/></linearGradient>
 <clipPath id="cblob"><circle cx="0" cy="0" r="62"/></clipPath>
</defs>
<rect width="1080" height="1920" fill="url(#gbg)"/>
<g id="glows"><circle id="glowM" cx="900" cy="420" r="520" fill="url(#gm)"/><circle id="glowC" cx="140" cy="1500" r="560" fill="url(#gc)"/><circle cx="540" cy="900" r="700" fill="url(#gv)"/></g>
'''
far = '<g id="bokehFar">' + ''.join(
    f'<circle cx="{rng.uniform(0,1080):.0f}" cy="{rng.uniform(0,2100):.0f}" r="{rng.uniform(3,7):.1f}" fill="{rng.choice([CYAN,MAG,GOLD,VIOLET])}" opacity="{rng.uniform(0.25,0.5):.2f}"/>'
    for _ in range(28)) + '</g>'
near = '<g id="bokehNear">' + ''.join(
    f'<circle cx="{rng.uniform(0,1080):.0f}" cy="{rng.uniform(0,2200):.0f}" r="{rng.uniform(10,22):.1f}" fill="{rng.choice([CYAN,MAG,VIOLET])}" opacity="{rng.uniform(0.10,0.2):.2f}" style="filter: blur(4px)"/>'
    for _ in range(10)) + '</g>'

# ---------------- blob mascot (original) ----------------
blob = f'''
<g transform="translate(120,300)"><g id="blob">
 <g id="blobBody">
  <ellipse cx="0" cy="74" rx="46" ry="9" fill="#000" opacity="0.35"/>
  <g style="filter: drop-shadow(0 0 22px {MAG});">
   <circle cx="0" cy="0" r="62" fill="url(#gblob)"/>
   <g clip-path="url(#cblob)"><circle cx="18" cy="26" r="66" fill="#6d1070" opacity="0.45"/><rect x="-40" y="-52" width="58" height="16" rx="8" fill="#fff" opacity="0.35" transform="rotate(-20)"/></g>
  </g>
  <g id="eyes">
   <ellipse cx="-20" cy="-8" rx="17" ry="20" fill="#fff"/><ellipse cx="20" cy="-8" rx="17" ry="20" fill="#fff"/>
   <g id="pupils"><circle cx="-17" cy="-5" r="8" fill="#1a0638"/><circle cx="23" cy="-5" r="8" fill="#1a0638"/>
    <circle cx="-14" cy="-9" r="2.6" fill="#fff"/><circle cx="26" cy="-9" r="2.6" fill="#fff"/></g>
   <g id="lids" opacity="0"><rect x="-38" y="-30" width="36" height="42" rx="16" fill="{MAG}"/><rect x="2" y="-30" width="36" height="42" rx="16" fill="{MAG}"/></g>
  </g>
  <path id="mouthSmile" d="M-14,22 Q0,34 14,22" stroke="#1a0638" stroke-width="5" fill="none" stroke-linecap="round"/>
  <g id="mouthO" opacity="0"><ellipse cx="0" cy="28" rx="7" ry="8" fill="#1a0638"/></g>
  <g id="mouthBig" opacity="0"><path d="M-20,18 Q0,48 20,18 Z" fill="#1a0638"/><path d="M-10,33 Q0,40 10,33" stroke="{MAG}" stroke-width="5" fill="none"/></g>
  </g>
</g></g>'''

# ---------------- intro ----------------
introCircles = ''
cols = ['#EE1C25', '#0D5EAF', '#FCD116', '#E00025', '#015197']
for i, c in enumerate(cols):
    x = 520 + (i-2)*140
    introCircles += (f'<g id="ic{i}" opacity="0" style="filter: drop-shadow(0 0 18px {c});"><circle cx="{x}" cy="1120" r="52" fill="{c}"/>'
                     f'<circle cx="{x-16}" cy="1102" r="15" fill="#fff" opacity="0.3"/>'
                     f'<text x="{x}" y="1143" font-size="64" fill="#fff" text-anchor="middle" class="disp">?</text></g>')
intro = f'''
<g id="intro">
 <g id="i1" opacity="0">{T(510, 640, "CAN YOU NAME", 70, '#fff', CYAN)}</g>
 <g id="i2" opacity="0">{T(520, 830, "ALL 5", 200, GOLD, ORANGE)}</g>
 <g id="i3" opacity="0">{T(520, 990, "FLAGS?", 112, CYAN, VIOLET)}</g>
 {introCircles}
 <g id="i4" opacity="0">{pill(520, 1250, "EASY TO EXPERT", 46, MAG, '#fff')}</g>
</g>'''

# ---------------- HUD ----------------
C = 2*math.pi*54
hud = f'''
<g id="hud" opacity="0">
 {T(560, 356, "GUESS THE FLAG", 58, '#fff', MAG)}
</g>'''
RING = f'''
<g id="ring" opacity="0" transform="translate(890,490)">
 <circle r="66" fill="#0b0420" style="filter: drop-shadow(0 0 18px {GOLD});"/>
 <circle r="54" fill="none" stroke="#3a2470" stroke-width="12"/>
 <circle id="ringArc" r="54" fill="none" stroke="{GOLD}" stroke-width="12" stroke-linecap="round" transform="rotate(-90)" stroke-dasharray="{C:.2f}" stroke-dashoffset="0"/>
 <text id="n3" y="24" font-size="66" fill="#fff" text-anchor="middle" class="disp">3</text>
 <text id="n2" y="24" font-size="66" fill="#fff" text-anchor="middle" class="disp" opacity="0">2</text>
 <text id="n1" y="24" font-size="66" fill="{MAG}" text-anchor="middle" class="disp" opacity="0">1</text>
</g>'''

qs = ''
FLAGBASE = []
for i, q in enumerate(QS):
    fs, w, h = q['flag']()
    FLAGBASE.append(f'translate({540-w*0.82/2:.1f},{672-h*0.82/2:.1f}) scale(0.82) rotate(%s,{w/2},{h/2})')
    col = q['col']
    lv = q['level']
    opts = ''
    for j, o in enumerate(q['opts']):
        y = 972 + j*112
        L = 'ABC'[j]
        opts += f'''<g id="q{i}o{j}" opacity="0">
  <g id="q{i}o{j}base"><rect x="150" y="{y-48}" width="780" height="96" rx="48" fill="#ffffff"/>
   <rect x="190" y="{y-42}" width="700" height="18" rx="9" fill="#fff" opacity="0.6"/>
   <circle cx="208" cy="{y}" r="36" fill="#2a0f6e"/><text x="208" y="{y+15}" font-size="40" fill="#fff" text-anchor="middle" class="disp">{L}</text>
   <text x="560" y="{y+17}" font-size="50" fill="#1a0638" text-anchor="middle" class="disp">{o}</text></g>
  <g id="q{i}o{j}win" opacity="0" style="filter: drop-shadow(0 0 26px {GREEN});"><rect x="150" y="{y-48}" width="780" height="96" rx="48" fill="{GREEN}"/>
   <rect x="190" y="{y-42}" width="700" height="18" rx="9" fill="#fff" opacity="0.35"/>
   <circle cx="208" cy="{y}" r="36" fill="#fff"/><text x="208" y="{y+15}" font-size="40" fill="#0f7a3c" text-anchor="middle" class="disp">{L}</text>
   <text x="560" y="{y+17}" font-size="50" fill="#0b0420" text-anchor="middle" class="disp">{o}</text>
   <path d="M850,{y} l18,20 l34,-40" stroke="#0b0420" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
</g>'''
    fw = len(q['fact'])*36*0.76 + 70
    qs += f'''
<g id="q{i}" opacity="0">
 <g id="q{i}cam">
  {pill(560, 425, f"FLAG {i+1}/5 · {lv}", 34, LVLCOL[lv], '#0b0420')}
  <g id="q{i}card" style="filter: drop-shadow(0 0 30px {col});">
   <rect x="120" y="470" width="840" height="410" rx="44" fill="#170a3f"/>
   <rect x="120" y="470" width="840" height="410" rx="44" fill="none" stroke="{col}" stroke-width="5" opacity="0.9"/>
  </g>
  <g id="q{i}flag" transform="translate({540-w*0.82/2:.1f},{672-h*0.82/2:.1f}) scale(0.82)">
   <g style="filter: drop-shadow(0 14px 18px rgba(0,0,0,0.55));">{fs}</g>
   <rect width="{w}" height="{h}" fill="url(#gshine)"/>
  </g>
  {opts}
  <g id="q{i}fact" opacity="0">
   <g style="filter: drop-shadow(0 0 18px {GOLD});"><rect x="{540-fw/2:.1f}" y="842" width="{fw:.1f}" height="76" rx="38" fill="#0b0420" stroke="{GOLD}" stroke-width="4"/></g>
   <text x="540" y="893" font-size="36" fill="{GOLD}" text-anchor="middle" class="disp">{q['fact']}</text>
  </g>
 </g>
</g>'''

# ---------------- outro ----------------
bub = ''
for k in range(6):
    x = 520 + (k-2.5)*124
    c = [VIOLET, VIOLET, CYAN, CYAN, GOLD, GREEN][k]
    bub += (f'<g id="sb{k}" opacity="0" style="filter: drop-shadow(0 0 14px {c});"><circle cx="{x}" cy="920" r="46" fill="{c}"/>'
            f'<text x="{x}" y="942" font-size="60" fill="#0b0420" text-anchor="middle" class="disp">{k}</text></g>')
outro = f'''
<g id="outro" opacity="0">
 <g id="o1" opacity="0">{T(510, 640, "HOW MANY", 92, '#fff', CYAN)}</g>
 <g id="o2" opacity="0">{T(520, 770, "DID YOU GET?", 92, GOLD, ORANGE)}</g>
 {bub}
 <g id="o3" opacity="0">{pill(520, 1060, "COMMENT YOUR SCORE", 42, CYAN)}</g>
 <g id="o4" opacity="0">{T(520, 1190, "FOLLOW FOR A DAILY QUIZ!", 50, '#fff', MAG)}</g>
</g>'''

# ---------------- captions (intro/outro only; questions show text on screen) ----------------

svg = f'<svg id="stage" width="1080" height="1920" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">{bg}{far}{near}{intro}{hud}{qs}{RING}{outro}{blob}</svg>'

# ---------------- timeline JS ----------------
js = []
A = js.append

def OP(sel, a, b, dur, at):
    A(f'tl.fromTo("{sel}", {{opacity: {a}}}, {{opacity: {b}, duration: {dur}, immediateRender: false}}, {at:.3f});')
def SC(sel, cx, cy, s0, s1, dur, ease, at, base='', rep=0):
    yo = f', repeat: {rep}, yoyo: true' if rep else ''
    A(f'PX("{sel}", "{base}", {cx}, {cy}, "s", {s0}, {s1}, {{duration: {dur}, ease: "{ease}"{yo}}}, {at:.3f});')
def ROT(sel, base, a0, a1, dur, ease, at):
    A(f'PX("{sel}", "{base}", 0, 0, "r", {a0}, {a1}, {{duration: {dur}, ease: "{ease}"}}, {at:.3f});')
qsent = [s for s in S if s['kind'] == 'q']; asent = [s for s in S if s['kind'] == 'a']
A(f'tl.to("#bokehFar", {{y: -160, duration: {END:.2f}, ease: "none"}}, 0);')
A(f'tl.to("#bokehNear", {{y: -320, duration: {END:.2f}, ease: "none"}}, 0);')
A(f'tl.to("#glowM", {{attr: {{cx: 760, cy: 560}}, duration: {END/2:.2f}, ease: "sine.inOut", yoyo: true, repeat: 1}}, 0);')
nb = int(END/0.5)
A(f'tl.to("#blobBody", {{y: -10, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: {nb-1}}}, 0);')
# blinks
for bt in [1.6, 6.3, 13.4, 20.2, 27.6, 35.1, 42.5]:
    A(f'tl.set("#lids", {{opacity: 1}}, {bt}); tl.set("#lids", {{opacity: 0}}, {bt+0.12:.2f});')
# intro
s0, s1 = S[0], S[1]
for k, idn in enumerate(['i1', 'i2', 'i3']):
    t0 = s0['start'] - 0.1 + k*0.42
    OP(f"#{idn}", 0, 1, 0.2, t0); SC(f"#{idn}", 520, [640,800,960][k], 1.5, 1, 0.32, "back.out(2)", t0)
for k in range(5):
    OP(f"#ic{k}", 0, 1, 0.15, s1["start"]+k*0.12); SC(f"#ic{k}", 520+(k-2)*140, 1120, 0, 1, 0.28, "back.out(3)", s1["start"]+k*0.12)
A(f'tl.fromTo("#i4", {{opacity: 0, y: 40}}, {{opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)"}}, {s1["start"]+0.55:.2f});')
SC("#i2", 520, 800, 1, 1.08, 0.6, "sine.inOut", s0["start"]+1.2, rep=3)
A(f'tl.set("#mouthSmile", {{opacity: 0}}, {s0["start"]:.2f}); tl.set("#mouthO", {{opacity: 1}}, {s0["start"]:.2f}); tl.set("#mouthO", {{opacity: 0}}, {s1["end"]:.2f}); tl.set("#mouthSmile", {{opacity: 1}}, {s1["end"]:.2f});')
first = qsent[0]['start'] - 0.08
OP("#intro", 1, 0, 0.2, first-0.2); SC("#intro", 520, 900, 1, 0.9, 0.2, "power2.in", first-0.2)
A(f'tl.fromTo("#hud", {{opacity: 0, y: -40}}, {{opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)"}}, {first:.2f});')
for i, (qs_, as_) in enumerate(zip(qsent, asent)):
    t0 = qs_['start'] - 0.08
    OP(f"#q{i}", 0, 1, 0.15, t0); SC(f"#q{i}", 540, 800, 1.14, 1, 0.3, "power3.out", t0)
    SC(f"#q{i}cam", 540, 800, 1, 1.035, 6.5, "none", t0)
    ROT(f"#q{i}flag", FLAGBASE[i], -4, 0, 0.6, "back.out(2)", t0)
    if i > 0:
        A(f'tl.set("#q{i-1}", {{opacity: 0}}, {t0+0.25:.2f});')
    for j in range(3):
        A(f'tl.fromTo("#q{i}o{j}", {{opacity: 0, x: {-80 if j%2==0 else 80}}}, {{opacity: 1, x: 0, duration: 0.26, ease: "back.out(2)"}}, {qs_["start"]+0.25+j*0.12:.2f});')
    # countdown
    c0 = qs_['end'] + 0.15
    A(f'tl.set("#n3", {{opacity: 1}}, {c0:.2f}); tl.set("#n2", {{opacity: 0}}, {c0:.2f}); tl.set("#n1", {{opacity: 0}}, {c0:.2f});')
    A(f'tl.set("#ringArc", {{attr: {{"stroke-dashoffset": 0}}}}, {c0:.2f});')
    OP("#ring", 0, 1, 0.1, c0-0.1); SC("#ring", 0, 0, 0, 1, 0.22, "back.out(3)", c0-0.1, base="translate(890,490)")
    A(f'tl.to("#ringArc", {{attr: {{"stroke-dashoffset": {C:.2f}}}, duration: 3, ease: "none", immediateRender: false}}, {c0:.2f});')
    A(f'tl.set("#n3", {{opacity: 0}}, {c0+1:.2f}); tl.set("#n2", {{opacity: 1}}, {c0+1:.2f}); tl.set("#n2", {{opacity: 0}}, {c0+2:.2f}); tl.set("#n1", {{opacity: 1}}, {c0+2:.2f});')
    for k in (1, 2):
        SC("#ring", 0, 0, 1.18, 1, 0.25, "power2.out", c0+k, base="translate(890,490)")
    # blob thinking: pupils look down
    A(f'tl.to("#pupils", {{x: 5, y: 6, duration: 0.2, immediateRender: false}}, {c0:.2f});')
    A(f'tl.set("#mouthSmile", {{opacity: 0}}, {c0:.2f}); tl.set("#mouthO", {{opacity: 1}}, {c0:.2f});')
    A(f'tl.to("#blob", {{x: 3, duration: 0.06, yoyo: true, repeat: 7, immediateRender: false}}, {c0+2:.2f});')
    # reveal
    r = as_['start'] - 0.1
    OP("#ring", 1, 0, 0.15, r); SC("#ring", 0, 0, 1, 0.5, 0.15, "power2.in", r, base="translate(890,490)")
    ans = QS[i]['ans']
    for j in range(3):
        if j == ans:
            A(f'tl.to("#q{i}o{j}win", {{opacity: 1, duration: 0.12}}, {r:.2f}); tl.set("#q{i}o{j}base", {{opacity: 0}}, {r+0.12:.2f});')
            SC(f"#q{i}o{j}", 540, 972+j*112, 1.12, 1, 0.35, "back.out(3)", r)
        else:
            A(f'tl.to("#q{i}o{j}", {{opacity: 0.3, duration: 0.2, immediateRender: false}}, {r:.2f});')
    A(f'tl.fromTo("#q{i}fact", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)"}}, {r+0.25:.2f});')
    A(f'tl.to("#pupils", {{x: 0, y: 0, duration: 0.15, immediateRender: false}}, {r:.2f});')
    A(f'tl.set("#mouthO", {{opacity: 0}}, {r:.2f}); tl.set("#mouthBig", {{opacity: 1}}, {r:.2f}); tl.set("#mouthBig", {{opacity: 0}}, {r+1.4:.2f}); tl.set("#mouthSmile", {{opacity: 1}}, {r+1.4:.2f});')
    A(f'tl.to("#blob", {{y: -36, duration: 0.18, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false}}, {r:.2f});')
# outro
o, o2 = S[-2], S[-1]
t0 = o['start'] - 0.1
A(f'tl.set("#q4", {{opacity: 0}}, {t0+0.2:.2f}); tl.to("#hud", {{opacity: 0, duration: 0.2, immediateRender: false}}, {t0:.2f});')
A(f'tl.set("#outro", {{opacity: 1}}, {t0:.2f});')
OP("#o1", 0, 1, 0.15, t0); SC("#o1", 520, 610, 1.4, 1, 0.3, "back.out(2)", t0)
OP("#o2", 0, 1, 0.15, t0+0.4); SC("#o2", 520, 740, 1.4, 1, 0.3, "back.out(2)", t0+0.4)
for k in range(6):
    OP(f"#sb{k}", 0, 1, 0.12, t0+0.8+k*0.1); SC(f"#sb{k}", 520+(k-2.5)*124, 920, 0, 1, 0.25, "back.out(3)", t0+0.8+k*0.1)
A(f'tl.fromTo("#o3", {{opacity: 0, y: 30}}, {{opacity: 1, y: 0, duration: 0.3, ease: "back.out(2)"}}, {o["end"]-0.6:.2f});')
OP("#o4", 0, 1, 0.15, o2["start"]-0.05); SC("#o4", 520, 1172, 0.6, 1, 0.35, "back.out(2.5)", o2["start"]-0.05)
SC("#o4", 520, 1172, 1, 1.06, 0.4, "sine.inOut", o2["start"]+0.4, rep=3)
A(f'tl.set("#mouthSmile", {{opacity: 0}}, {t0:.2f}); tl.set("#mouthBig", {{opacity: 1}}, {t0:.2f});')

html = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<style>
 * {{ margin: 0; padding: 0; box-sizing: border-box; }}
 html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0b0420; }}
 #root {{ width: 1080px; height: 1920px; position: relative; }}
 #stage {{ position: absolute; inset: 0; }}
 .disp {{ font-family: 'Montserrat', sans-serif; font-weight: 900; font-style: italic; letter-spacing: -0.01em; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{END:.2f}" data-width="1080" data-height="1920">
{svg}
<audio id="soundtrack" src="assets/audio/soundtrack.wav" data-start="0" data-duration="{END:.2f}" data-track-index="1"></audio>
</div>
<script>
(function () {{
 const tl = gsap.timeline({{ paused: true }});
 function PX(sel, base, cx, cy, kind, v0, v1, vars, at) {{
   const el = document.querySelector(sel);
   const f = (v) => kind === "r" ? base.replace("%s", v) : (base + " translate(" + cx + "," + cy + ") scale(" + v + ") translate(" + (-cx) + "," + (-cy) + ")");
   tl.fromTo(el, {{attr: {{transform: f(v0)}}}}, Object.assign({{attr: {{transform: f(v1)}}, immediateRender: false}}, vars), at);
 }}
 {chr(10).join(js)}
 window.__timelines = window.__timelines || {{}};
 window.__timelines["main"] = tl;
 tl.seek(0);
}})();
</script>
</body>
</html>'''
open(os.path.join(P, 'index.html'), 'w').write(html)
print('ok', END)
