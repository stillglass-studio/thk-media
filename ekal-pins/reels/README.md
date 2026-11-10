# Eka L. short-form reels

Reels for TikTok, YouTube Shorts and Facebook Reels, published through Metricool (brand "Eka L", blog id 8002367).
The MP4s here are served from their public raw URLs, which is how Metricool fetches them.

## Layout

| Path | What it is |
| --- | --- |
| `YYYY-MM-wN/` | One folder per weekly batch of rendered reels (1080x1920, 30 fps, H.264, AAC, -14 LUFS) |
| `schedule-YYYY-MM-wN.json` | Captions per platform, product link and posting slots for that batch |
| `pipeline/render.py` | Template renderer: PIL frames piped to ffmpeg, cuts timed to the beats of the track |
| `wildhearted/` | 18 Wildhearted coloring-book reels: grayscale plates turning into colour |
| `schedule-2026-11-reshuffle.json` | Current master plan after adding Wildhearted (Nov 14 - Dec 22) |
| `pipeline/wh_render.py` | Wildhearted renderer: sweep, bloom, layered-scribble, slider, montage and mood effects |
| `pipeline/analyse.py`, `pipeline/audit.py` | Track analysis: tempo, beat grid, loudest sections, brightness and harshness |

Source art and music are not stored here because this repo is public. The renderer reads them from the
working session (the Payhip preview pack and the Suno tracks).

## Formats

1. Look closer: starts on a detail, zooms out to the full print, loops.
2. Pick one: three prints numbered 1-2-3, then the set, with "Which one goes on your wall?"
3. Birth-month art: the 12 calendar months, one per beat.
4. Lock screen glow-up: plain phone, then the wallpapers on the beat. Ends on "Free".
5. Not another sepia kit: journal elements drop onto a page, then the sheets flick past.
6. Pick your set / 9-print bundle grid (batch 2).

### Wildhearted (Amazon coloring book)

Each plate's grayscale page (600 dpi master) is aligned pixel-for-pixel with its colorized version, then revealed with one of six effects:
brush sweep, radial bloom from the face, layered scribble fill, colored-pencil hatching (with a pencil that picks up the colour it lays down), before/after slider, three-page montage, and warm / cool / pastel mood grades.
End card uses the book cover on the book's charcoal-and-gold palette with "Available on Amazon" and "Search: Wildhearted Eka Lestienne".

## Cadence

- TikTok: 2 a day. From Nov 14: 10:07 = Eka L. shop reel, 18:07 = Wildhearted reel (runs to Dec 1); then 1 a day at 18:07 with Wildhearted batch 2 to Dec 17
- Facebook + YouTube: 1 a day. Nov 11-22 at 12:07 (FB) and 16:07 (YT); from Nov 23 one combined post at 14:07, alternating Wildhearted and shop reels (runs to Dec 22), then Wildhearted batch 2 to Jan 7

Times come from Metricool's best-time data for each network and should be revisited once the account has its own history.

## Pricing on end cards

Gallery sets and journal kit show $12. The calendar shows $14 until Jan 31, then a "50% off" end card in February.
Wallpapers always show "Free". The CAL2027 coupon (until Dec 1) appears in captions only.

## Track shortlist

- Warm, melodic: Tea by the Window, Threshold of New Light, River of Light, Golden Medal Dusk, Wild colour, Reverie
- Upbeat, balanced: Clockwork Butterfly Run, Canopy Runner, Moon on the Drum, New year, Carnival
- Not used: Catwalk Parade (rejected by ear), Run The Floor (both), Treadmill Crown, Moon on the Drum (1),
  Rainbow Dream Pulse (bright and harsh); Floating Islands, Forgotten Planet, Frequencies of Letting Go (too bassy for phone speakers)
