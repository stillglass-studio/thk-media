# Eka L. short-form reels

Reels for TikTok, YouTube Shorts and Facebook Reels, published through Metricool (brand "Eka L", blog id 8002367).
The MP4s here are served from their public raw URLs, which is how Metricool fetches them.

## Layout

| Path | What it is |
| --- | --- |
| `YYYY-MM-wN/` | One folder per weekly batch of rendered reels (1080x1920, 30 fps, H.264, AAC, -14 LUFS) |
| `schedule-YYYY-MM-wN.json` | Captions per platform, product link and posting slots for that batch |
| `pipeline/render.py` | Template renderer: PIL frames piped to ffmpeg, cuts timed to the beats of the track |
| `pipeline/analyse.py`, `pipeline/audit.py` | Track analysis: tempo, beat grid, loudest sections, brightness and harshness |

Source art and music are not stored here because this repo is public. The renderer reads them from the
working session (the Payhip preview pack and the Suno tracks).

## Formats

1. Look closer: starts on a detail, zooms out to the full print, loops.
2. Pick one: three prints numbered 1-2-3, then the set, with "Which one goes on your wall?"
3. Birth-month art: the 12 calendar months, one per beat.
4. Lock screen glow-up: plain phone, then the wallpapers on the beat. Ends on "Free".
5. Not another sepia kit: journal elements drop onto a page, then the sheets flick past.

## Cadence

- TikTok: 2 a day, 10:07 and 18:07 Paris time
- YouTube Shorts: 1 a day, 16:07
- Facebook Reels: 1 a day, 12:07

Times come from Metricool's best-time data for each network and should be revisited once the account has its own history.

## Pricing on end cards

Gallery sets and journal kit show $12. The calendar shows $14 until Jan 31, then a "50% off" end card in February.
Wallpapers always show "Free". The CAL2027 coupon (until Dec 1) appears in captions only.

## Track shortlist

- Warm, melodic: Tea by the Window, Threshold of New Light, River of Light, Golden Medal Dusk, Wild colour, Reverie
- Upbeat, balanced: Clockwork Butterfly Run, Canopy Runner, Moon on the Drum, New year, Carnival
- Not used: Catwalk Parade (rejected by ear), Run The Floor (both), Treadmill Crown, Moon on the Drum (1),
  Rainbow Dream Pulse (bright and harsh); Floating Islands, Forgotten Planet, Frequencies of Letting Go (too bassy for phone speakers)
