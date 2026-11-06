"""Stillglass pin composer.

Usage:
  python3 -I compose.py <type> <book> <input_image|-> <headline> <out.png> [--kicker TEXT]
  python3 -I compose.py VERSE <book> <input_image> "<KJV verse>" "<Reference>" <out.png>

type   : SPLIT | GIFT | COZY | SET | PEEK
book   : CC | CW | SG | ALL
input  : GPT image (SPLIT/GIFT/COZY/SET) or a comma-separated list of 4 page PNGs (PEEK)
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = lambda name, size: ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
W, H = 1000, 1500
BAND = 300
NAVY = (15, 20, 40)
GOLD = (233, 185, 58)
GOLD_SOFT = (214, 186, 120)
CREAM = (246, 241, 232)
COVERS = {b: os.path.join(HERE, "assets", f"{b}_cover.png") for b in ("CC", "CW", "SG")}
BOOK_NAMES = {"CC": "CATHEDRAL CREATURES", "CW": "CHURCH WINDOWS", "SG": "SACRED GLASS", "ALL": "THE STILLGLASS COLLECTION"}


def cover_fill(im, w, h, anchor_y=0.5):
    """Scale to cover w x h, crop centred (vertical anchor adjustable)."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * anchor_y)
    return im.crop((x, y, x + w, y + h))


def trim_white(im, thresh=245):
    g = im.convert("L").point(lambda v: 255 if v < thresh else 0)
    box = g.getbbox()
    return im.crop(box) if box else im


def fit_text(draw, text, font_name, max_w, max_lines, start, minimum):
    """Largest size where text fits in <= max_lines lines; two-line splits are balanced."""
    words = text.split()
    for size in range(start, minimum - 1, -2):
        f = FONT(font_name, size)
        if draw.textlength(text, font=f) <= max_w:
            return f, [text]
        if max_lines >= 2 and len(words) > 1:
            best = min(range(1, len(words)), key=lambda k: max(draw.textlength(" ".join(words[:k]), font=f), draw.textlength(" ".join(words[k:]), font=f)))
            lines = [" ".join(words[:best]), " ".join(words[best:])]
            if all(draw.textlength(l, font=f) <= max_w for l in lines):
                return f, lines
    return FONT(font_name, minimum), [text]


def shadow(canvas, im, xy, radius=18, offset=(0, 10), opacity=110):
    mask = Image.new("L", (im.width + radius * 4, im.height + radius * 4), 0)
    ImageDraw.Draw(mask).rectangle((radius * 2, radius * 2, radius * 2 + im.width, radius * 2 + im.height), fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(radius))
    blk = Image.new("RGB", mask.size, (0, 0, 0))
    canvas.paste(blk, (xy[0] - radius * 2 + offset[0], xy[1] - radius * 2 + offset[1]), mask)
    canvas.paste(im, xy)


def band(canvas, headline, kicker):
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, 0, W, BAND), fill=NAVY)
    d.rectangle((0, BAND - 6, W, BAND), fill=GOLD)
    d.line((40, BAND - 16, W - 40, BAND - 16), fill=GOLD_SOFT, width=1)
    kf = FONT("cinzel-latin-600-normal.ttf", 24)
    kw = d.textlength(kicker, font=kf)
    d.text(((W - kw) / 2, 38), kicker, font=kf, fill=GOLD_SOFT)
    f, lines = fit_text(d, headline, "eb-garamond-latin-700-normal.ttf", W - 110, 2, 86, 52)
    lh = f.size * 1.08
    total = lh * len(lines)
    y = 80 + (BAND - 30 - 80 - total) / 2
    for l in lines:
        lw = d.textlength(l, font=f)
        d.text(((W - lw) / 2, y), l, font=f, fill=GOLD)
        y += lh


def badge(canvas, book, label="Paperback on Amazon", bw=236):
    cov = Image.open(COVERS[book]).convert("RGB")
    cov = cov.resize((bw, round(cov.height * bw / cov.width)), Image.LANCZOS)
    cov = ImageOps.expand(cov, border=3, fill=GOLD)
    x, y = W - cov.width - 44, H - cov.height - 92
    shadow(canvas, cov, (x, y))
    d = ImageDraw.Draw(canvas)
    f = FONT("cinzel-latin-700-normal.ttf", 20)
    tw = d.textlength(label, font=f)
    px, py = x + cov.width / 2 - tw / 2 - 18, y + cov.height + 18
    d.rounded_rectangle((px, py, px + tw + 36, py + 42), radius=21, fill=NAVY, outline=GOLD, width=2)
    d.text((px + 18, py + 9), label, font=f, fill=GOLD)


def make(ptype, book, src, headline, out, kicker=None):
    kicker = kicker or BOOK_NAMES[book] + (" · COLORING BOOK" if book != "ALL" else "")
    canvas = Image.new("RGB", (W, H), CREAM)
    body_h = H - BAND
    if ptype == "SPLIT":
        page = trim_white(Image.open(src).convert("RGB"))
        canvas.paste((255, 255, 255), (0, BAND, W, H))
        s = min((W - 70) / page.width, (body_h - 50) / page.height)
        page = page.resize((round(page.width * s), round(page.height * s)), Image.LANCZOS)
        canvas.paste(page, ((W - page.width) // 2, BAND + 25 + (body_h - 50 - page.height) // 2))
    elif ptype in ("GIFT", "COZY"):
        img = cover_fill(Image.open(src).convert("RGB"), W, H)
        canvas.paste(img.crop((0, BAND, W, H)), (0, BAND))
    elif ptype == "SET":
        img = cover_fill(Image.open(src).convert("RGB"), W, H)
        canvas.paste(img.crop((0, BAND, W, H)), (0, BAND))
        cw = 300
        for i, b in enumerate(("CW", "CC", "SG")):
            cov = Image.open(COVERS[b]).convert("RGB")
            w = cw + (40 if i == 1 else 0)
            cov = cov.resize((w, round(cov.height * w / cov.width)), Image.LANCZOS)
            cov = ImageOps.expand(cov, border=2, fill=GOLD)
            x = [40, (W - cov.width) // 2, W - cov.width - 40][i]
            y = BAND + (body_h - cov.height) // 2 + (0 if i == 1 else 40)
            if i == 1:
                continue
            shadow(canvas, cov, (x, y), radius=22, offset=(0, 14), opacity=140)
        b = "CC"
        cov = Image.open(COVERS[b]).convert("RGB")
        cov = cov.resize((cw + 40, round(cov.height * (cw + 40) / cov.width)), Image.LANCZOS)
        cov = ImageOps.expand(cov, border=2, fill=GOLD)
        shadow(canvas, cov, ((W - cov.width) // 2, BAND + (body_h - cov.height) // 2 - 10), radius=24, offset=(0, 16), opacity=160)
    elif ptype == "PEEK":
        pages = [trim_white(Image.open(p).convert("RGB")) for p in src.split(",")][:4]
        gap, m = 22, 40
        cw_, ch_ = (W - 2 * m - gap) // 2, (body_h - 2 * m - gap - 120) // 2
        for i, pg in enumerate(pages):
            s = min(cw_ / pg.width, ch_ / pg.height)
            pg = pg.resize((round(pg.width * s), round(pg.height * s)), Image.LANCZOS)
            card = Image.new("RGB", (cw_, ch_), "white")
            card.paste(pg, ((cw_ - pg.width) // 2, (ch_ - pg.height) // 2))
            x = m + (i % 2) * (cw_ + gap)
            y = BAND + m + (i // 2) * (ch_ + gap)
            shadow(canvas, card, (x, y), radius=10, offset=(0, 6), opacity=70)
    else:
        raise SystemExit("unknown type " + ptype)
    band(canvas, headline, kicker)
    if ptype != "SET" and book in COVERS:
        badge(canvas, book, bw=200 if ptype in ("SPLIT", "PEEK") else 236)
    canvas.save(out, optimize=True)
    return out


def make_verse(book, src, verse, ref, out):
    """Light 'verse' layout: no navy band; KJV verse in italic over the art, real cover badge."""
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    top = 250
    f, lines = fit_text(d, "\u201c" + verse + "\u201d", "eb-garamond-latin-500-italic.ttf", W - 120, 2, 64, 40)
    lh = f.size * 1.12
    y = 46 + (150 - lh * len(lines)) / 2
    for l in lines:
        lw = d.textlength(l, font=f)
        d.text(((W - lw) / 2, y), l, font=f, fill=NAVY)
        y += lh
    rf = FONT("cinzel-latin-600-normal.ttf", 24)
    rw = d.textlength(ref, font=rf)
    ry = y + 14
    d.line(((W - rw) / 2 - 70, ry + 14, (W - rw) / 2 - 18, ry + 14), fill=GOLD, width=2)
    d.line(((W + rw) / 2 + 18, ry + 14, (W + rw) / 2 + 70, ry + 14), fill=GOLD, width=2)
    d.text(((W - rw) / 2, ry), ref, font=rf, fill=(176, 132, 30))
    page = trim_white(Image.open(src).convert("RGB"))
    s = min((W - 60) / page.width, (H - top - 30) / page.height)
    page = page.resize((round(page.width * s), round(page.height * s)), Image.LANCZOS)
    canvas.paste(page, ((W - page.width) // 2, top + (H - top - 30 - page.height) // 2 + 10))
    badge(canvas, book, bw=190)
    canvas.save(out, optimize=True)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "VERSE":
        print(make_verse(a[1], a[2], a[3], a[4], a[5])); sys.exit()
    kick = None
    if "--kicker" in a:
        i = a.index("--kicker"); kick = a[i + 1]; a = a[:i] + a[i + 2:]
    print(make(a[0], a[1], a[2], a[3], a[4], kick))
