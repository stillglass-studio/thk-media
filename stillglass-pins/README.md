# Stillglass pins

Public image host for Stillglass Studio Pinterest pins, scheduled through Metricool.

- `inbox/` raw images from the Stillglass Pin Studio GPT (`BOOK_TYPE_subject_vN.png`)
- `ready/` finished 1000x1500 pins (`..._h<n>.png` = headline variant n)
- `pipeline/compose.py` builds a pin: navy headline band, real cover badge
- `pipeline/plates.py` exports line-art plates from the interior PDFs
- `log.csv` every scheduled pin: board, link, time, Metricool id

Fonts: Cinzel and EB Garamond (SIL Open Font License).
