#!/usr/bin/env python3
"""Quiz Short renderer v2: 1080x1920, 30 fps, Kokoro narration, 3 layouts, any number of questions.
usage: python3 quiz.py quizzes/<name>.json out.mp4          (render)
       python3 quiz.py quizzes/<name>.json /tmp/x 0.8,7.5   (still frames, no audio)

Quiz JSON:
  title, hook1, hook2, hook_emoji, bg [c1,c2], style {pattern, timer, bpm, root, voice}, ask (default spoken question),
  questions: [{ layout: mcq|versus|tiles, emoji?, text?, say?, options[], opt_emoji[]?, answer, fact, say_answer? }]
  mcq    = 3 stacked options (emoji/text clue in the card)
  versus = 2 big side-by-side choices with an emoji each (true/false, which is bigger/older/faster)
  tiles  = 4 emoji tiles in a 2x2 grid (odd one out, which one is…); options are short labels, opt_emoji the pictures
"""
import json, sys, math, subprocess, wave, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
LW, LH = 1920, 1080  # landscape (long-video) canvas
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
FE = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
EMO = ImageFont.truetype(FE, 109, layout_engine=ImageFont.Layout.RAQM)
_FC = {}
def F(s):
    s = max(8, int(s))
    if s not in _FC: _FC[s] = ImageFont.truetype(FB, s)
    return _FC[s]
POP, THINK = 0.35, 3.0
LAND = False  # set by main() for landscape long videos
INK = (20, 16, 40)

def ease(u): u = max(0, min(1, u)); return 1 - (1 - u) ** 3
def back(u):
    u = max(0, min(1, u)); c = 1.70158
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2

_EC = {}
def emoji_img(s, h):
    h = max(2, int(h))
    key = (s, h)
    if key in _EC: return _EC[key]
    base = _EC.get((s, 0))
    if base is None:
        tmp = Image.new('RGBA', (140 * max(1, len(s)) + 40, 150), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((10, 10), s, font=EMO, embedded_color=True)
        base = tmp.crop(tmp.getbbox()); _EC[(s, 0)] = base
    im = base.resize((max(1, int(base.width * h / base.height)), h), Image.LANCZOS)
    if len(_EC) < 400: _EC[key] = im
    return im

def text_mixed(d, im, xy, s, size, fill, stroke=0, maxw=940):
    parts = s.split('|')
    while size > 20 and d.textlength(parts[0], font=F(size)) + (size * 1.2 if len(parts) > 1 else 0) > maxw:
        size -= 4
    f = F(size)
    if len(parts) == 1:
        d.text(xy, s, font=f, fill=fill, anchor='mm', stroke_width=stroke, stroke_fill=INK); return
    t, e = parts
    tw = d.textlength(t, font=f); em = emoji_img(e, size * 1.05)
    x0 = xy[0] - (tw + 16 + em.width) / 2
    d.text((x0, xy[1]), t, font=f, fill=fill, anchor='lm', stroke_width=stroke, stroke_fill=INK)
    im.alpha_composite(em, (int(x0 + tw + 16), int(xy[1] - em.height / 2)))

def rr(d, box, r, fill, outline=None, w=0):
    x0, y0, x1, y1 = box
    if x1 - x0 < 2 or y1 - y0 < 2: return
    d.rounded_rectangle((x0, y0, x1, y1), min(r, (x1 - x0) / 2, (y1 - y0) / 2), fill=fill, outline=outline, width=w)

def clean(s): return re.sub(r'\|.*$', '', s).replace('\n', ' ').strip()


# ---------------- stick man reactor ----------------
def stick(d, cx, fy, h, mood, t, face_dir=1):
    """cx = centre x, fy = foot y, h = total height. mood: wave | think | nervous | happy | point"""
    bob = 0
    if mood == 'happy': bob = -abs(math.sin(t * 9)) * h * 0.10
    fy = fy + bob
    hr = h * 0.15; neck = fy - h * 0.62; hip = fy - h * 0.32
    hx, hy = cx, neck - hr
    def L(pts, w):
        d.line(pts, fill=(255, 255, 255), width=int(w + h * 0.035), joint='curve')
        d.line(pts, fill=INK, width=int(w), joint='curve')
    lw = max(4, h * 0.045)
    # legs
    sp = h * 0.13
    if mood == 'happy': L([(cx - sp, fy), (cx, hip), (cx + sp, fy)], lw)
    else: L([(cx - sp * 0.8, fy), (cx, hip), (cx + sp * 0.8, fy)], lw)
    L([(cx, hip), (cx, neck)], lw)
    sh = neck + h * 0.05; a = h * 0.22
    if mood == 'wave':
        ang = math.sin(t * 10) * 0.35
        L([(cx, sh), (cx - a * 0.9, sh + a * 0.8)], lw)
        L([(cx, sh), (cx + a * 0.7, sh - a * 0.4), (cx + a * 0.7 + math.sin(ang) * a * 0.6, sh - a * 0.4 - math.cos(ang) * a * 0.7)], lw)
    elif mood == 'think':
        L([(cx, sh), (cx - a * 0.8, sh + a * 0.85)], lw)
        L([(cx, sh), (cx + a * 0.75, sh + a * 0.35), (cx + hr * 0.5, hy + hr * 0.95)], lw)
    elif mood == 'nervous':
        L([(cx, sh), (cx - a * 0.6, sh - a * 0.5), (cx - hr * 0.9, hy + hr * 0.3)], lw)
        L([(cx, sh), (cx + a * 0.6, sh - a * 0.5), (cx + hr * 0.9, hy + hr * 0.3)], lw)
    elif mood == 'happy':
        L([(cx, sh), (cx - a * 1.05, sh - a * 0.75)], lw); L([(cx, sh), (cx + a * 1.05, sh - a * 0.75)], lw)
    else:  # point
        L([(cx, sh), (cx - a * 0.8, sh + a * 0.85)], lw)
        L([(cx, sh), (cx + face_dir * a * 1.1, sh - a * 0.55)], lw)
    # head
    d.ellipse((hx - hr - h * 0.017, hy - hr - h * 0.017, hx + hr + h * 0.017, hy + hr + h * 0.017), fill=(255, 255, 255))
    d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(255, 236, 200), outline=INK, width=int(lw * 0.8))
    e = hr * 0.38; ey = hy - hr * 0.12; er = max(2, hr * 0.12)
    if mood == 'think':
        for sx in (-1, 1): d.ellipse((hx + sx * e - er, ey - hr * 0.18 - er, hx + sx * e + er, ey - hr * 0.18 + er), fill=INK)
        d.line([(hx - hr * 0.3, hy + hr * 0.45), (hx + hr * 0.25, hy + hr * 0.38)], fill=INK, width=int(lw * 0.6))
        d.line([(hx - e - er * 1.6, ey - hr * 0.55), (hx - e + er * 1.6, ey - hr * 0.62)], fill=INK, width=int(lw * 0.5))
    elif mood == 'nervous':
        for sx in (-1, 1): d.ellipse((hx + sx * e - er * 1.5, ey - er * 1.5, hx + sx * e + er * 1.5, ey + er * 1.5), fill=(255, 255, 255), outline=INK, width=int(lw * 0.4))
        for sx in (-1, 1): d.ellipse((hx + sx * e - er * 0.6, ey - er * 0.6, hx + sx * e + er * 0.6, ey + er * 0.6), fill=INK)
        d.arc((hx - hr * 0.35, hy + hr * 0.3, hx + hr * 0.35, hy + hr * 0.75), 200, 340, fill=INK, width=int(lw * 0.6))
        d.ellipse((hx + hr * 0.95, hy - hr * 0.5, hx + hr * 1.25, hy - hr * 0.05), fill=(120, 200, 255))
    elif mood == 'happy':
        for sx in (-1, 1): d.arc((hx + sx * e - er * 1.6, ey - er * 1.4, hx + sx * e + er * 1.6, ey + er * 1.8), 200, 340, fill=INK, width=int(lw * 0.55))
        d.chord((hx - hr * 0.5, hy + hr * 0.05, hx + hr * 0.5, hy + hr * 0.75), 0, 180, fill=INK)
    else:
        for sx in (-1, 1): d.ellipse((hx + sx * e - er, ey - er, hx + sx * e + er, ey + er), fill=INK)
        d.arc((hx - hr * 0.45, hy + hr * 0.05, hx + hr * 0.45, hy + hr * 0.6), 20, 160, fill=INK, width=int(lw * 0.6))
    return hx, hy, hr

def bubble(d, x, y, txt, size):
    tw = d.textlength(txt, font=F(size))
    rr(d, (x - tw / 2 - 22, y - size * 0.8, x + tw / 2 + 22, y + size * 0.8), 30, (255, 255, 255), outline=INK, w=4)
    d.text((x, y), txt, font=F(size), fill=INK, anchor='mm')

# ---------------- timeline ----------------
def plan(q, voice_on=True):
    st = q.get('style', {}); vo = st.get('voice', 'af_heart')
    segs = []  # (kind, idx, start, dur, speech_text)
    def tl(text):
        if not voice_on: return None, max(0.8, len(text) * 0.055)
        from tts import say
        a = say(text, voice=vo); return a, len(a) / SR
    audio = []
    t = 0.0
    a, d = tl(f"{q['hook1']} {q['hook2']}".replace('#', 'number '))
    audio.append((0.1, a)); HOOK = max(1.4, d + 0.25)
    segs.append(('hook', -1, 0.0, HOOK)); t = HOOK
    for k, x in enumerate(q['questions']):
        ask = x.get('say') or (clean(x['text']) if x.get('text') else q.get('ask', 'What is it?'))
        a, d = tl(ask); audio.append((t + 0.15, a))
        think0 = max(POP, 0.15 + d)
        ans = x['options'][x['answer']]
        sa = x.get('say_answer') or f"{ans}!"
        if q.get('speak_fact') and x.get('fact'): sa = f"{sa} {clean(x['fact'])}"
        a2, d2 = tl(sa)
        rev = max(1.4, d2 + 0.25)
        audio.append((t + think0 + THINK + 0.08, a2))
        segs.append(('q', k, t, think0 + THINK + rev, think0)); t += think0 + THINK + rev
    a, d = tl(q.get('outro_say', 'How many did you get? Comment your score, and follow for a new quiz every day!'))
    audio.append((t + 0.15, a)); END = max(2.0, d + 0.6)
    segs.append(('end', -1, t, END)); t += END
    return segs, audio, t

def build_bg(q, W=W, H=H):
    c1, c2 = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in q['bg']]
    yy = np.linspace(0, 1, H)[:, None, None]
    grad = (np.array(c1)[None, None, :] * (1 - yy) + np.array(c2)[None, None, :] * yy).repeat(W, 1).astype(np.uint8)
    BG = Image.fromarray(grad, 'RGB').convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
    pat = q.get('style', {}).get('pattern', 'dots')
    if pat == 'dots':
        for i in range(70):
            x, y = (i * 397) % W, (i * 613) % H
            dd.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 255, 255, 40))
    elif pat == 'stripes':
        for i in range(-H, W, 90): dd.line([(i, H), (i + H, 0)], fill=(255, 255, 255, 22), width=28)
    else:
        for y0 in range(80, H, 160):
            dd.line([(x, y0 + 26 * math.sin(x / 90 + y0)) for x in range(0, W + 20, 20)], fill=(255, 255, 255, 30), width=6)
    return Image.alpha_composite(BG, ov)

def fit_prompt(e, maxw=800, h=300):
    im = emoji_img(e, h)
    return im if im.width <= maxw else im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)

LEVELS = [('EASY', (90, 220, 120)), ('MEDIUM', (255, 190, 60)), ('HARD', (255, 110, 70)), ('EXPERT', (230, 60, 90))]
def level(k, n):
    i = 0 if k < max(1, round(n * 0.4)) else 1 if k < round(n * 0.6) else 2 if k < round(n * 0.8) else 3
    return LEVELS[i]

def frame(q, BG, segs, t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    qs = q['questions']; n = len(qs)
    seg = next(s for s in segs if s[2] <= t < s[2] + s[3]) if t < segs[-1][2] + segs[-1][3] else segs[-1]
    kind, k, t0 = seg[0], seg[1], seg[2]
    lt = t - t0
    if kind == 'hook':
        s = back(lt / 0.45)
        text_mixed(d, im, (540, 640), q['hook1'], 118 * s, (255, 255, 255), stroke=10)
        text_mixed(d, im, (540, 800), q['hook2'], 96 * s, (255, 222, 74), stroke=10)
        e = emoji_img(q['hook_emoji'], 220 * s)
        im.alpha_composite(e, (700 - e.width // 2, 1080))
        if s > 0.2: stick(d, 380, 1520, 470 * min(1, s), 'wave', t)
        return im
    if kind == 'end':
        s = back(lt / 0.4)
        text_mixed(d, im, (540, 640), 'How many did', 100 * s, (255, 255, 255), stroke=9)
        text_mixed(d, im, (540, 770), 'you get?', 110 * s, (255, 222, 74), stroke=9)
        text_mixed(d, im, (540, 900), 'Comment your score|👇', 60 * s, (255, 255, 255), stroke=6)
        fa = ease((lt - 0.6) / 0.3)
        if fa > 0:
            rr(d, (540 - 330 * fa, 1330, 540 + 330 * fa, 1430), 50, (255, 60, 70))
            if fa > 0.9: d.text((540, 1380), q.get('outro_text', 'Follow for a daily quiz!'), font=F(48 if len(q.get('outro_text', '')) < 26 else 40), fill=(255, 255, 255), anchor='mm')
            stick(d, 200, 1720, 300, 'point', t)
        chips = min(n, 10)
        for i in range(chips):
            x = 540 + (i - (chips - 1) / 2) * (900 / max(chips, 5))
            a = ease((lt - 0.3 - i * 0.06) / 0.25)
            if a > 0:
                rr(d, (x - 40, 1080 - 40 * a, x + 40, 1080 + 40 * a), 22, (255, 255, 255, 230))
                lab = str(i + 1) if n <= 10 else str((i + 1) * n // chips)
                d.text((x, 1080), lab, font=F(44), fill=(40, 30, 90), anchor='mm')
        return im
    x = qs[k]; think0 = seg[4]
    lay = x.get('layout', 'mcq')
    # header
    d.text((540, 230), q['title'], font=F(52), fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=INK)
    if n <= 12:
        for i in range(n):
            cx = 540 + (i - (n - 1) / 2) * (70 if n <= 6 else 52)
            col = (255, 222, 74) if i < k else (255, 255, 255) if i == k else (255, 255, 255, 90)
            r = 16 if i == k else 11
            d.ellipse((cx - r, 300 - r, cx + r, 300 + r), fill=col)
    else:
        rr(d, (240, 290, 840, 310), 10, (255, 255, 255, 90)); rr(d, (240, 290, 240 + 600 * (k + 1) / n, 310), 10, (255, 222, 74))
    lv, lc = level(k, n)
    rr(d, (390, 350, 690, 420), 35, lc)
    d.text((540, 385), f'Q{k+1} · {lv}', font=F(38), fill=(255, 255, 255), anchor='mm')
    # prompt card
    s = back(lt / POP)
    cw, ch = int(900 * s), int(560 * s)
    if lay == 'tiles': ch = int(330 * s)
    cy = 760 if lay != 'tiles' else 640
    if cw > 10:
        rr(d, (540 - cw // 2, cy - ch // 2, 540 + cw // 2, cy + ch // 2), 48, (255, 255, 255, 245))
        if x.get('emoji') and s > 0.3:
            p = fit_prompt(x['emoji'], h=300 if not x.get('text') else 190)
            p = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))))
            py = cy - p.height // 2 if not x.get('text') else cy - 150 - p.height // 2 + 40
            im.alpha_composite(p, (540 - p.width // 2, py))
        if x.get('text') and s > 0.6:
            lines = x['text'].split('\n'); fs = 62 if not x.get('emoji') else 54
            if lay == 'tiles': fs = 56
            y0 = cy - (len(lines) - 1) * fs * 0.6 + (90 if x.get('emoji') else 0)
            for j, ln in enumerate(lines):
                while fs > 30 and d.textlength(ln, font=F(fs)) > 820: fs -= 4
                d.text((540, y0 + j * fs * 1.2), ln, font=F(fs), fill=(30, 24, 60), anchor='mm')
    reveal = lt >= think0 + THINK
    ru = ease((lt - think0 - THINK) / 0.2)
    pulse = 0.06 * math.sin(min(1, (lt - think0 - THINK) / 0.3) * math.pi) if reveal else 0
    def tick(cx, cy, sz=1.0):
        d.line([(cx - 22 * sz, cy + 2 * sz), (cx - 6 * sz, cy + 20 * sz), (cx + 24 * sz, cy - 20 * sz)], fill=(255, 255, 255), width=int(12 * sz), joint='curve')
    opts = x['options']; oe = x.get('opt_emoji', [])
    if lay == 'mcq':
        for j, opt in enumerate(opts):
            a = ease((lt - 0.15 - j * 0.08) / 0.25)
            if a <= 0: continue
            y = 1150 + j * 150; xo = int((1 - a) * 400); ok = j == x['answer']
            fill, tc = (255, 255, 255, 235), (30, 24, 60)
            if reveal:
                if ok: fill, tc = (60, 200, 100, 255), (255, 255, 255)
                else: fill, tc = (255, 255, 255, int(235 - 150 * ru)), (120, 110, 150)
            sc = 1 + (pulse if ok else 0); hw, hh = 400 * sc, 60 * sc
            rr(d, (540 - hw + xo, y - hh, 540 + hw + xo, y + hh), 60, fill)
            d.ellipse((540 - hw + 24 + xo, y - 42, 540 - hw + 108 + xo, y + 42), fill=(255, 255, 255) if reveal and ok else (40, 30, 90))
            d.text((540 - hw + 66 + xo, y), 'ABC'[j], font=F(44), fill=(60, 200, 100) if reveal and ok else (255, 255, 255), anchor='mm')
            fs = 52
            while fs > 30 and d.textlength(opt, font=F(fs)) > 520: fs -= 4
            d.text((560 + xo, y), opt, font=F(fs), fill=tc, anchor='mm')
            if reveal and ok: tick(540 + hw - 70 + xo, y)
    elif lay == 'versus':
        for j, opt in enumerate(opts[:2]):
            a = back((lt - 0.15 - j * 0.1) / 0.35)
            if a <= 0.02: continue
            cx = 290 if j == 0 else 790; y = 1270; ok = j == x['answer']
            fill, tc = (255, 255, 255, 240), (30, 24, 60)
            if reveal:
                if ok: fill, tc = (60, 200, 100, 255), (255, 255, 255)
                else: fill, tc = (255, 255, 255, int(240 - 150 * ru)), (120, 110, 150)
            sc = a * (1 + (pulse if ok else 0)); hw, hh = 225 * sc, 200 * sc
            rr(d, (cx - hw, y - hh, cx + hw, y + hh), 44, fill)
            if j < len(oe) and sc > 0.3:
                e = emoji_img(oe[j], 170 * sc); im.alpha_composite(e, (int(cx - e.width / 2), int(y - 55 * sc - e.height / 2)))
            fs = 50
            while fs > 28 and d.textlength(opt, font=F(fs)) > 400: fs -= 4
            d.text((cx, y + 120 * sc), opt, font=F(fs * sc), fill=tc, anchor='mm')
            if reveal and ok: tick(cx + hw - 50, y - hh + 50, 0.9)
        if ease((lt - 0.3) / 0.2) > 0:
            d.ellipse((540 - 52, 1270 - 52, 540 + 52, 1270 + 52), fill=INK)
            d.text((540, 1270), 'VS', font=F(46), fill=(255, 222, 74), anchor='mm')
    else:  # tiles 2x2
        for j, opt in enumerate(opts[:4]):
            a = back((lt - 0.15 - j * 0.07) / 0.3)
            if a <= 0.02: continue
            cx = 300 if j % 2 == 0 else 780; cy2 = 1030 + (j // 2) * 360; ok = j == x['answer']
            fill, tc = (255, 255, 255, 240), (30, 24, 60)
            if reveal:
                if ok: fill, tc = (60, 200, 100, 255), (255, 255, 255)
                else: fill, tc = (255, 255, 255, int(240 - 150 * ru)), (120, 110, 150)
            sc = a * (1 + (pulse if ok else 0)); hw, hh = 215 * sc, 160 * sc
            rr(d, (cx - hw, cy2 - hh, cx + hw, cy2 + hh), 40, fill)
            d.ellipse((cx - hw + 14, cy2 - hh + 14, cx - hw + 74, cy2 - hh + 74), fill=(255, 255, 255) if reveal and ok else (40, 30, 90))
            d.text((cx - hw + 44, cy2 - hh + 44), 'ABCD'[j], font=F(34), fill=(60, 200, 100) if reveal and ok else (255, 255, 255), anchor='mm')
            if j < len(oe) and sc > 0.3:
                e = emoji_img(oe[j], 150 * sc); im.alpha_composite(e, (int(cx - e.width / 2), int(cy2 - 30 * sc - e.height / 2)))
            fs = 40
            while fs > 24 and d.textlength(opt, font=F(fs)) > 380: fs -= 4
            d.text((cx, cy2 + 110 * sc), opt, font=F(fs * sc), fill=tc, anchor='mm')
    # stick man reactor (top corner, away from the timer)
    tm0 = q.get('style', {}).get('timer', 'ring')
    sx = 965 if tm0 == 'ring-left' else (100 if tm0 == 'bar' else 115)
    if lt < think0: mood = 'point' if lt > 0.3 else 'wave'
    elif lt < think0 + THINK - 1.0: mood = 'think'
    elif lt < think0 + THINK: mood = 'nervous'
    else: mood = 'happy'
    hx, hy, hr = stick(d, sx, 478, 265, mood, t, face_dir=1 if sx < 540 else -1)
    if mood == 'think': bubble(d, hx + (60 if sx < 540 else -60), hy - hr - 40, '?', 40)
    if mood == 'happy' and lt - think0 - THINK < 1.2: bubble(d, hx + (95 if sx < 540 else -95), hy - hr - 40, 'YES!', 32)
    # timer
    if think0 <= lt < think0 + THINK:
        u = (lt - think0) / THINK; rem = math.ceil(THINK - (lt - think0) - 1e-6)
        pul = 1 + 0.25 * max(0, 1 - ((lt - think0) % 1) / 0.25)
        tm = q.get('style', {}).get('timer', 'ring')
        by = 1850 if LAND else 456  # landscape: timer drawn in a spare strip, moved by frame_land()
        if LAND and tm != 'bar': tm = 'bar'
        if tm == 'bar':
            rr(d, (140, by - 10, 940, by + 10), 10, (20, 16, 40, 160))
            rr(d, (140, by - 10, 140 + max(20, int(800 * (1 - u))), by + 10), 10, (255, 222, 74))
            d.text((985, by), str(rem), font=F(54 * pul), fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=INK)
        else:
            cx, cy3 = (180, 470) if tm == 'ring-left' else (900, 470)
            d.ellipse((cx - 70, cy3 - 70, cx + 70, cy3 + 70), fill=(20, 16, 40, 200))
            d.arc((cx - 62, cy3 - 62, cx + 62, cy3 + 62), -90, -90 + 360 * (1 - u), fill=(255, 222, 74), width=12)
            d.text((cx, cy3), str(rem), font=F(70 * pul), fill=(255, 255, 255), anchor='mm')
    if reveal and x.get('fact'):
        a = ease((lt - think0 - THINK - 0.2) / 0.25)
        if a > 0:
            fs = 50 if len(x['fact']) < 34 else 42
            tw = min(960, d.textlength(clean(x['fact']), font=F(fs)) + (70 if '|' in x['fact'] else 0))
            fy = 1690 if lay == 'tiles' else 1625
            rr(d, (540 - tw / 2 - 36, fy - 50 * a, 540 + tw / 2 + 36, fy + 50 * a), 50, (20, 16, 40, 200))
            if a > 0.9: text_mixed(d, im, (540, fy), x['fact'], fs, (255, 255, 255))
    return im

# ---------------- audio ----------------
def tone(f, dur, amp=0.3, dec=8):
    t = np.arange(int(SR * dur)) / SR
    return amp * np.sin(2 * np.pi * f * t) * np.exp(-dec * t)
def add(buf, sig, at):
    if sig is None: return
    i = int(at * SR); j = min(len(buf), i + len(sig))
    if j > i: buf[i:j] += sig[:j - i]
def audio(q, segs, speech, total, path):
    st = q.get('style', {})
    music = np.zeros(int(SR * (total + 0.5))); sfx = np.zeros_like(music); voice = np.zeros_like(music)
    beat = 60 / st.get('bpm', 124); r0 = st.get('root', 220)
    notes = [r0 * 2 ** (k / 12) for k in (0, 4, 7, 4, 2, 6, 9, 6)]
    t, step = 0, 0
    while t < total:
        add(music, tone(55, 0.25, 0.35, 18) * np.linspace(1, 0.2, int(SR * 0.25)), t)
        add(music, np.random.randn(int(SR * 0.04)) * 0.03, t + beat / 2)
        add(music, tone(notes[step % 8], beat * 0.9, 0.05, 3), t)
        t += beat; step += 1
    add(sfx, tone(880, 0.5, 0.25, 5) + tone(1318, 0.5, 0.15, 5), 0.02)
    for s in segs:
        if s[0] != 'q': continue
        t0, think0 = s[2], s[4]
        add(sfx, np.random.randn(int(SR * 0.25)) * np.linspace(0, 0.15, int(SR * 0.25)), t0)
        for k in range(int(THINK)): add(sfx, tone(1500, 0.06, 0.3, 60) * (1 if k >= THINK - 3 else 0.5), t0 + think0 + k)
        add(sfx, tone(1046.5, 0.8, 0.25, 4) + tone(1568, 0.8, 0.16, 4) + tone(2093, 0.8, 0.08, 5), t0 + think0 + THINK)
    for at, a in speech: add(voice, a, at)
    env = np.convolve((np.abs(voice) > 0.02).astype(float), np.ones(int(SR * 0.25)) / int(SR * 0.25), 'same')
    music *= 1 - 0.65 * np.clip(env * 3, 0, 1)
    mix = music * 0.8 + sfx * 0.7 + voice * 1.0
    mix = np.clip(mix / max(1e-6, np.abs(mix).max() / 0.9), -1, 1)
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())

_CLEAR = None
def frame_land(q, BGL, segs, t):
    """Landscape 1920x1080: draw the portrait layout on a clear canvas, then rearrange its parts."""
    global _CLEAR
    if _CLEAR is None: _CLEAR = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    src = frame(q, _CLEAR, segs, t); out = BGL.copy()
    def put(box, sc, xy):
        part = src.crop(box)
        if sc != 1: part = part.resize((int(part.width * sc), int(part.height * sc)), Image.LANCZOS)
        out.alpha_composite(part, (int(xy[0]), int(xy[1])))
    seg = next((s for s in segs if s[2] <= t < s[2] + s[3]), segs[-1])
    if seg[0] == 'hook': put((0, 430, W, 1580), 0.88, ((LW - W * 0.88) / 2, 40)); return out
    if seg[0] == 'end': put((0, 500, W, 1760), 0.82, ((LW - W * 0.82) / 2, 30)); return out
    lay = q['questions'][seg[1]].get('layout', 'mcq')
    put((0, 170, W, 470), 0.78, ((LW - W * 0.78) / 2, 0))                     # title, progress, level, stick man
    put((0, 1800, W, 1900), 1.0, ((LW - W) / 2, 225))                        # timer bar
    card = (85, 475, 995, 1050) if lay != 'tiles' else (85, 470, 995, 815)
    opts = {'mcq': (0, 1075, W, 1530), 'versus': (30, 1055, 1050, 1485), 'tiles': (60, 855, 1020, 1565)}[lay]
    cs = 0.82 if lay != 'tiles' else 0.9
    ch = (card[3] - card[1]) * cs
    put(card, cs, (80, 335 + (520 - ch) / 2))
    osc = 0.9 if lay != 'tiles' else 0.78
    oh = (opts[3] - opts[1]) * osc
    put(opts, osc, (1000 + (880 - (opts[2] - opts[0]) * osc) / 2, 335 + (520 - oh) / 2))
    fy = 1690 if lay == 'tiles' else 1625
    put((0, fy - 70, W, fy + 70), 1.0, ((LW - W) / 2, 900))                  # fact pill
    return out

def main(spec, out, still=None):
    global THINK, LAND
    q = json.load(open(spec)); THINK = float(q.get('think', 3.0))
    land = LAND = q.get('format') == 'landscape'
    BG = build_bg(q, LW, LH) if land else build_bg(q)
    render = (lambda segs, t: frame_land(q, BG, segs, t)) if land else (lambda segs, t: frame(q, BG, segs, t))
    VW, VH = (LW, LH) if land else (W, H)
    if still:
        segs, _, total = plan(q, voice_on=False)
        for tt in still: render(segs, min(tt, total - 0.01)).convert('RGB').save(f'{out}_{tt}.jpg', quality=80)
        return
    segs, speech, total = plan(q)
    wav = out + '.wav'; audio(q, segs, speech, total, wav)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{VW}x{VH}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                          '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        p.stdin.write(render(segs, i / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print(out, round(total, 1), 's')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None)
