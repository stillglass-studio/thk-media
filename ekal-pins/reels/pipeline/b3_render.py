"""Batch 3: softer reels. Slow room push-ins from the Pinterest mockups and slow colored-pencil Wildhearted reels.
Soft tracks get a phone-speaker EQ (less sub-bass, a little more mid presence) before loudnorm."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import render as R
import wh_render as WHR
from render import W, H, load, cover_crop, ease, ease_out, label, end_card, PLUM, CREAM

PINS = '/home/claude/pins3/Pins'
R.AFILTER = 'highpass=f=60,lowshelf=f=180:g=-6,equalizer=f=900:t=q:w=1.2:g=3,'

def reel_room(pin, focus, art, line, title, sub, price, beats, z1=1.45):
    src = load(f'{PINS}/{pin}'); art_img = load(art)
    full = (src.width / 2, src.height / 2)
    tA = min(beats, key=lambda b: abs(b - 6.0))           # room push-in ends, art fades in
    end_t = min(beats, key=lambda b: abs(b - (tA + 6.0)))  # art drift ends
    dur = end_t + 3.2; xf = 1.0
    def room(t):
        p = ease(min(t / (tA + xf), 1.0))
        z = 1.0 + (z1 - 1.0) * p
        cx = full[0] + (focus[0] - full[0]) * p; cy = full[1] + (focus[1] - full[1]) * p
        return cover_crop(src, cx, cy, z).convert('RGBA')
    from PIL import ImageFilter, ImageEnhance
    bg = ImageEnhance.Brightness(cover_crop(art_img, art_img.width / 2, art_img.height / 2, 1.0).filter(ImageFilter.GaussianBlur(40))).enhance(0.55).convert('RGBA')
    fit = art_img.copy(); fit.thumbnail((940, 1300), R.Image.LANCZOS)
    card = R.Image.new('RGBA', (fit.width + 20, fit.height + 20), CREAM + (255,)); card.alpha_composite(fit.convert('RGBA'), (10, 10))
    card = R.shadowed(card, blur=22, off=(0, 18), opacity=150)
    def artf(t):
        p = min(max((t - tA) / (end_t - tA + 1.0), 0), 1)
        img = bg.copy(); s = 0.97 + 0.07 * ease(p)
        c = card.resize((int(card.width * s), int(card.height * s)), R.Image.BILINEAR)
        R.paste_center(img, c, W / 2, 960)
        return img
    def frame(t):
        if t >= end_t:
            return end_card(t - end_t, art_img, title, sub, price)
        if t < tA: img = room(t)
        elif t < tA + xf:
            a = ease((t - tA) / xf); img = R.Image.blend(room(t), artf(t), a)
        else: img = artf(t)
        if t > tA + 0.6:
            label(img, line, 175, size=40, kind='sans_bold', fg=PLUM, bg=CREAM, alpha=ease_out((t - tA - 0.6) / 0.6), pad=(30, 16), radius=26)
        return img
    return frame, dur

P = '/home/claude/in/EkaL_Product-Previews/EkaL_Product-Previews/'
B3 = {
 'b3-01_room_calendar-desk':  ('rm', 'Full_Cup_Hymn', 40.0, dict(pin='01-2027-art-calendar-desk.jpg', focus=(500, 520), art=P + '01_2027-Art-Calendar/Calendar_Wall-Letter_01-January.jpg', line='January · one of 12 artworks', title='The 2027 Art Calendar', sub='12 artworks · wall + desk · 36 phone wallpapers', price='Printable · $14')),
 'b3-02_room_wallpapers':     ('rm', 'Enough_in_Gold', 48.0, dict(pin='03-free-2027-phone-wallpapers.jpg', focus=(500, 600), art=P + '02_Phone-Wallpapers/Wallpaper_art-only_GildedRain.jpg', line='Free · 36 lock screens', title='Free 2027 phone wallpapers', sub='Dated by month or art-only', price='Free download')),
 'b3-03_room_journal-desk':   ('rm', 'Tea_by_the_Window', 64.0, dict(pin='04-junk-journal-in-use.jpg', focus=(520, 720), art=P + '03_Junk-Journal-Kit/Kit_Sheet_06-Fussy-cuts-2.jpg', line='16 sheets · 15 papers · 127 PNGs', title='Kindred Curiosities journal kit', sub='Printable + digital junk journal ephemera', price='Printable · $12')),
 'b3-04_room_journal-ephemera': ('rm', 'Full_Cup_Hymn', 88.0, dict(pin='05-junk-journal-ephemera.jpg', focus=(520, 640), art=P + '03_Junk-Journal-Kit/Kit_Sheet_08-Stamps-postmarks.jpg', line='Cut, layer, collage', title='Kindred Curiosities journal kit', sub='Printable + digital junk journal ephemera', price='Printable · $12')),
 'b3-05_room_kindred':        ('rm', 'Velvet_Cocoon', 96.0, dict(pin='06-kindred-gallery-wall.jpg', focus=(510, 720), art=P + '04_Gallery-Set_Kindred/Kindred_1-FoxAndFreckles_print-2x3.jpg', line='Fox & Freckles · Kindred set', title='Kindred · set of 3 prints', sub='Fox & Freckles · Wolf Sister · Lilac Swan', price='Printable · $12')),
 'b3-06_room_masquerade':     ('rm', 'Enough_in_Gold', 88.0, dict(pin='08-masquerade-gallery-wall.jpg', focus=(510, 720), art=P + '05_Gallery-Set_Masquerade/Masquerade_2-SongbirdMask_print-2x3.jpg', line='Songbird Mask · Masquerade set', title='Masquerade · set of 3 prints', sub='Gilded Rain · Songbird Mask · Checkmate Carnival', price='Printable · $12')),
 'b3-07_room_reverie':        ('rm', 'Frequencies_of_Letting_Go.wav', 80.0, dict(pin='09-reverie-gallery-wall.jpg', focus=(510, 740), art=P + '06_Gallery-Set_Reverie/Reverie_2-LotusSeraph_print-2x3.jpg', line='Lotus Seraph · Reverie set', title='Reverie · set of 3 prints', sub='Horned Tea Ritual · Lotus Seraph · Small World Keeper', price='Printable · $12')),
 'b3-08_room_bundle':         ('rm', 'Full_Cup_Hymn', 56.0, dict(pin='10-maximalist-gallery-wall-bundle.jpg', focus=(650, 860), art=P + '07_Gallery-Bundle_All-3-Sets/Bundle_overview_9-prints.jpg', line='9 prints · 3 sets', title='The gallery wall bundle', sub='Kindred + Masquerade + Reverie · 9 prints', price='Printable · $29', z1=1.3)),
 'b3-09_slowpencil_small-things': ('sp', 'Full_Cup_Hymn', 64.0, dict(n=2, text='Carry less.\nColour more.', origin=(0.5, 0.35), seed=101)),
 'b3-10_slowpencil_joy':      ('sp', 'Enough_in_Gold', 64.0, dict(n=3, text='Joy, one pencil\nstroke at a time.', origin=(0.5, 0.32), seed=103)),
 'b3-11_slowpencil_fox-witness': ('sp', 'Tea_by_the_Window', 96.0, dict(n=9, text='Breathe out.\nWatch the fox appear.', origin=(0.45, 0.4), seed=107)),
 'b3-12_slowpencil_many-eyed-house': ('sp', 'Velvet_Cocoon', 112.0, dict(n=13, text='A quiet house,\nslowly filling with colour.', origin=(0.5, 0.35), seed=109)),
 'b3-13_slowpencil_tenderness': ('sp', 'Full_Cup_Hymn', 104.0, dict(n=17, text='Soft hands,\nwild heart.', origin=(0.5, 0.32), seed=113)),
 'b3-14_slowpencil_rest':     ('sp', 'Frequencies_of_Letting_Go.wav', 128.0, dict(n=19, text='Rest is allowed.\nSo is colour.', origin=(0.5, 0.35), seed=127)),
 'b3-15_slowpencil_horizon':  ('sp', 'River_of_Light', 30.0, dict(n=35, text='Sunday pace.\nColored pencil.', origin=(0.5, 0.3), seed=131)),
 'b3-16_slowpencil_moving-water': ('sp', 'Enough_in_Gold', 72.0, dict(n=37, text='Let it move\nslowly.', origin=(0.5, 0.4), seed=137)),
}

def build(rid):
    kind, tr, guess, kw = B3[rid]
    a, s, beats, _ = R.track_info(tr, guess)
    if kind == 'rm': fr, dur = reel_room(beats=beats, **kw)
    else: fr, dur = WHR.reel_pencil(beats=beats, span=9.0, **kw)
    return fr, dur, a, s

R.build = build

if __name__ == '__main__':
    rid = sys.argv[1]
    pts = [float(x) for x in sys.argv[2].split(',')] if len(sys.argv) > 2 else None
    R.render(rid, pts)
