"""Wildhearted reels: grayscale plates becoming colour with six reveal effects."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from render import W, H, label, font, ease, ease_out, paste_center, shadowed

WH = '/home/claude/wh'
P2C = json.load(open(f'{WH}/plate2color.json'))
DARK = (24, 31, 29); GOLD = (217, 169, 59); CREAM = (246, 238, 222)
SW, SH = 1103, 1426

def plate(n):
    key = [k for k in P2C if k.startswith(f'Plate{n:02d}_')][0]
    g = np.asarray(Image.open(f'{WH}/gray_small/{key}.png').convert('RGB'), np.float32)
    c = np.asarray(Image.open(f'{WH}/colorized_set/{P2C[key]}').convert('RGB'), np.float32)
    return key, g, c

def noise(seed, scales=((6, 1.0), (14, 0.5), (34, 0.25))):
    rng = np.random.default_rng(seed); acc = np.zeros((SH, SW), np.float32); tot = 0
    for s, wgt in scales:
        small = Image.fromarray(rng.random((max(2, int(s * SH / SW)), s)).astype(np.float32), 'F')
        acc += wgt * np.asarray(small.resize((SW, SH), Image.BICUBIC), np.float32); tot += wgt
    acc /= tot; return (acc - acc.min()) / (acc.max() - acc.min())

YY, XX = np.mgrid[0:SH, 0:SW].astype(np.float32)

def composite(g, c, m, glow=0.0):
    m3 = m[..., None]
    out = g * (1 - m3) + c * m3
    if glow > 0:
        e = (4 * m * (1 - m))[..., None]
        out = out + glow * 255 * e
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def frame_from(img, zoom, cx=SW / 2, cy=SH / 2):
    return R.cover_crop(img, cx, cy, zoom).convert('RGBA')

COVER = None
def cover():
    global COVER
    if COVER is None:
        im = Image.open(f'{WH}/cover-1.png').convert('RGB'); COVER = im.crop((1066, 0, im.width, im.height))
    return COVER

def end_card(t_in, line2='40 grayscale collage portraits\nmade for colored pencils'):
    img = Image.new('RGBA', (W, H), DARK + (255,))
    a = ease_out(t_in / 0.35)
    el = cover().copy().convert('RGBA'); el.thumbnail((640, 830), Image.LANCZOS)
    s = 0.93 + 0.07 * a
    el = shadowed(el, blur=22, off=(0, 18), opacity=200).resize((int((el.width + 132) * s), int((el.height + 132) * s)), Image.LANCZOS)
    paste_center(img, el, W / 2, 690)
    label(img, line2, 1250, size=40, kind='serif_it', fg=CREAM, bg=None, pad=(0, 0))
    label(img, 'Available on Amazon', 1385, size=44, kind='sans_bold', fg=DARK, bg=GOLD, pad=(40, 16), radius=40)
    label(img, 'Search: Wildhearted Eka Lestienne', 1480, size=32, kind='sans_bold', fg=CREAM, bg=None, pad=(0, 0))
    if a < 1:
        img = Image.blend(Image.new('RGBA', (W, H), DARK + (255,)), img, a)
    return img

def hook(img, text, y=270, alpha=1.0, size=64):
    label(img, text, y, size=size, fg=CREAM, bg=DARK, alpha=alpha * 0.97, maxw=900)

# ---------------------------------------------------------------- effects
def reel_reveal(n, beats, text, mode, origin=(0.5, 0.45), seed=1):
    key, g, c = plate(n)
    b = beats; t0 = b[1]; t1 = t0 + 5.0
    end_t = min(x for x in b if x >= t1 + 2.2); dur = end_t + 2.8
    nz = noise(seed)
    if mode == 'sweep':
        d = (XX / SW * 0.55 + YY / SH * 0.45) + 0.10 * (nz - 0.5)
        lo, hi, soft, glow = -0.15, 1.15, 0.06, 0.35
    elif mode == 'bloom':
        ox, oy = origin[0] * SW, origin[1] * SH
        r = np.sqrt((XX - ox) ** 2 + (YY - oy) ** 2); d = r / r.max() + 0.12 * (nz - 0.5)
        lo, hi, soft, glow = -0.1, 1.15, 0.05, 0.45
    else:  # scribble: patches fill in like layers of pencil
        r = np.sqrt((XX - SW / 2) ** 2 + (YY - SH * 0.45) ** 2); r = r / r.max()
        d = 0.65 * noise(seed + 7, ((10, 1.0), (24, 0.6), (60, 0.35))) + 0.35 * r
        d = (d - d.min()) / (d.max() - d.min())
        lo, hi, soft, glow = -0.05, 1.08, 0.025, 0.12
    gray_img = Image.fromarray(g.astype(np.uint8)); color_img = Image.fromarray(c.astype(np.uint8))
    def frame(t):
        if t >= end_t: return end_card(t - end_t)
        zoom = 1.0 + 0.08 * min(t / end_t, 1)
        if t < t0: src = gray_img
        elif t >= t1: src = color_img
        else:
            p = lo + (hi - lo) * ease((t - t0) / (t1 - t0))
            m = np.clip((p - d) / soft, 0, 1)
            src = composite(g, c, m, glow)
        img = frame_from(src, zoom)
        if t < t1 + 1.0:
            hook(img, text, alpha=1.0 if t < t1 + 0.6 else 1 - (t - t1 - 0.6) / 0.4)
        return img
    return frame, dur

def reel_slider(n, beats, text):
    key, g, c = plate(n)
    gray_img = Image.fromarray(g.astype(np.uint8)); color_img = Image.fromarray(c.astype(np.uint8))
    b = beats
    keys = [(b[0], 0.0), (b[4], 0.72), (b[8], 0.28), (b[12], 1.0)]
    end_t = b[15]; dur = end_t + 2.8
    s = max(W / SW, H / SH); vis_w = W / s; x_off = (SW - vis_w) / 2
    def xpos(t):
        if t <= keys[0][0]: return 0.0
        for (ta, xa), (tb, xb) in zip(keys, keys[1:]):
            if t <= tb: return xa + (xb - xa) * ease((t - ta) / (tb - ta))
        return 1.0
    def frame(t):
        if t >= end_t: return end_card(t - end_t)
        f = xpos(t); split = x_off + f * vis_w
        src = gray_img.copy(); src.paste(color_img.crop((0, 0, int(split), SH)), (0, 0))
        img = frame_from(src, 1.0); d = ImageDraw.Draw(img)
        if 0.0 < f < 1.0:
            x = f * W
            d.rectangle((x - 3, 0, x + 3, H), fill=CREAM)
            d.ellipse((x - 46, 960 - 46, x + 46, 960 + 46), fill=CREAM, outline=GOLD, width=5)
            d.polygon([(x - 30, 960), (x - 12, 946), (x - 12, 974)], fill=DARK); d.polygon([(x + 30, 960), (x + 12, 946), (x + 12, 974)], fill=DARK)
        if f < 1.0:
            label(img, 'YOUR COLOUR', 1500, size=28, kind='sans_bold', fg=DARK, bg=GOLD, pad=(20, 10), radius=18) if f > 0.5 else None
            label(img, 'AS PRINTED', 1500, size=28, kind='sans_bold', fg=CREAM, bg=DARK, pad=(20, 10), radius=18) if f <= 0.5 else None
        hook(img, text)
        return img
    return frame, dur

def reel_montage(ns, beats, text):
    pages = [plate(n) for n in ns]
    b = beats; per = 6
    starts = [b[k * per] for k in range(3)]; flips = [b[k * per + 3] for k in range(3)]
    end_t = b[3 * per]; dur = end_t + 2.8
    pw = 900; ph = int(pw * SH / SW)
    prepared = []
    for key, g, c in pages:
        gi = Image.fromarray(g.astype(np.uint8)).resize((pw, ph), Image.LANCZOS).convert('RGBA')
        ci = Image.fromarray(c.astype(np.uint8)).resize((pw, ph), Image.LANCZOS).convert('RGBA')
        prepared.append((shadowed(gi, blur=20, opacity=180), shadowed(ci, blur=20, opacity=180), Image.fromarray(c.astype(np.uint8))))
    bgs = [Image.blend(p[2].resize((40, 52)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR), Image.new('RGB', (W, H), DARK), 0.72).convert('RGBA') for p in prepared]
    def frame(t):
        if t >= end_t: return end_card(t - end_t)
        i = min(2, sum(1 for s in starts if t >= s) - 1)
        gs, cs, _ = prepared[i]
        img = Image.new('RGBA', (W, H), DARK + (255,)) if t < flips[i] else bgs[i].copy()
        local = t - starts[i]; sc = 1.0 + 0.03 * min(local / 2, 1)
        if t < flips[i]: el = gs
        else:
            a = min(1, (t - flips[i]) / 0.3)
            el = Image.blend(gs, cs, a) if a < 1 else cs
        el = el.resize((int(el.width * sc), int(el.height * sc)), Image.BILINEAR)
        paste_center(img, el, W / 2, 1030)
        if flips[i] <= t < flips[i] + 0.18:
            fl = Image.new('RGBA', (W, H), (255, 255, 255, int(150 * (1 - (t - flips[i]) / 0.18)))); img.alpha_composite(fl)
        hook(img, text, y=230, size=60)
        return img
    return frame, dur

def grade(c, kind):
    x = c / 255.0; orig = x.copy()
    wm = np.clip((orig.mean(axis=2, keepdims=True) - 0.86) / 0.1, 0, 1)
    if kind == 'Warm':
        x = x * np.array([1.08, 1.0, 0.82]); x = x ** 0.95
    elif kind == 'Cool':
        x = x * np.array([0.86, 0.98, 1.12]); x = x ** 1.03
    else:  # Pastel
        lum = x.mean(axis=2, keepdims=True); x = lum + (x - lum) * 0.6; x = 0.72 * x + 0.28
    x = x * (1 - wm) + orig * wm
    return Image.fromarray(np.clip(x * 255, 0, 255).astype(np.uint8))

def reel_moods(n, beats, text, moods=('Warm', 'Cool', 'Pastel')):
    key, g, c = plate(n)
    states = [Image.fromarray(g.astype(np.uint8))] + [grade(c, m) for m in moods] + [Image.fromarray(c.astype(np.uint8))]
    b = beats; marks = [b[0], b[3], b[6], b[9], b[12]]; end_t = b[15]; dur = end_t + 2.8
    tags = [None] + list(moods) + ['As coloured by the artist']
    def frame(t):
        if t >= end_t: return end_card(t - end_t)
        i = sum(1 for m in marks if t >= m) - 1
        a = min(1, (t - marks[i]) / 0.35) if i > 0 else 1
        src = Image.blend(states[i - 1], states[i], a) if a < 1 else states[i]
        img = frame_from(src, 1.0 + 0.06 * t / end_t)
        hook(img, text)
        if tags[i]: label(img, tags[i], 1480, size=30, kind='sans_bold', fg=DARK, bg=GOLD, pad=(22, 10), radius=18)
        return img
    return frame, dur


def pencil_sprite(color, length=520, width=50):
    L, Wd = length, width
    im = Image.new('RGBA', (L + 20, Wd + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    oy = 10; cone = 70
    body = tuple(int(v) for v in color)
    d.rectangle((10 + cone, oy, 10 + L - 30, oy + Wd), fill=body + (255,))
    d.rectangle((10 + cone, oy + Wd * 0.38, 10 + L - 30, oy + Wd * 0.62), fill=tuple(min(255, int(v * 1.18 + 20)) for v in body) + (255,))
    d.rectangle((10 + L - 30, oy, 10 + L, oy + Wd), fill=(70, 62, 58, 255))
    d.polygon([(10 + cone, oy), (10 + cone, oy + Wd), (10 + 18, oy + Wd / 2 + 6), (10 + 18, oy + Wd / 2 - 6)], fill=(232, 196, 150, 255))
    d.polygon([(10 + 22, oy + Wd / 2 - 6), (10 + 22, oy + Wd / 2 + 6), (10, oy + Wd / 2)], fill=body + (255,))
    return im

def reel_pencil(n, beats, text, origin=(0.5, 0.4), seed=1):
    key, g, c = plate(n)
    b = beats; t0 = b[1]; t1 = t0 + 7.0
    end_t = min(x for x in b if x >= t1 + 1.6); dur = end_t + 2.8
    rng = np.random.default_rng(seed)
    lum = c.mean(axis=2) / 255.0
    grain = noise(seed + 101, ((180, 1.0), (360, 0.6)))
    ox, oy = origin[0] * SW, origin[1] * SH
    strokes = []
    for pas, ang0 in ((0, 0.70), (1, -0.62)):
        sp = 36
        for yy in range(0, SH, sp):
            for xx in range(0, SW, sp):
                x = xx + rng.uniform(-10, 10); y = yy + rng.uniform(-10, 10)
                xi, yi = int(min(SW - 1, max(0, x))), int(min(SH - 1, max(0, y)))
                if lum[max(0, yi - 18):yi + 18, max(0, xi - 18):xi + 18].min() > 0.93: continue
                a = ang0 + rng.uniform(-0.18, 0.18); ln = rng.uniform(70, 115)
                dist = np.hypot(x - ox, y - oy) / np.hypot(SW, SH)
                order = dist + 0.18 * rng.random() + (0.42 if pas else 0.0)
                strokes.append((order, pas, x, y, a, ln))
    strokes.sort()
    omax = strokes[-1][0]
    times = [t0 + (t1 - t0 - 0.6) * (o / omax) ** 1.15 for o, *_ in strokes]
    gray_img = Image.fromarray(g.astype(np.uint8)); color_img = Image.fromarray(c.astype(np.uint8))
    st = {'t': -1, 'k': 0, 'm': [Image.new('L', (SW, SH), 0), Image.new('L', (SW, SH), 0)], 'tip': None}
    def draw_upto(t):
        if t < st['t']:
            st.update(t=-1, k=0, m=[Image.new('L', (SW, SH), 0), Image.new('L', (SW, SH), 0)], tip=None)
        ds = [ImageDraw.Draw(st['m'][0]), ImageDraw.Draw(st['m'][1])]
        while st['k'] < len(strokes) and times[st['k']] <= t:
            _, pas, x, y, a, ln = strokes[st['k']]
            dx, dy = np.cos(a), np.sin(a); nx, ny = -dy, dx
            for j in range(-2, 3):
                ox2, oy2 = x + nx * j * 7, y + ny * j * 7
                ds[pas].line((ox2 - dx * ln / 2, oy2 - dy * ln / 2, ox2 + dx * ln / 2, oy2 + dy * ln / 2), fill=255, width=5)
            st['k'] += 1
        st['t'] = t
    def frame(t):
        if t >= end_t: return end_card(t - end_t)
        zoom = 1.0 + 0.06 * min(t / end_t, 1)
        tip = None
        if t < t0: src = gray_img
        elif t >= t1: src = color_img
        else:
            draw_upto(t)
            m0 = np.asarray(st['m'][0], np.float32) / 255; m1 = np.asarray(st['m'][1], np.float32) / 255
            m = np.clip(m0 * (grain > 0.5) * 0.7 + m1 * (0.6 + 0.4 * (grain <= 0.5)), 0, 1)
            fin = max(0.0, (t - (t1 - 0.6)) / 0.6); m = m + (1 - m) * fin
            src = composite(g, c, m)
            if st['k'] > 0 and fin < 0.5:
                _, pas, x, y, a, ln = strokes[st['k'] - 1]
                wig = np.sin(t * 38) * ln * 0.4
                tip = (x + np.cos(a) * wig, y + np.sin(a) * wig, c[int(min(SH - 1, max(0, y))), int(min(SW - 1, max(0, x)))])
        img = frame_from(src, zoom)
        if tip is not None:
            s = max(W / SW, H / SH) * zoom; bw, bh = W / s, H / s
            x0 = min(max(SW / 2 - bw / 2, 0), SW - bw); y0 = min(max(SH / 2 - bh / 2, 0), SH - bh)
            px, py = (tip[0] - x0) * s, (tip[1] - y0) * s
            if st['tip'] is not None and t > 0: px, py = st['tip'][0] * 0.55 + px * 0.45, st['tip'][1] * 0.55 + py * 0.45
            st['tip'] = (px, py)
            pen = pencil_sprite(tip[2]).rotate(-128, expand=True, resample=Image.BICUBIC)
            pen = shadowed(pen, blur=8, off=(10, 14), opacity=90)
            ang = np.deg2rad(-128); half = (520 + 20) / 2
            tipx = pen.width / 2 - np.cos(ang) * half * -1; tipy = pen.height / 2 + np.sin(ang) * half * -1
            img.alpha_composite(pen, (int(px - tipx), int(py - tipy)))
        if t < t1 + 1.0:
            hook(img, text, alpha=1.0 if t < t1 + 0.6 else 1 - (t - t1 - 0.6) / 0.4)
        return img
    return frame, dur

# ---------------------------------------------------------------- registry
WREELS = {
 'w01_sweep_tiger-crown':     ('rv', 'Tea_by_the_Window', 148.3, dict(n=21, text='Watch her come alive.', mode='sweep', seed=3)),
 'w02_sweep_wolf':            ('rv', 'Threshold_of_New_Light', 89.3, dict(n=16, text='Grayscale is not an\nabsence of colour.', mode='sweep', seed=5)),
 'w03_sweep_dragon':          ('rv', 'River_of_Light', 83.5, dict(n=27, text='From gray to wild.', mode='sweep', seed=8)),
 'w04_bloom_toucan':          ('rv', 'C___Reverie', 54.1, dict(n=34, text='One spark of colour…', mode='bloom', origin=(0.6, 0.5), seed=11)),
 'w05_bloom_serpent':         ('rv', 'Golden_Medal', 47.4, dict(n=29, text='She was waiting\nfor your colours.', mode='bloom', origin=(0.6, 0.45), seed=13)),
 'w06_bloom_lion':            ('rv', 'A___Wild_colour', 40.5, dict(n=17, text='Every layer makes\nher glow.', mode='bloom', origin=(0.5, 0.42), seed=17)),
 'w07_layers_elephant':       ('rv', 'Tea_by_the_Window', 177.1, dict(n=14, text='What colouring this\npage feels like.', mode='scribble', seed=19)),
 'w08_layers_parrot':         ('rv', 'Threshold_of_New_Light', 40.0, dict(n=36, text='The shadows are already\nthere. Add colour.', mode='scribble', seed=23)),
 'w09_layers_fox':            ('rv', 'Golden_Medal', 57.4, dict(n=9, text='Slow evening.\nOne page. Pure calm.', mode='scribble', seed=29)),
 'w10_slider_rhino':          ('sl', 'Moon_on_the_Drum.wav', 52.0, dict(n=28, text='As printed vs. your colour')),
 'w11_slider_tiger':          ('sl', 'Clockwork', 53.7, dict(n=19, text='Before or after?')),
 'w12_slider_flamingo':       ('sl', 'Canopy', 95.9, dict(n=37, text='Gray first. Then magic.')),
 'w13_montage_companions':    ('mt', 'D___New_year', 51.4, dict(ns=(2, 3, 25), text='Every page has\na wild companion.')),
 'w14_montage_pick-a-page':   ('mt', 'Clockwork', 80.1, dict(ns=(22, 32, 40), text='Pick a page.\nMake it yours.')),
 'w15_montage_cat-people':    ('mt', 'Canopy', 126.5, dict(ns=(13, 15, 23), text='Cat people,\nthis book is for you.')),
 'w16_moods_chameleon':       ('md', 'Moon_on_the_Drum.wav', 122.0, dict(n=33, text='Same page. Three moods.')),
 'w17_moods_giraffe':         ('md', 'A___Wild_colour', 57.1, dict(n=35, text='There are no\ncorrect colours.', moods=('Pastel', 'Warm', 'Cool'))),
 'w18_moods_rabbit':          ('md', 'C___Reverie', 68.8, dict(n=8, text='Your palette,\nyour rules.', moods=('Cool', 'Pastel', 'Warm'))),
}

def build(rid):
    kind, tr, guess, kw = WREELS[rid]
    a, s, beats, _ = R.track_info(tr, guess)
    if kind == 'rv': fr, dur = reel_reveal(beats=beats, **kw)
    elif kind == 'sl': fr, dur = reel_slider(beats=beats, **kw)
    elif kind == 'mt': fr, dur = reel_montage(beats=beats, **kw)
    elif kind == 'pc': fr, dur = reel_pencil(beats=beats, **kw)
    else: fr, dur = reel_moods(beats=beats, **kw)
    return fr, dur, a, s

R.build = build


WREELS.update({
 'w19_sweep_familiar':        ('rv', 'Tea_by_the_Window', 191.8, dict(n=1, text='Meet her familiar.\nNow watch the colour.', mode='sweep', seed=31)),
 'w20_sweep_ride-the-wind':   ('rv', 'Threshold_of_New_Light', 20.8, dict(n=18, text='Ride the wind\nin full colour.', mode='sweep', seed=37)),
 'w21_sweep_old-creatures':   ('rv', 'River_of_Light', 108.3, dict(n=26, text='Old creatures,\nnew colours.', mode='sweep', seed=41)),
 'w22_bloom_second-sight':    ('rv', 'C___Reverie', 26.5, dict(n=31, text='Look into her eyes.\nNow watch.', mode='bloom', origin=(0.45, 0.45), seed=43)),
 'w23_bloom_impossible-cup':  ('rv', 'Golden_Medal', 36.1, dict(n=24, text='A cup full of colour…', mode='bloom', origin=(0.6, 0.42), seed=47)),
 'w24_bloom_white-rabbit':    ('rv', 'A___Wild_colour', 24.4, dict(n=7, text='Soft gray, then\nall the colour.', mode='bloom', origin=(0.5, 0.36), seed=53)),
 'w25_pencil_listening-forest': ('pc', 'Tea_by_the_Window', 44.4, dict(n=10, text='Quiet forest.\nSlow colour.', origin=(0.45, 0.35), seed=59)),
 'w26_pencil_morning-keeper': ('pc', 'Threshold_of_New_Light', 7.0, dict(n=4, text='Your morning ritual,\nin colour.', origin=(0.5, 0.3), seed=61)),
 'w27_pencil_horns-flowers':  ('pc', 'River_of_Light', 125.6, dict(n=6, text='Between horns\nand flowers.', origin=(0.4, 0.35), seed=67)),
 'w28_pencil_gentleness':     ('pc', 'A___Wild_colour', 88.4, dict(n=12, text='Gentle pages\nfor loud days.', origin=(0.5, 0.3), seed=71)),
 'w29_slider_earth':          ('sl', 'Clockwork', 31.5, dict(n=5, text='Gray or gold?')),
 'w30_slider_bull-moon':      ('sl', 'Canopy', 168.8, dict(n=11, text='As printed vs. your colour')),
 'w31_slider_messenger':      ('sl', 'Moon_on_the_Drum.wav', 143.7, dict(n=39, text='Swipe the city\ninto colour.')),
 'w32_moods_room-for-play':   ('md', 'D___New_year', 82.4, dict(n=38, text='Pick her mood.', moods=('Cool', 'Warm', 'Pastel'))),
 'w33_moods_sacred-absurdity': ('md', 'C___Reverie', 91.1, dict(n=30, text='Warm, cool\nor pastel?', moods=('Warm', 'Cool', 'Pastel'))),
 'w34_moods_faithful-wild':   ('md', 'D___New_year', 93.5, dict(n=20, text='Which mood\nis yours?', moods=('Pastel', 'Cool', 'Warm'))),
})

if __name__ == '__main__':
    rid = sys.argv[1]
    pts = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    R.render(rid, pts)
