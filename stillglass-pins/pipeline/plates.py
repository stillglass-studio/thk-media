"""Export line-art plates from an interior PDF by plate number.
Usage: python3 -I plates.py <interior.pdf> <BOOK> <outdir> <n> [<n> ...]"""
import sys, re, os, pypdf, pypdfium2
pdf, book, outdir, nums = sys.argv[1], sys.argv[2], sys.argv[3], [int(n) for n in sys.argv[4:]]
os.makedirs(outdir, exist_ok=True)
idx = {}
for i, p in enumerate(pypdf.PdfReader(pdf).pages):
    m = re.match(r"\s*(\d\d)\s+·\s+(.+?)\s+·", (p.extract_text() or "").strip())
    if m: idx[int(m.group(1))] = (i, m.group(2).strip())
doc = pypdfium2.PdfDocument(pdf)
for n in nums:
    i, name = idx[n]
    slug = re.sub(r"[^a-z]", "", name.lower().replace("the ", ""))[:18]
    im = doc[i].render(scale=2.5).to_pil().convert("RGB"); w, h = im.size
    out = os.path.join(outdir, f"{book}_plate{n:02d}_{slug}_lineart.png")
    im.crop((0, 0, w, int(h * 0.93))).save(out); print(out, "|", name)
