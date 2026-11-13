#!/usr/bin/env python3
"""Quiz Short renderer: 1080x1920, 30fps, 5 questions, countdown, reveal, loop ending.
usage: python3 quiz.py quizzes/flags.json out.mp4"""
import json, sys, math, subprocess, wave, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
FE = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
EMO = ImageFont.truetype(FE, 109, layout_engine=ImageFont.Layout.RAQM)
def F(s): return ImageFont.truetype(FB, s)

HOOK, POP, THINK, REVEAL, END = 1.3, 0.35, 3.0, 1.35, 2.0
QD = POP + THINK + REVEAL

def ease(u): u = max(0, min(1, u)); return 1 - (1 - u) ** 3
def back(u):
    u = max(0, min(1, u)); c = 1.70158
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2

def emoji_img(s, h):
    tmp = Image.new('RGBA', (140 * max(1, len(s)) + 40, 150), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((10, 10), s, font=EMO, embedded_color=True)
    tmp = tmp.crop(tmp.getbbox())
    h = max(2, h); return tmp.resize((max(1, int(tmp.width * h / tmp.height)), h), Image.LANCZOS)

def text_mixed(d, im, xy, s, size, fill, anchor='mm', stroke=0):
    """text with optional trailing emoji, centered"""
    parts = s.split('|')
    while size > 20 and d.textlength(parts[0], font=F(size)) + (size * 1.2 if len(parts) > 1 else 0) > 940:
        size -= 4
    f = F(size)
    if len(parts) == 1:
        d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(20, 16, 40))
        return
    t, e = parts
    tw = d.textlength(t, font=f); em = emoji_img(e, int(size * 1.05))
    x0 = xy[0] - (tw + 16 + em.width) / 2
    d.text((x0, xy[1]), t, font=f, fill=fill, anchor='lm', stroke_width=stroke, stroke_fill=(20, 16, 40))
    im.alpha_composite(em, (int(x0 + tw + 16), int(xy[1] - em.height / 2)))

def rr(d, box, r, fill, outline=None, w=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=w)

def build(q):
    c1, c2 = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in q['bg']]
    yy = np.linspace(0, 1, H)[:, None]
    grad = (np.array(c1) * (1 - yy) + np.array(c2) * yy)[:, None, :].repeat(W, 1).astype(np.uint8).squeeze()
    BG = Image.fromarray(grad.reshape(H, W, 3), 'RGB').convert('RGBA')
    # soft dots pattern
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
            pts = [(x, y0 + 26 * math.sin(x / 90 + y0)) for x in range(0, W + 20, 20)]
            dd.line(pts, fill=(255, 255, 255, 30), width=6)
    BG = Image.alpha_composite(BG, ov)
    qs = q['questions']
    def fit(e):
        im = emoji_img(e, 300)
        return im if im.width <= 800 else im.resize((800, int(im.height * 800 / im.width)), Image.LANCZOS)
    prompts = [fit(x['emoji']) if x.get('emoji') else None for x in qs]
    total = HOOK + QD * len(qs) + END
    return BG, prompts, total

def frame(q, BG, prompts, t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    qs = q['questions']; n = len(qs)
    # header pill
    k = (t - HOOK) // QD if t >= HOOK else -1
    k = int(min(k, n - 1))
    if t < HOOK:  # HOOK: big title
        s = back(t / 0.45)
        sz = int(118 * s) or 1
        text_mixed(d, im, (540, 640), q['hook1'], sz, (255, 255, 255), stroke=10)
        text_mixed(d, im, (540, 800), q['hook2'], int(96 * s) or 1, (255, 222, 74), stroke=10)
        im2 = emoji_img(q['hook_emoji'], int(260 * s) or 1)
        im.alpha_composite(im2, (540 - im2.width // 2, 1000))
        return im
    if t >= HOOK + QD * n:  # END
        u = t - (HOOK + QD * n)
        s = back(u / 0.4)
        text_mixed(d, im, (540, 640), 'How many did', int(100 * s) or 1, (255, 255, 255), stroke=9)
        text_mixed(d, im, (540, 770), 'you get?', int(110 * s) or 1, (255, 222, 74), stroke=9)
        text_mixed(d, im, (540, 980), 'Comment your score|👇', int(64 * s) or 1, (255, 255, 255), stroke=6)
        # score chips
        for i in range(n):
            x = 540 + (i - (n - 1) / 2) * 120
            a = ease((u - 0.3 - i * 0.08) / 0.25)
            if a > 0:
                rr(d, (x - 46, 1130 - 46 * a, x + 46, 1130 + 46 * a), 24, (255, 255, 255, 230))
                d.text((x, 1130), f'{i+1}', font=F(54), fill=(40, 30, 90), anchor='mm')
        return im
    lt = t - HOOK - k * QD
    x = qs[k]
    # top: progress + label
    d.text((540, 230), q['title'], font=F(52), fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=(20, 16, 40))
    for i in range(n):
        cx = 540 + (i - (n - 1) / 2) * 70
        col = (255, 222, 74) if i < k else (255, 255, 255) if i == k else (255, 255, 255, 90)
        r = 16 if i == k else 11
        d.ellipse((cx - r, 310 - r, cx + r, 310 + r), fill=col)
    level = ['EASY', 'EASY', 'MEDIUM', 'HARD', 'EXPERT'][k] if n == 5 else ''
    lc = {'EASY': (90, 220, 120), 'MEDIUM': (255, 190, 60), 'HARD': (255, 110, 70), 'EXPERT': (230, 60, 90)}.get(level, (255, 255, 255))
    rr(d, (390, 350, 690, 420), 35, lc)
    d.text((540, 385), f'Q{k+1} · {level}', font=F(38), fill=(255, 255, 255), anchor='mm')
    # prompt card
    s = back(lt / POP)
    cw, ch = int(900 * s), int(560 * s)
    if cw > 10:
        rr(d, (540 - cw // 2, 760 - ch // 2, 540 + cw // 2, 760 + ch // 2), 48, (255, 255, 255, 245))
        if prompts[k] is not None:
            p = prompts[k]
            if 'text' in x:
                pp = p.resize((max(1, int(p.width * 0.62 * s)), max(1, int(p.height * 0.62 * s))))
                im.alpha_composite(pp, (540 - pp.width // 2, 590 - pp.height // 2 + 30))
            else:
                pp = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))))
                im.alpha_composite(pp, (540 - pp.width // 2, 760 - pp.height // 2))
        if 'text' in x and s > 0.6:
            lines = x['text'].split('\n'); fs = 62 if prompts[k] is None else 54
            y0 = 760 - (len(lines) - 1) * fs * 0.6 + (90 if prompts[k] is not None else 0)
            for j, ln in enumerate(lines):
                d.text((540, y0 + j * fs * 1.2), ln, font=F(fs), fill=(30, 24, 60), anchor='mm')
    # options
    reveal = lt >= POP + THINK
    for j, opt in enumerate(x['options']):
        a = ease((lt - 0.15 - j * 0.08) / 0.25)
        if a <= 0: continue
        y = 1150 + j * 150
        xo = int((1 - a) * 400)
        correct = j == x['answer']
        fill = (255, 255, 255, 235); tc = (30, 24, 60)
        if reveal:
            ru = ease((lt - POP - THINK) / 0.2)
            if correct: fill = (60, 200, 100, 255); tc = (255, 255, 255)
            else: fill = (255, 255, 255, int(235 - 150 * ru)); tc = (120, 110, 150)
        sc = 1 + (0.06 * math.sin(min(1, (lt - POP - THINK) / 0.3) * math.pi) if reveal and correct else 0)
        hw, hh = 400 * sc, 60 * sc
        rr(d, (540 - hw + xo, y - hh, 540 + hw + xo, y + hh), 60, fill)
        badge = 'ABC'[j]
        d.ellipse((540 - hw + 24 + xo, y - 42, 540 - hw + 108 + xo, y + 42), fill=(40, 30, 90) if not (reveal and correct) else (255, 255, 255))
        d.text((540 - hw + 66 + xo, y), badge, font=F(44), fill=(255, 255, 255) if not (reveal and correct) else (60, 200, 100), anchor='mm')
        d.text((560 + xo, y), opt, font=F(52), fill=tc, anchor='mm')
        if reveal and correct:
            cx0 = 540 + hw - 70 + xo
            d.line([(cx0 - 22, y + 2), (cx0 - 6, y + 20), (cx0 + 24, y - 20)], fill=(255, 255, 255), width=12, joint='curve')
    # countdown ring (top-right of card)
    if POP <= lt < POP + THINK:
        u = (lt - POP) / THINK; rem = 3 - int((lt - POP))
        tm = q.get('style', {}).get('timer', 'ring')
        pul = 1 + 0.25 * max(0, 1 - ((lt - POP) % 1) / 0.25)
        if tm == 'bar':
            rr(d, (140, 446, 940, 466), 10, (20, 16, 40, 160))
            rr(d, (140, 446, 140 + max(20, int(800 * (1 - u))), 466), 10, (255, 222, 74))
            d.text((985, 456), str(rem), font=F(int(54 * pul)), fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=(20, 16, 40))
        else:
            cx, cy = (180, 470) if tm == 'ring-left' else (900, 470)
            d.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=(20, 16, 40, 200))
            d.arc((cx - 62, cy - 62, cx + 62, cy + 62), -90, -90 + 360 * (1 - u), fill=(255, 222, 74), width=12)
            d.text((cx, cy), str(rem), font=F(int(70 * pul)), fill=(255, 255, 255), anchor='mm')
    if reveal and x.get('fact'):
        a = ease((lt - POP - THINK - 0.2) / 0.25)
        if a > 0:
            fs = 50 if len(x['fact']) < 34 else 42
            tw = d.textlength(x['fact'].split('|')[0], font=F(fs)) + (70 if '|' in x['fact'] else 0)
            rr(d, (540 - tw / 2 - 36, 1625 - 50 * a, 540 + tw / 2 + 36, 1625 + 50 * a), 50, (20, 16, 40, 200))
            if a > 0.9: text_mixed(d, im, (540, 1625), x['fact'], fs, (255, 255, 255))
    return im

# ---------- audio ----------
SR = 44100
def tone(f, dur, amp=0.3, dec=8):
    t = np.arange(int(SR * dur)) / SR
    return amp * np.sin(2 * np.pi * f * t) * np.exp(-dec * t)
def add(buf, sig, at):
    i = int(at * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]
def audio(q, total, path):
    n = len(q['questions']); buf = np.zeros(int(SR * (total + 0.5)))
    # music: 124bpm light loop
    st = q.get('style', {}); beat = 60 / st.get('bpm', 124); t = 0; step = 0
    r0 = st.get('root', 220); notes = [r0 * 2 ** (k / 12) for k in (0, 4, 7, 4, 2, 6, 9, 6)]
    while t < total:
        add(buf, tone(55, 0.25, 0.35, 18) * np.linspace(1, 0.2, int(SR * 0.25)), t)           # kick
        add(buf, np.random.randn(int(SR * 0.04)) * 0.03, t + beat / 2)                      # hat
        add(buf, tone(notes[step % 8], beat * 0.9, 0.05, 3), t)                             # pluck
        t += beat; step += 1
    add(buf, tone(880, 0.5, 0.25, 5) + tone(1318, 0.5, 0.15, 5), 0.05)  # hook sting
    for k in range(n):
        t0 = HOOK + k * QD
        sw = np.random.randn(int(SR * 0.25)) * np.linspace(0, 0.18, int(SR * 0.25))
        add(buf, sw, t0)                                                                     # whoosh
        for s in range(3): add(buf, tone(1500, 0.06, 0.35, 60), t0 + POP + s)               # ticks
        add(buf, tone(1046.5, 0.8, 0.3, 4) + tone(1568, 0.8, 0.2, 4) + tone(2093, 0.8, 0.1, 5), t0 + POP + THINK)  # ding
    add(buf, tone(660, 0.6, 0.25, 4) + tone(990, 0.6, 0.18, 4), HOOK + n * QD)
    buf = np.clip(buf / max(1, np.abs(buf).max() / 0.85), -1, 1)
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())

def main(spec, out, still=None):
    q = json.load(open(spec)); BG, prompts, total = build(q)
    if still:
        for tt in still: frame(q, BG, prompts, tt).convert('RGB').save(f'{out}_{tt}.jpg', quality=80)
        return
    wav = out + '.wav'; audio(q, total, wav)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                          '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        p.stdin.write(frame(q, BG, prompts, i / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print(out, round(total, 1), 's')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None)
