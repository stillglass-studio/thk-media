"""Eka L. reel renderer: PIL frames piped to ffmpeg, cut to the beat."""
import json, math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = '/home/claude/in/EkaL_Product-Previews/EkaL_Product-Previews'
UP = '/mnt/user-data/uploads'
FONTS = '/home/claude/work/fonts'
OUT = '/home/claude/work/out'
ANALYSIS = json.load(open('/home/claude/work/audio/analysis.json'))

PLUM = (59, 18, 48); CREAM = (251, 243, 230); YELLOW = (255, 210, 63); PINK = (232, 51, 109)

def font(kind, size):
    p = {'serif': f'{FONTS}/fraunces-latin-600-normal.ttf',
         'serif_bold': f'{FONTS}/fraunces-latin-800-normal.ttf',
         'serif_it': f'{FONTS}/fraunces-latin-600-italic.ttf',
         'sans': '/usr/share/fonts/opentype/inter/Inter-Medium.otf',
         'sans_bold': '/usr/share/fonts/opentype/inter/Inter-Bold.otf'}[kind]
    if not os.path.exists(p):
        import glob
        cand = glob.glob('/usr/share/fonts/**/Inter*%s*.tt*' % ('Bold' if 'bold' in kind else 'Medium'), recursive=True)
        p = cand[0]
    return ImageFont.truetype(p, size)

_img_cache = {}
def load(path, mode='RGB'):
    k = (path, mode)
    if k not in _img_cache:
        _img_cache[k] = Image.open(path if path.startswith('/') else f'{ROOT}/{path}').convert(mode)
    return _img_cache[k]

def ease(x):  # ease in-out cubic
    x = max(0.0, min(1.0, x))
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def cover_crop(src, cx, cy, zoom):
    """Frame of W x H from src, centred on (cx,cy) in src px, zoom 1 = cover fit."""
    s = max(W / src.width, H / src.height) * zoom
    bw, bh = W / s, H / s
    x0 = min(max(cx - bw / 2, 0), src.width - bw); y0 = min(max(cy - bh / 2, 0), src.height - bh)
    return src.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + bw, y0 + bh))

def wrap(text, f, maxw, d):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def label(img, text, cy, size=74, kind='serif', fg=PLUM, bg=CREAM, maxw=820, pad=(40, 26), alpha=1.0, scale=1.0, radius=30, line_gap=10):
    d = ImageDraw.Draw(img)
    f = font(kind, int(size * scale))
    lines = []
    for part in text.split('\n'): lines += wrap(part, f, maxw * scale, d)
    asc, desc = f.getmetrics(); lh = asc + desc
    tw = max(d.textlength(l, font=f) for l in lines)
    bw, bh = tw + 2 * pad[0] * scale, len(lines) * lh + (len(lines) - 1) * line_gap + 2 * pad[1] * scale
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    x0, y0 = W / 2 - bw / 2, cy - bh / 2
    if bg is not None:
        ld.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=radius * scale, fill=bg + (int(240 * alpha),))
    y = y0 + pad[1] * scale
    for l in lines:
        ld.text((W / 2, y), l, font=f, fill=fg + (int(255 * alpha),), anchor='ma'); y += lh + line_gap
    img.alpha_composite(layer) if img.mode == 'RGBA' else img.paste(layer, (0, 0), layer)
    return (x0, y0, x0 + bw, y0 + bh)

def shadowed(el, blur=14, off=(0, 12), opacity=110):
    pad = blur * 3
    canvas = Image.new('RGBA', (el.width + 2 * pad, el.height + 2 * pad), (0, 0, 0, 0))
    a = el.split()[3].point(lambda v: v * opacity // 255)
    sh = Image.new('RGBA', el.size, (20, 5, 15, 0)); sh.putalpha(a)
    canvas.paste(sh, (pad + off[0], pad + off[1]), sh)
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(el, (pad, pad))
    return canvas

def paste_center(dst, el, cx, cy):
    dst.alpha_composite(el, (int(cx - el.width / 2), int(cy - el.height / 2)))

# ------------------------------------------------------------------ end cards
def end_band(img, title, sub, alpha):
    """Soft brand band for reach reels (sits above the caption zone)."""
    label(img, title, 1250, size=42, kind='serif', alpha=alpha, maxw=980, pad=(30, 18))
    label(img, sub, 1352, size=34, kind='sans_bold', fg=CREAM, bg=PLUM, alpha=alpha, maxw=860, pad=(28, 14), radius=22)

def end_card(t_in, art, title, sub, price, art_box=(760, 700)):
    """Full conversion end card on plum."""
    img = Image.new('RGBA', (W, H), PLUM + (255,))
    a = ease_out(t_in / 0.35)
    el = art.copy().convert('RGBA'); el.thumbnail(art_box, Image.LANCZOS)
    framed = Image.new('RGBA', (el.width + 24, el.height + 24), CREAM + (255,)); framed.alpha_composite(el, (12, 12))
    framed = shadowed(framed, blur=18, off=(0, 16), opacity=140)
    s = 0.92 + 0.08 * a
    framed = framed.resize((int(framed.width * s), int(framed.height * s)), Image.LANCZOS)
    paste_center(img, framed, W / 2, 330 + art_box[1] / 2)
    ytxt = 330 + art_box[1] + 90
    label(img, title, ytxt, size=60, kind='serif', fg=CREAM, bg=None, maxw=900, pad=(0, 0))
    label(img, sub, ytxt + 105, size=36, kind='sans', fg=(236, 214, 226), bg=None, maxw=900, pad=(0, 0))
    label(img, price, ytxt + 205, size=46, kind='sans_bold', fg=PLUM, bg=YELLOW, pad=(40, 16), radius=40)
    label(img, 'payhip.com/ekavibes  ·  EKA L.', ytxt + 300, size=32, kind='sans_bold', fg=CREAM, bg=None, pad=(0, 0))
    if a < 1:
        img = Image.blend(Image.new('RGBA', (W, H), PLUM + (255,)), img, a)
    return img

# ------------------------------------------------------------------ audio helpers
def track_info(name, guess):
    key = [k for k in ANALYSIS if name in k][0]
    beats = ANALYSIS[key]['beats']
    start = min(beats, key=lambda b: abs(b - guess))
    return f'{UP}/{key}', start, [b - start for b in beats if b >= start], ANALYSIS[key]['tempo']

# ------------------------------------------------------------------ reels
def reel_look_closer(art, focus, hook, title, sub, dur=9.0, z0=2.0):
    src = load(art)
    full = (src.width / 2, src.height / 2)
    def frame(t):
        p = ease(min(t / 6.2, 1.0))
        zoom = z0 + (1.0 - z0) * p
        cx = focus[0] + (full[0] - focus[0]) * p; cy = focus[1] + (full[1] - focus[1]) * p
        img = cover_crop(src, cx, cy, zoom).convert('RGBA')
        if t < 3.2:
            a = 1.0 if t < 2.8 else 1 - (t - 2.8) / 0.4
            label(img, hook, 300, size=70, alpha=a)
        if t >= dur - 2.6:
            end_band(img, title, sub, ease_out((t - (dur - 2.6)) / 0.3))
        return img
    return frame, dur

def reel_pick_one(prints, triptych, hook, title, sub, beats):
    b = beats; per = 4
    cuts = [b[0], b[per], b[2 * per], b[3 * per]]
    dur = b[3 * per + 8] + 0.02
    srcs = [load(p) for p in prints]; tri = load(triptych).convert('RGBA')
    def frame(t):
        i = sum(1 for c in cuts[1:] if t >= c)
        if i < 3:
            loc = (t - cuts[i]) / (cuts[i + 1] - cuts[i])
            s = srcs[i]
            img = cover_crop(s, s.width / 2, s.height / 2, 1.0 + 0.08 * loc).convert('RGBA')
            pop = ease_out(loc * 4)
            r = int(92 * (0.6 + 0.4 * pop))
            d = ImageDraw.Draw(img)
            d.ellipse((150 - r, 520 - r, 150 + r, 520 + r), fill=CREAM)
            d.text((150, 522), str(i + 1), font=font('serif_bold', int(110 * (0.6 + 0.4 * pop))), fill=PLUM, anchor='mm')
        else:
            loc = t - cuts[3]
            img = Image.new('RGBA', (W, H), PLUM + (255,))
            el = tri.resize((1000, 500), Image.LANCZOS)
            paste_center(img, shadowed(el, opacity=160), 540, 860)
            d = ImageDraw.Draw(img)
            for k, x in enumerate((540 - 333, 540, 540 + 333)):
                pk = ease_out((loc - 0.12 * k) / 0.25)
                if pk <= 0: continue
                r = 56 * pk
                d.ellipse((x - r, 1200 - r, x + r, 1200 + r), fill=CREAM)
                d.text((x, 1202), str(k + 1), font=font('serif_bold', max(8, int(70 * pk))), fill=PLUM, anchor='mm')
            if loc > 0.9:
                end_band(img, title, sub, ease_out((loc - 0.9) / 0.3)) if False else None
                label(img, title, 1390, size=44, kind='serif', alpha=ease_out((loc - 0.9) / 0.3), pad=(32, 16))
                label(img, sub, 1480, size=32, kind='sans_bold', fg=PLUM, bg=YELLOW, alpha=ease_out((loc - 0.9) / 0.3), pad=(26, 12), radius=22)
        label(img, hook, 290, size=62, maxw=940)
        return img
    return frame, dur

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
ART = ['Lilac Swan', 'Sunlit Lullaby', 'Monarch Gaze', 'Pearl & Unicorn', 'Lotus Seraph', 'Songbird Mask', 'Wolf Sister', 'Gilded Rain', 'Small World Keeper', 'Horned Tea Ritual', 'Tea for the Dragon', 'Ginger & the Pup']

def reel_birth_month(beats, hook="Find your birth month's artwork", per=2, names=True):
    b = beats
    cover_end = b[3]
    starts = [b[3 + per * k] for k in range(12)]
    end_t = b[3 + 12 * per]
    dur = end_t + 2.8
    pages = [load('01_2027-Art-Calendar/Calendar_Wall-Letter_00-Cover.jpg')] + \
            [load(f'01_2027-Art-Calendar/Calendar_Wall-Letter_{m:02d}-{MONTHS[m-1]}.jpg') for m in range(1, 13)]
    bg_cache = {}
    def bg_for(i):
        if i not in bg_cache:
            small = pages[i].resize((54, 96)).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
            bg_cache[i] = Image.blend(small, Image.new('RGB', (W, H), PLUM), 0.55).convert('RGBA')
        return bg_cache[i]
    def page_frame(i, local):
        img = bg_for(i).copy()
        s = 1.0 + 0.05 * (1 - ease_out(local / 0.22))
        pw = int(900 * s); ph = int(pw * 1400 / 1082)
        el = pages[i].resize((pw, ph), Image.LANCZOS).convert('RGBA')
        paste_center(img, shadowed(el, blur=20, opacity=150), 540, 1010)
        return img
    def frame(t):
        if t < cover_end:
            img = page_frame(0, 1.0)
            label(img, hook, 250, size=64)
            return img
        if t < end_t:
            i = sum(1 for s in starts if t >= s)
            img = page_frame(i, t - starts[i - 1])
            label(img, MONTHS[i - 1], 220, size=84, kind='serif_bold', pad=(48, 18))
            if names: label(img, ART[i - 1], 330, size=40, kind='serif_it', fg=CREAM, bg=None, pad=(0, 0))
            return img
        return end_card(t - end_t, pages[0], 'The 2027 Art Calendar', '12 artworks · wall + desk · 36 phone wallpapers', 'Printable · $14')
    return frame, dur

def phone(screen_img, clock=True, date='Monday, January 4'):
    sw, sh = 520, 1127
    scr = screen_img.resize((sw, sh), Image.LANCZOS).convert('RGBA')
    if clock:
        d = ImageDraw.Draw(scr)
        d.text((sw / 2, 120), date, font=font('sans_bold', 24), fill=(255, 255, 255, 235), anchor='mm')
        d.text((sw / 2, 205), '9:41', font=font('sans_bold', 118), fill=(255, 255, 255, 245), anchor='mm')
    mask = Image.new('L', (sw, sh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=64, fill=255)
    bez = 18
    body = Image.new('RGBA', (sw + 2 * bez, sh + 2 * bez), (0, 0, 0, 0))
    ImageDraw.Draw(body).rounded_rectangle((0, 0, body.width - 1, body.height - 1), radius=80, fill=(16, 12, 16, 255))
    body.paste(scr, (bez, bez), mask)
    ImageDraw.Draw(body).rounded_rectangle((body.width / 2 - 62, bez + 18, body.width / 2 + 62, bez + 52), radius=17, fill=(0, 0, 0, 255))
    return shadowed(body, blur=26, off=(0, 22), opacity=170)

def reel_lockscreen(beats, before='Your lock screen, before…', after='Free 2027 lock screens', order=(0, 1, 2, 3, 4, 5)):
    b = beats
    walls = ['02_Phone-Wallpapers/Wallpaper_dated_01-January.jpg', '02_Phone-Wallpapers/Wallpaper_art-only_GildedRain.jpg',
             '02_Phone-Wallpapers/Wallpaper_dated_04-April.jpg', '02_Phone-Wallpapers/Wallpaper_art-only_GingerAndThePup.jpg',
             '02_Phone-Wallpapers/Wallpaper_dated_07-July.jpg', '02_Phone-Wallpapers/Wallpaper_dated_10-October.jpg']
    dates = ['Monday, January 4', 'Monday, March 1', 'Monday, April 5', 'Monday, December 6', 'Monday, July 5', 'Monday, October 4']
    walls = [walls[k] for k in order]; dates = [dates[k] for k in order]
    srcs = [load(w) for w in walls]
    DATES = {-1: 'Monday, January 4'}; DATES.update({k: d for k, d in enumerate(dates)})
    g = Image.linear_gradient('L').resize((645, 1398))
    plain = Image.merge('RGB', [g.point(lambda v: 70 + v // 6), g.point(lambda v: 78 + v // 6), g.point(lambda v: 92 + v // 5)])
    starts = [b[2]] + [b[2 + 3 * k] for k in range(1, 6)]
    end_t = b[2 + 18]; dur = end_t + 2.8
    cache = {}
    def scene(i):
        if i not in cache:
            src = plain if i < 0 else srcs[i]
            bg = src.resize((40, 87)).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
            bg = Image.blend(bg, Image.new('RGB', (W, H), PLUM), 0.35).convert('RGBA')
            cache[i] = (bg, phone(src, date=DATES[i]))
        return cache[i]
    def frame(t):
        if t >= end_t:
            return end_card(t - end_t, srcs[0], '2027 phone wallpapers', '36 lock screens · dated + art-only', 'Free download', art_box=(420, 760))
        i = sum(1 for s in starts if t >= s) - 1
        bg, ph = scene(i)
        img = bg.copy()
        local = t - (starts[i] if i >= 0 else 0)
        s = 1.0 + (0.035 * (1 - ease_out(local / 0.25)) if i >= 0 else 0)
        p = ph if s == 1.0 else ph.resize((int(ph.width * s), int(ph.height * s)), Image.BILINEAR)
        paste_center(img, p, 540, 1030)
        label(img, before if i < 0 else after, 250, size=66)
        return img
    return frame, dur

def reel_journal(beats, hook='Junk journalers bored of beige?', paper='EkaL_Paper_13_Soft.jpg', flip=False, step=1, sheets=None, sheet_hook='16 sheets of colour'):
    b = beats[::step]
    E = f'{ROOT}/03_Junk-Journal-Kit/transparent-PNG-elements/'
    items = [  # file, cx, cy, width, rotation
        ('EkaL_Card-3x4_01.png', 300, 690, 360, -6), ('EkaL_FussyCut_01_fox_circle.png', 770, 610, 300, 8),
        ('EkaL_Ticket_01_MIDNIGHT-MASQUERADE.png', 650, 940, 520, -3), ('EkaL_Stamp_01_freckles.png', 250, 1120, 200, -9),
        ('EkaL_FussyCut_17_golden-nap_heart.png', 560, 1220, 270, 6), ('EkaL_Tag_05_marmoset.png', 880, 1210, 170, 11),
        ('EkaL_Postmark_1.png', 700, 820, 300, 0), ('EkaL_FussyCut_13_unicorn_circle.png', 210, 1390, 210, -10),
        ('EkaL_Stamp_11_songbird-eyes.png', 820, 1420, 180, 7), ('EkaL_Ticket_04_DAYDREAM-THEATRE.png', 520, 1460, 420, 3)]
    if flip:
        items = [(fn, 1080 - cx, cy, w, -rot) for fn, cx, cy, w, rot in items[::-1]]
        items = [(it[0].replace('Card-3x4_01', 'Card-3x4_02').replace('FussyCut_01_fox_circle', 'FussyCut_04_tiger_scallop').replace('Tag_05_marmoset', 'Tag_01_wolf').replace('FussyCut_13_unicorn_circle', 'FussyCut_07_pomegranate_circle'),) + it[1:] for it in items]
    els = []
    for fn, cx, cy, w, rot in items:
        e = load(E + fn, 'RGBA'); e = e.resize((w, int(e.height * w / e.width)), Image.LANCZOS).rotate(rot, expand=True, resample=Image.BICUBIC)
        els.append((shadowed(e, blur=10, off=(4, 10), opacity=120), cx, cy))
    bg = cover_crop(load('03_Junk-Journal-Kit/background-paper-samples/' + paper), 541, 700, 1.0).convert('RGBA')
    drops = [b[k] - 0.12 for k in range(10)]
    sheets = sheets or ['03_Junk-Journal-Kit/Kit_Sheet_05-Fussy-cuts.jpg', '03_Junk-Journal-Kit/Kit_Sheet_07-Stamps.jpg',
              '03_Junk-Journal-Kit/Kit_Sheet_11-Tickets.jpg', '03_Junk-Journal-Kit/Kit_Sheet_09-Tags.jpg']
    sh_start = b[11]; sh_t = [b[11 + k] for k in range(4)]; end_t = b[15]; dur = end_t + 2.8
    base_cache = {}
    def base_with(n):
        if n not in base_cache:
            img = bg.copy()
            for e, cx, cy in els[:n]: paste_center(img, e, cx, cy)
            base_cache[n] = img
        return base_cache[n]
    def frame(t):
        if t >= end_t:
            return end_card(t - end_t, load('03_Junk-Journal-Kit/Kit_Sheet_05-Fussy-cuts.jpg'), 'Junk journal kit',
                            'Kindred Curiosities · 16 sheets · 15 papers · 127 PNGs', 'Printable · $12')
        if t >= sh_start:
            i = min(3, sum(1 for s in sh_t if t >= s) - 1)
            img = Image.new('RGBA', (W, H), PLUM + (255,))
            local = t - sh_t[i]
            el = load(sheets[i]).resize((860, int(860 * 1400 / 1082)), Image.LANCZOS).convert('RGBA')
            rot = (-4, 3, -2, 4)[i] * (1 - ease_out(local / 0.25)) + (-1, 1, -1, 1)[i]
            el = el.rotate(rot, expand=True, resample=Image.BICUBIC)
            paste_center(img, shadowed(el, blur=18, opacity=150), 540 + 60 * (1 - ease_out(local / 0.2)), 1000)
            label(img, sheet_hook, 250, size=64)
            return img
        n_done = sum(1 for d in drops if t >= d + 0.2)
        img = base_with(n_done).copy()
        for k, dt in enumerate(drops):
            if dt <= t < dt + 0.2:
                p = ease_out((t - dt) / 0.2)
                e, cx, cy = els[k]
                s = 1.3 - 0.3 * p
                ee = e.resize((int(e.width * s), int(e.height * s)), Image.BILINEAR)
                if p < 1:
                    a = ee.split()[3].point(lambda v: int(v * min(1, p * 1.6))); ee.putalpha(a)
                paste_center(img, ee, cx, cy - 70 * (1 - p))
        label(img, hook, 250, size=64)
        return img
    return frame, dur


SETS = [('Kindred', '04_Gallery-Set_Kindred/Kindred_set-of-3_side-by-side.jpg'),
        ('Masquerade', '05_Gallery-Set_Masquerade/Masquerade_set-of-3_side-by-side.jpg'),
        ('Reverie', '06_Gallery-Set_Reverie/Reverie_set-of-3_side-by-side.jpg')]

def reel_pick_set(beats, hook='Pick your gallery wall: 1, 2 or 3?'):
    b = beats; per = 4
    cuts = [b[0], b[per], b[2 * per], b[3 * per]]
    dur = b[3 * per + 8] + 0.02
    srcs = [load(f) for _, f in SETS]
    bgs = [Image.blend(s.resize((48, 24)).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR), Image.new('RGB', (W, H), PLUM), 0.5).convert('RGBA') for s in srcs]
    def frame(t):
        i = sum(1 for c in cuts[1:] if t >= c)
        if i < 3:
            loc = (t - cuts[i]) / (cuts[i + 1] - cuts[i])
            img = bgs[i].copy()
            w = int(1040 * (1.0 + 0.04 * loc)); el = srcs[i].resize((w, w // 2), Image.LANCZOS).convert('RGBA')
            paste_center(img, shadowed(el, opacity=160), 540, 960)
            pop = ease_out(loc * 4); r = int(80 * (0.6 + 0.4 * pop)); d = ImageDraw.Draw(img)
            d.ellipse((540 - r, 1360 - r, 540 + r, 1360 + r), fill=CREAM)
            d.text((540, 1362), str(i + 1), font=font('serif_bold', int(96 * (0.6 + 0.4 * pop))), fill=PLUM, anchor='mm')
            label(img, SETS[i][0], 640, size=56, kind='serif_it', fg=CREAM, bg=None, pad=(0, 0))
        else:
            loc = t - cuts[3]
            img = Image.new('RGBA', (W, H), PLUM + (255,)); d = ImageDraw.Draw(img)
            for k in range(3):
                pk = ease_out((loc - 0.12 * k) / 0.25)
                if pk <= 0: continue
                el = srcs[k].resize((820, 410), Image.LANCZOS).convert('RGBA')
                y = 640 + k * 450
                paste_center(img, shadowed(el, opacity=150), 600, y)
                r = 46 * pk
                d.ellipse((95 - r, y - r, 95 + r, y + r), fill=CREAM)
                d.text((95, y + 2), str(k + 1), font=font('serif_bold', max(8, int(58 * pk))), fill=PLUM, anchor='mm')
            if loc > 0.9:
                label(img, 'Each set $12 · all 9 prints $29', 1640, size=36, kind='sans_bold', fg=PLUM, bg=YELLOW, alpha=ease_out((loc - 0.9) / 0.3), pad=(28, 14), radius=24)
        label(img, hook, 290, size=60, maxw=940)
        return img
    return frame, dur

BUNDLE = ['04_Gallery-Set_Kindred/Kindred_1-FoxAndFreckles_print-2x3.jpg', '04_Gallery-Set_Kindred/Kindred_2-WolfSister_print-2x3.jpg', '04_Gallery-Set_Kindred/Kindred_3-LilacSwan_print-2x3.jpg',
          '05_Gallery-Set_Masquerade/Masquerade_1-GildedRain_print-2x3.jpg', '05_Gallery-Set_Masquerade/Masquerade_2-SongbirdMask_print-2x3.jpg', '05_Gallery-Set_Masquerade/Masquerade_3-CheckmateCarnival_print-2x3.jpg',
          '06_Gallery-Set_Reverie/Reverie_1-HornedTeaRitual_print-2x3.jpg', '06_Gallery-Set_Reverie/Reverie_2-LotusSeraph_print-2x3.jpg', '06_Gallery-Set_Reverie/Reverie_3-SmallWorldKeeper_print-2x3.jpg']

def reel_bundle(beats, hook='Nine prints. Endless personality.'):
    b = beats
    pops = [b[k] for k in range(9)]
    end_t = b[9 + 4]; dur = end_t + 2.8
    tw, th = 260, 390
    tiles = [load(f).resize((tw, th), Image.LANCZOS).convert('RGBA') for f in BUNDLE]
    tiles = [shadowed(t, blur=10, off=(0, 8), opacity=130) for t in tiles]
    bg = Image.new('RGBA', (W, H), PLUM + (255,))
    def frame(t):
        if t >= end_t:
            return end_card(t - end_t, load('07_Gallery-Bundle_All-3-Sets/Bundle_overview_9-prints.jpg'), 'The gallery wall bundle', 'Kindred + Masquerade + Reverie · 9 prints', 'Printable · $29', art_box=(760, 700))
        img = bg.copy()
        for k, pt in enumerate(pops):
            if t < pt - 0.05: continue
            p = ease_out((t - pt + 0.05) / 0.2)
            cx = 540 + (k % 3 - 1) * 290; cy = 1010 + (k // 3 - 1) * 420
            el = tiles[k]
            if p < 1:
                s_ = 0.7 + 0.3 * p; el = el.resize((int(el.width * s_), int(el.height * s_)), Image.BILINEAR)
            paste_center(img, el, cx, cy)
        zoom_t = pops[-1] + 0.4
        if t > zoom_t:
            z = 1 + 0.05 * ease((t - zoom_t) / (end_t - zoom_t))
            img = img.resize((int(W * z), int(H * z)), Image.BILINEAR).crop((int((W * z - W) / 2), int((H * z - H) / 2), int((W * z - W) / 2) + W, int((H * z - H) / 2) + H))
        label(img, hook, 250, size=64)
        return img
    return frame, dur

# ------------------------------------------------------------------ registry

B2 = {
 'b2-01_look-closer_wolf': ('lc', 'Wild_colour', 79.9, dict(art='04_Gallery-Set_Kindred/Kindred_2-WolfSister_print-2x3.jpg', focus=(250, 560), hook='Someone’s watching.\nZoom out.', title='Wolf Sister · Kindred set of 3', z0=2.3)),
 'b2-02_look-closer_swan': ('lc', 'River_of_Light', 9.6, dict(art='04_Gallery-Set_Kindred/Kindred_3-LilacSwan_print-2x3.jpg', focus=(650, 580), hook='This swan has company.\nZoom out.', title='Lilac Swan · Kindred set of 3', z0=2.3)),
 'b2-03_look-closer_gilded': ('lc', 'Carnival', 116.7, dict(art='05_Gallery-Set_Masquerade/Masquerade_1-GildedRain_print-2x3.jpg', focus=(540, 930), hook='Red lips. Gold rain.\nNow the whole face.', title='Gilded Rain · Masquerade set of 3', z0=2.2)),
 'b2-04_look-closer_songbird': ('lc', 'Moon_on_the_Drum.wav', 16.0, dict(art='05_Gallery-Set_Masquerade/Masquerade_2-SongbirdMask_print-2x3.jpg', focus=(880, 1000), hook='Follow the little bird.\nZoom out.', title='Songbird Mask · Masquerade set of 3', z0=2.3)),
 'b2-05_look-closer_checkmate': ('lc', 'Canopy_Runner', 64.4, dict(art='05_Gallery-Set_Masquerade/Masquerade_3-CheckmateCarnival_print-2x3.jpg', focus=(400, 1040), hook='Who’s winning?\nZoom out.', title='Checkmate Carnival · Masquerade set of 3', z0=2.2)),
 'b2-06_look-closer_horned-tea': ('lc', 'Tea_by_the_Window', 120.0, dict(art='06_Gallery-Set_Reverie/Reverie_1-HornedTeaRitual_print-2x3.jpg', focus=(420, 960), hook='Tea time, but make it\nmagic. Zoom out.', title='Horned Tea Ritual · Reverie set of 3', z0=2.2)),
 'b2-07_look-closer_small-world': ('lc', 'Threshold_of_New_Light', 119.5, dict(art='06_Gallery-Set_Reverie/Reverie_3-SmallWorldKeeper_print-2x3.jpg', focus=(560, 1000), hook='She is holding a whole\nworld. Zoom out.', title='Small World Keeper · Reverie set of 3', z0=2.2)),
 'b2-08_pick-one_kindred': ('po', 'Canopy_Runner', 203.0, dict(prints=[f'04_Gallery-Set_Kindred/Kindred_{n}_print-2x3.jpg' for n in ('1-FoxAndFreckles', '2-WolfSister', '3-LilacSwan')], tri='04_Gallery-Set_Kindred/Kindred_set-of-3_side-by-side.jpg', hook='Fox, wolf or swan?', title='Kindred · set of 3 prints')),
 'b2-09_pick-one_reverie': ('po', 'Reverie', 36.5, dict(prints=[f'06_Gallery-Set_Reverie/Reverie_{n}_print-2x3.jpg' for n in ('1-HornedTeaRitual', '2-LotusSeraph', '3-SmallWorldKeeper')], tri='06_Gallery-Set_Reverie/Reverie_set-of-3_side-by-side.jpg', hook='Which dream would you hang?', title='Reverie · set of 3 prints')),
 'b2-10_pick-your-set': ('ps', 'Moon_on_the_Drum.wav', 104.0, dict()),
 'b2-11_calendar_birthday': ('bm', 'New_year', 112.0, dict(hook="What's your birthday month's artwork?")),
 'b2-12_calendar_12-in-12': ('bm', 'Golden_Medal', 85.0, dict(hook='12 months. 12 artworks.', per=1, names=False)),
 'b2-13_calendar_month-vibe': ('bm', 'Threshold_of_New_Light', 181.0, dict(hook='Which month is your vibe?')),
 'b2-14_lockscreen_pov': ('ls', 'Clockwork_Butterfly', 100.0, dict(before='POV: your lock screen\nin 2027', after='Free · 36 wallpapers', order=(2, 0, 4, 1, 5, 3))),
 'b2-15_lockscreen_which': ('ls', 'Wild_colour', 8.0, dict(before='Your phone deserves\nbetter art', after='Which one are you?', order=(1, 3, 0, 5, 2, 4))),
 'b2-16_journal_127-pngs': ('jj', 'Tea_by_the_Window', 59.5, dict(hook='127 PNGs. Zero beige.', paper='EkaL_Paper_15_Soft.jpg', flip=True, sheets=['03_Junk-Journal-Kit/Kit_Sheet_06-Fussy-cuts-2.jpg', '03_Junk-Journal-Kit/Kit_Sheet_08-Stamps-postmarks.jpg', '03_Junk-Journal-Kit/Kit_Sheet_10-Tags-2.jpg', '03_Junk-Journal-Kit/Kit_Sheet_12-Cards-3x4.jpg'], sheet_hook='Print. Cut. Create.')),
 'b2-17_journal_tiny-pieces': ('jj', 'River_of_Light', 63.0, dict(hook='Tiny pieces.\nBig imagination.', step=2, sheets=['03_Junk-Journal-Kit/Kit_Sheet_03-Bottle-cap-circles.jpg', '03_Junk-Journal-Kit/Kit_Sheet_04-Inchies.jpg', '03_Junk-Journal-Kit/Kit_Sheet_14-Cards-6x4.jpg', '03_Junk-Journal-Kit/Kit_Sheet_13-Cards-3x4-2.jpg'], sheet_hook='15 papers · 127 PNGs')),
 'b2-18_bundle_nine-prints': ('bd', 'Clockwork_Butterfly', 130.0, dict()),
}
SUBS = {'lc': 'Printable art · payhip.com/ekavibes'}

def build_b2(rid):
    kind, tr, guess, kw = B2[rid]
    a, s, beats, _ = track_info(tr, guess)
    if kind == 'lc':
        fr, dur = reel_look_closer(kw['art'], kw['focus'], kw['hook'], kw['title'], SUBS['lc'], z0=kw['z0'])
    elif kind == 'po':
        fr, dur = reel_pick_one(kw['prints'], kw['tri'], kw['hook'], kw['title'], 'Printable · $12 · payhip.com/ekavibes', beats)
    elif kind == 'ps':
        fr, dur = reel_pick_set(beats)
    elif kind == 'bm':
        fr, dur = reel_birth_month(beats, **kw)
    elif kind == 'ls':
        fr, dur = reel_lockscreen(beats, **kw)
    elif kind == 'jj':
        fr, dur = reel_journal(beats, **kw)
    elif kind == 'bd':
        fr, dur = reel_bundle(beats)
    return fr, dur, a, s

def build(rid):
    if rid in B2: return build_b2(rid)
    if rid == '01_look-closer_fox':
        a, s, beats, _ = track_info('Wild_colour', 7.9)
        fr, dur = reel_look_closer('04_Gallery-Set_Kindred/Kindred_1-FoxAndFreckles_print-2x3.jpg', (430, 1080),
                                   'This fox has a best\nfriend. Zoom out.', 'Fox & Freckles · Kindred set of 3', 'Printable art · payhip.com/ekavibes', z0=2.4)
    elif rid == '02_pick-one_masquerade':
        a, s, beats, _ = track_info('Carnival', 25.5)
        fr, dur = reel_pick_one([f'05_Gallery-Set_Masquerade/Masquerade_{n}_print-2x3.jpg' for n in ('1-GildedRain', '2-SongbirdMask', '3-CheckmateCarnival')],
                                '05_Gallery-Set_Masquerade/Masquerade_set-of-3_side-by-side.jpg',
                                'Which one goes on your wall?', 'Masquerade · set of 3 prints', 'Printable · $12 · payhip.com/ekavibes', beats)
    elif rid == '03_birth-month_calendar':
        a, s, beats, _ = track_info('New_year', 10.8)
        fr, dur = reel_birth_month(beats)
    elif rid == '04_lockscreen_free':
        tr = os.environ.get('TRACK', 'Catwalk:109.9').split(':')
        a, s, beats, _ = track_info(tr[0], float(tr[1]))
        fr, dur = reel_lockscreen(beats)
    elif rid == '05_journal_kit':
        a, s, beats, _ = track_info('Golden_Medal', 21.5)
        fr, dur = reel_journal(beats)
    elif rid == '06_look-closer_lotus':
        a, s, beats, _ = track_info('Reverie', 5.6)
        fr, dur = reel_look_closer('06_Gallery-Set_Reverie/Reverie_2-LotusSeraph_print-2x3.jpg', (860, 1030),
                                   'This owl is guarding\nsomeone. Zoom out.', 'Lotus Seraph · Reverie set of 3', 'Printable art · payhip.com/ekavibes', z0=2.2)
    return fr, dur, a, s

def render(rid, preview_times=None):
    fr, dur, audio, start = build(rid)
    os.makedirs(OUT, exist_ok=True)
    if preview_times:
        for t in preview_times:
            fr(min(t, dur - 0.01)).convert('RGB').save(f'{OUT}/{rid}_t{t:05.2f}.jpg', quality=85)
        print(rid, 'dur', round(dur, 2)); return
    n = int(round(dur * FPS)); fade = 0.5
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', audio,
           '-filter_complex', f'[1:a]afade=t=in:d=0.02,afade=t=out:st={dur - fade:.3f}:d={fade},loudnorm=I=-14:TP=-1.5:LRA=11[a]',
           '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-shortest', f'{OUT}/{rid}{os.environ.get("SUFFIX", "")}.mp4']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n):
        p.stdin.write(fr(k / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    print(rid, 'done', round(dur, 2), 's', audio, round(start,2))

if __name__ == '__main__':
    rid = sys.argv[1]
    pts = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    render(rid, pts)
