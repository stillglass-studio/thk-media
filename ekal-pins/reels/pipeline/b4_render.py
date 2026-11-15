"""Batch 4: holiday + new-year shorts from the Christmas / Start 2027 / Tiger kit pin sets.
Two formats:
  'pin'  single pin: whole pin readable first (its headline is the hook), then a slow push into the product, end card.
  'list' listicle: 3-6 pins, one per beat-snapped step, numbered, hook on the first item, end card.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from render import W, H, load, cover_crop, ease, ease_out, label, end_card, PLUM, CREAM
from PIL import Image, ImageFilter, ImageEnhance

N = '/home/claude/new3/'
XM = N + 'ee16c80f/'; ST = N + 'ed25e7cd/'; TG = N + '7a304b21/'
SOFT_EQ = 'highpass=f=60,lowshelf=f=180:g=-6,equalizer=f=900:t=q:w=1.2:g=3,'
SOFT = ('Full_Cup_Hymn', 'Enough_in_Gold', 'Tea_by_the_Window', 'Threshold_of_New_Light', 'Golden_Medal', 'River_of_Light', 'Wild_colour')
GOLD = (217, 169, 59)

_cache = {}
def staged(path, fitw=930):
    """Blurred, dimmed copy of the pin as background plus the pin fitted on top, as RGBA layers."""
    if path in _cache: return _cache[path]
    src = load(path)
    bg = ImageEnhance.Brightness(cover_crop(src, src.width / 2, src.height / 2, 1.0).filter(ImageFilter.GaussianBlur(45))).enhance(0.5).convert('RGBA')
    fit = src.copy().convert('RGBA'); fit = fit.resize((fitw, int(src.height * fitw / src.width)), Image.LANCZOS)
    fit = R.shadowed(fit, blur=20, off=(0, 14), opacity=150)
    _cache[path] = (src, bg, fit)
    return _cache[path]

def contained(path, s=1.0):
    src, bg, fit = staged(path)
    img = bg.copy()
    el = fit if abs(s - 1) < 1e-3 else fit.resize((int(fit.width * s), int(fit.height * s)), Image.BILINEAR)
    R.paste_center(img, el, W / 2, H / 2)
    return img

def reel_pin(pin, focus, line, title, sub, price, beats, z1=1.6):
    src, bg, _ = staged(pin); srcA = src.convert('RGBA')
    fw = 930; s0 = fw / src.width                      # pin scale when fully visible
    sEnd = max(W / src.width, H / src.height) * z1     # scale at the end of the push (fills the frame)
    tX = 1.4                                            # hold so the headline can be read
    tP = min(beats, key=lambda b: abs(b - 8.4))
    dur = tP + 3.2
    def frame(t):
        if t >= tP: return end_card(t - tP, src, title, sub, price)
        p = ease(min(max((t - tX) / (tP - tX), 0), 1))
        sc = s0 * (1.0 + 0.02 * min(t / tX, 1)) * (sEnd / s0) ** p
        # focus point drifts from its place on the fitted pin to the frame centre
        fx0 = W / 2 + (focus[0] - src.width / 2) * sc; fy0 = H / 2 + (focus[1] - src.height / 2) * sc
        fx = fx0 + (W / 2 - fx0) * p; fy = fy0 + (H / 2 - fy0) * p
        x0 = fx - focus[0] * sc; y0 = fy - focus[1] * sc
        img = bg.copy() if sc * src.width < W * 1.02 or sc * src.height < H * 1.02 else Image.new('RGBA', (W, H))
        # crop the needed region of the source before resizing (keeps it fast)
        cx0 = max(0, -x0 / sc); cy0 = max(0, -y0 / sc)
        cx1 = min(src.width, (W - x0) / sc); cy1 = min(src.height, (H - y0) / sc)
        crop = srcA.crop((int(cx0), int(cy0), int(cx1) + 1, int(cy1) + 1))
        el = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.BILINEAR)
        img.alpha_composite(el, (int(x0 + int(cx0) * sc), int(y0 + int(cy0) * sc)))
        if t > tX + 1.4 and line:
            label(img, line, 175, size=40, kind='sans_bold', fg=PLUM, bg=CREAM, alpha=ease_out((t - tX - 1.4) / 0.5), pad=(30, 16), radius=26)
        return img
    return frame, dur

def reel_list(items, hook, title, sub, price, end_art, beats, per=2.4):
    """items: [(pin_path, short label)]. Hook sits on item 1, numbers on the rest."""
    cuts = [0.0]
    for k in range(1, len(items) + 1):
        cuts.append(min(beats, key=lambda b: abs(b - k * per)))
    end_t = cuts[-1]; dur = end_t + 3.2; xf = 0.22
    art = load(end_art)
    n = len(items)
    def item_img(i, t):
        p = (t - cuts[i]) / (cuts[i + 1] - cuts[i])
        return contained(items[i][0], 1.0 + 0.05 * max(0, min(p, 1)))
    def frame(t):
        if t >= end_t: return end_card(t - end_t, art, title, sub, price)
        i = max(k for k in range(n) if cuts[k] <= t)
        img = item_img(i, t)
        if i > 0 and t < cuts[i] + xf:
            img = Image.blend(item_img(i - 1, t), img, ease((t - cuts[i]) / xf))
        if i == 0:
            label(img, hook, 130, size=52, kind='serif', fg=PLUM, bg=CREAM, maxw=920, pad=(34, 18), radius=28)
        else:
            label(img, f'{i + 1}/{n}  ·  {items[i][1]}', 120, size=44, kind='sans_bold', fg=PLUM, bg=CREAM, maxw=940, pad=(30, 16), radius=26,
                  alpha=ease_out((t - cuts[i]) / 0.25))
        return img
    return frame, dur

# ---- product facts
KIT = ('Kindred Curiosities journal kit', '16 ephemera sheets · 15 papers · 127 PNGs', 'Printable · $12')
CAL = ('The 2027 Art Calendar', '12 artworks · wall + desk · 36 phone wallpapers', 'Printable · $14')
KIN = ('Kindred · set of 3 prints', 'Fox & Freckles · Wolf Sister · Lilac Swan', 'Printable · $12')
MAS = ('Masquerade · set of 3 prints', 'Gilded Rain · Songbird Mask · Checkmate Carnival', 'Printable · $12')
REV = ('Reverie · set of 3 prints', 'Horned Tea Ritual · Lotus Seraph · Small World Keeper', 'Printable · $12')
BUN = ('The gallery wall bundle', 'Kindred + Masquerade + Reverie · 9 prints', 'Printable · $29')
WAL = ('Free 2027 phone wallpapers', '36 lock screens · dated or art-only', 'Free download')

def p(d, name): return d + name + '.png'

B4 = {
 # ---- listicles
 'b4-01_list_impossible-to-shop-for': ('list', 'Canopy_Runner', 30.0, dict(
     hook='Gifts for people who are\nimpossible to shop for', items=[
        (p(ST, 'Kindred Gallery Wall Holiday Gift-9'), 'the wild-hearted friend'),
        (p(ST, 'Masquerade art trio, holiday glow-8'), 'the drama lover'),
        (p(ST, 'Holiday art calendar on velvet-1'), 'the planner'),
        (p(ST, 'Thoughtful Little Christmas Desk Gift-3'), 'the desk dweller'),
        (p(ST, 'Nine-print maximalist holiday gallery wall-10'), 'the true maximalist')],
     end=p(ST, 'Nine-print maximalist holiday gallery wall-10'), card=BUN)),
 'b4-02_list_make-with-one-kit': ('list', 'Clockwork_Butterfly', 48.0, dict(
     hook='5 Christmas makes from\none printable kit', items=[
        (p(XM, 'Daydream Paper Ornaments for Christmas-3'), 'paper ornaments'),
        (p(ST, 'Beautifully Extra Holiday Wrapping Ideas-4'), 'gift tags'),
        (p(XM, 'Printable bookmark gifts for book lovers-2'), 'bookmarks'),
        (p(XM, 'Tiny art, happy holiday mail-1'), 'holiday mail'),
        (p(XM, 'Handmade Christmas table favor-1'), 'table favours')],
     end=p(XM, 'Daydream Paper Ornaments for Christmas-3'), card=KIT)),
 'b4-03_list_no-shipping-needed': ('list', 'Moon_on_the_Drum.wav', 40.0, dict(
     hook="Missed the shipping deadline?\nThese arrive in seconds.", items=[
        (p(ST, 'Holiday art calendar on velvet-1'), 'a year of art'),
        (p(ST, 'Christmas Memory-Keeping Junk Journal Kit-5'), 'a Christmas journal kit'),
        (p(XM, 'Lilac swan, kindred art gift-2'), 'print-and-frame art'),
        (p(TG, 'Vivid maximalist phone wallpapers by Eka L-4'), 'free lock screens')],
     end=p(ST, 'Holiday art calendar on velvet-1'), card=CAL)),
 'b4-04_list_treat-yourself': ('list', 'Reverie', 30.0, dict(
     hook='Gift shopping done?\nNow one for you.', items=[
        (p(ST, 'Cozy holiday junk journal kit-6'), 'a cosy journal kit'),
        (p(TG, 'Maximalist junk journal creative still life-7'), 'a little beautiful chaos'),
        (p(TG, 'Beautifully Extra Tiger Ephemera Kit-10'), '127 PNG elements'),
        (p(XM, '127-element digital collage daydream-3'), 'a digital daydream')],
     end=p(TG, 'Beautifully Extra Tiger Ephemera Kit-10'), card=KIT)),
 'b4-05_list_2027-starter-pack': ('list', 'New_year', 24.0, dict(
     hook='Your 2027\nstarter pack', items=[
        (p(ST, 'Start 2027 in Full Colour-2'), 'a wall calendar'),
        (p(TG, 'A Little Magic Desk Calendar-1'), 'a desk calendar'),
        (p(TG, 'Free 2027 calendar phone wallpapers-3'), 'free wallpapers'),
        (p(TG, 'Cobalt Blue 2027 Art Calendar-2'), '12 months of art')],
     end=p(ST, 'Start 2027 in Full Colour-2'), card=CAL)),
 'b4-06_list_which-corner': ('list', 'Carnival', 20.0, dict(
     hook='New year, new wall.\nWhich one is you? 1, 2 or 3?', per=2.8, items=[
        (p(TG, 'Kindred gallery wall_ three untamed prints-5'), 'Kindred: wild'),
        (p(TG, 'Masquerade gallery wall set in aubergine-6'), 'Masquerade: dramatic'),
        (p(TG, 'Sunlit sage corner with dreamy art trio-8'), 'Reverie: dreamy')],
     end=p(TG, 'Nine Art Prints, Endless Personality-9'), card=BUN)),
 # ---- single pins (soft)
 'b4-07_pin_ornaments':      ('pin', 'Full_Cup_Hymn', 72.0, dict(pin=p(XM, 'Daydream Paper Ornaments for Christmas-3'), focus=(512, 760), line='Print · cut · thread', card=KIT)),
 'b4-08_pin_bookmarks':      ('pin', 'Enough_in_Gold', 56.0, dict(pin=p(XM, 'Printable bookmark gifts for book lovers-2'), focus=(620, 850), line='A gift for the reader', card=KIT)),
 'b4-09_pin_gift-wrap':      ('pin', 'Tea_by_the_Window', 120.0, dict(pin=p(ST, 'Beautifully Extra Holiday Wrapping Ideas-4'), focus=(512, 680), line='Printable tags + ephemera', card=KIT)),
 'b4-10_pin_holiday-mail':   ('pin', 'Threshold_of_New_Light', 40.0, dict(pin=p(XM, 'Tiny art, happy holiday mail-1'), focus=(512, 820), line='Faux stamps for real letters', card=KIT)),
 'b4-11_pin_small-wall':     ('pin', 'Golden_Medal', 60.0, dict(pin=p(XM, 'Small entryway, big holiday mood-2'), focus=(512, 760), line='Kindred · 3 printable artworks', card=KIN)),
 'b4-12_pin_colour-recipe':  ('pin', 'Full_Cup_Hymn', 120.0, dict(pin=p(XM, 'Christmas colour recipe print mood board-1'), focus=(650, 640), line='Cobalt · tangerine · lilac', card=KIN)),
 'b4-13_pin_lilac-swan':     ('pin', 'Enough_in_Gold', 100.0, dict(pin=p(XM, 'Lilac swan, kindred art gift-2'), focus=(512, 600), line='Print · frame · gift', card=KIN)),
 'b4-14_pin_table-favour':   ('pin', 'River_of_Light', 60.0, dict(pin=p(XM, 'Handmade Christmas table favor-1'), focus=(512, 560), line='A favour for every seat', card=KIT)),
 'b4-15_pin_kindred-spirit': ('pin', 'Wild_colour', 30.0, dict(pin=p(XM, 'Kindred spirit art gift guide-2'), focus=(420, 900), line='For your wild-hearted friend', card=KIN)),
 'b4-16_pin_folded-world':   ('pin', 'Tea_by_the_Window', 160.0, dict(pin=p(XM, 'A tiny world, folded small-1'), focus=(512, 600), line='A mini keepsake to make', card=KIT)),
 'b4-17_pin_memory-journal': ('pin', 'Threshold_of_New_Light', 96.0, dict(pin=p(ST, 'Christmas Memory-Keeping Junk Journal Kit-5'), focus=(512, 760), line='Print · layer · keep', card=KIT)),
 'b4-18_pin_digital-daydream': ('pin', 'Golden_Medal', 100.0, dict(pin=p(XM, '127-element digital collage daydream-3'), focus=(512, 700), line='127 transparent PNG elements', card=KIT)),
 'b4-19_pin_cobalt-new-year': ('pin', 'River_of_Light', 100.0, dict(pin=p(TG, 'Cobalt Blue 2027 Art Calendar-2'), focus=(512, 780), line='12 months of art', card=CAL)),
 'b4-20_pin_nine-prints':    ('pin', 'Full_Cup_Hymn', 40.0, dict(pin=p(TG, 'Nine Art Prints, Endless Personality-9'), focus=(512, 820), line='Kindred · Masquerade · Reverie', card=BUN, z1=1.4)),
 'b4-21_pin_masquerade-glow': ('pin', 'Wild_colour', 70.0, dict(pin=p(ST, 'Masquerade art trio, holiday glow-8'), focus=(512, 480), line='Download · print · frame', card=MAS)),
 'b4-22_pin_reverie-corner': ('pin', 'Enough_in_Gold', 120.0, dict(pin=p(ST, 'Reverie holiday reading corner-7'), focus=(512, 540), line='Art for your cosiest corner', card=REV)),
}

def build(rid):
    kind, tr, guess, kw = B4[rid]
    R.AFILTER = SOFT_EQ if any(s in tr for s in SOFT) else ''
    a, s, beats, _ = R.track_info(tr, guess)
    title, sub, price = kw['card']
    if kind == 'pin':
        fr, dur = reel_pin(kw['pin'], kw['focus'], kw['line'], title, sub, price, beats, kw.get('z1', 1.6))
    else:
        fr, dur = reel_list(kw['items'], kw['hook'], title, sub, price, kw['end'], beats, kw.get('per', 2.4))
    return fr, dur, a, s

R.build = build

if __name__ == '__main__':
    rid = sys.argv[1]
    pts = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    R.render(rid, pts)
