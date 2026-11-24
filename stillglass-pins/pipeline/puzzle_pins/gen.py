import re, json, base64, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent

def b64(p):
    return 'data:image/jpeg;base64,' + base64.b64encode(Path(p).read_bytes()).decode()

# ---------- word search extraction + verification ----------
def ws_puzzle(path, n):
    t = open(path).read()
    i = t.find(f'PUZZLE {n} · 100'); j = t.find('\f', i)
    block = t[i:j]
    lines = [re.sub(r'\s+',' ',l).strip() for l in block.split('\n') if l.strip()]
    title = lines[1]
    grid = [l.split() for l in lines if re.fullmatch(r'([A-Z] ){12}[A-Z]', l)]
    k = block.find('FIND THESE WORDS')
    words = re.findall(r'·\s*([A-Z]{2,})\b', block[k:block.find('Large Print Bible', k)])
    assert len(grid) == 13 and all(len(r) == 13 for r in grid), (n, len(grid))
    return title, grid, words

def find(grid, w):
    D = [(0,1),(1,0),(1,1),(-1,1),(0,-1),(-1,0),(-1,-1),(1,-1)]
    for r in range(13):
        for c in range(13):
            for dr, dc in D:
                ok = True
                for k, ch in enumerate(w):
                    rr, cc = r+dr*k, c+dc*k
                    if not (0 <= rr < 13 and 0 <= cc < 13 and grid[rr][cc] == ch):
                        ok = False; break
                if ok: return True
    return False

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1000px;height:1500px;font-family:'Inter',sans-serif;color:#1b2540}
.pin{width:1000px;height:1500px;position:relative;overflow:hidden;
 background:radial-gradient(ellipse at 50% 0%,#fbf6ec 0%,#f3e9d6 70%,#ecdfc6 100%)}
.top{background:#16213e;color:#f4ead5;padding:40px 60px 34px;text-align:center;position:relative}
.top:after{content:'';position:absolute;left:0;right:0;bottom:-10px;height:10px;
 background:repeating-linear-gradient(90deg,#b8893b 0 60px,#7a2f3a 60px 120px,#2f5d62 120px 180px,#4b3f7a 180px 240px)}
.kicker{font:600 22px 'Inter';letter-spacing:.28em;color:#d9b46a;text-transform:uppercase;margin-bottom:16px}
h1{font-family:'Lora',serif;font-weight:700;font-size:66px;line-height:1.08;color:#fbf3e2}
h1 em{color:#e6c27a;font-style:italic}
.sub{font:400 27px 'Inter';color:#d8cfbd;margin-top:16px}
.body{padding:36px 60px 0}
.card{background:#fffdf8;border:2px solid #d9c49b;border-radius:18px;box-shadow:0 10px 30px rgba(60,40,10,.12);padding:28px 30px}
.grid{display:grid;grid-template-columns:repeat(13,1fr);gap:0;margin:0 auto;width:780px}
.grid div{height:49px;display:flex;align-items:center;justify-content:center;font:600 31px 'Inter';color:#16213e}
.ttl{font:600 22px 'Inter';letter-spacing:.2em;text-transform:uppercase;color:#9a7330;text-align:center;margin-bottom:10px}
.words{display:grid;grid-template-columns:repeat(4,1fr);gap:4px 18px;margin-top:16px;font:700 24px 'Inter';color:#16213e;letter-spacing:.04em}
.words span.long{grid-column:span 2}
.words span:before{content:'☐ ';color:#b8893b;font-weight:400}
.q{margin-bottom:20px}
.q b{display:block;font:600 29px/1.3 'Lora',serif;color:#16213e;margin-bottom:8px}
.opts{display:grid;grid-template-columns:1fr 1fr;gap:4px 24px;font:400 24px 'Inter';color:#3a4258}
.opts i{font-style:normal;font-weight:700;color:#9a7330;margin-right:8px}
.strip{position:absolute;left:0;right:0;bottom:0;height:270px;background:#16213e;display:flex;align-items:center;padding:0 60px;gap:40px}
.strip img{height:225px;border-radius:4px;box-shadow:0 10px 24px rgba(0,0,0,.45);transform:rotate(-2deg)}
.strip .t{color:#f4ead5}
.strip .t .bk{font:700 34px/1.2 'Lora',serif;color:#fbf3e2}
.strip .t .fx{font:400 24px/1.45 'Inter';color:#cfc6b4;margin-top:10px}
.strip .t .cta{display:inline-block;margin-top:18px;background:#b8893b;color:#16213e;font:700 24px 'Inter';padding:12px 26px;border-radius:40px;letter-spacing:.04em}
.brand{position:absolute;right:22px;top:16px;font:600 14px 'Inter';letter-spacing:.3em;color:#7f88a3}
.cipher{font:700 38px/1.75 'Inter';letter-spacing:.12em;color:#16213e;text-align:center}
.start{font:600 24px 'Inter';color:#9a7330;text-align:center;margin:18px 0 6px;letter-spacing:.08em}
.blanks{text-align:center;font:400 26px 'Inter';color:#9aa0ad;letter-spacing:.2em;margin-top:8px}
.steps .s{display:flex;gap:22px;margin-bottom:24px;align-items:flex-start}
.steps .n{flex:0 0 58px;height:58px;border-radius:50%;background:#16213e;color:#e6c27a;font:700 30px 'Lora';display:flex;align-items:center;justify-content:center}
.steps .s div b{display:block;font:700 30px/1.25 'Lora',serif;color:#16213e}
.steps .s div p{font:400 24px/1.45 'Inter';color:#3a4258;margin-top:4px}
.ans{margin-top:16px;text-align:center;font:600 21px 'Inter';color:#7a6a48;letter-spacing:.03em}
.mono{font-family:'Inter';font-weight:700;letter-spacing:.1em;color:#7a2f3a}
"""

CSS_BIG = """
.k-trivia .q{margin-bottom:20px}
.k-trivia .q b{font-size:32px;margin-bottom:8px}
.k-trivia .opts{font-size:27px;gap:4px 24px}
.k-trivia .card{padding:30px 36px}
.k-trivia .ans{font-size:26px;margin-top:6px}
.k-crypto .cipher{font-size:48px;line-height:1.8}
.k-crypto .card{padding:44px 24px}
.k-crypto .start{font-size:30px;margin-top:34px}
.k-crypto .blanks{font-size:30px;margin-top:18px;color:#7a6a48;letter-spacing:.02em}
.k-crypto .ttl{font-size:26px;margin-bottom:30px}
.k-steps .card{padding:46px 40px}
.k-steps .s{margin-bottom:40px}
.k-steps .s div b{font-size:38px}
.k-steps .s div p{font-size:30px}
.k-steps .n{flex:0 0 72px;height:72px;font-size:36px}
"""

def page(inner, kind=''):
    return f"<html><head><meta charset='utf-8'><style>{CSS}{CSS_BIG}</style></head><body><div class='pin k-{kind}'>{inner}<div class='brand'>STILLGLASS STUDIO</div></div></body></html>"

def strip(cover, book, facts, cta):
    imgs = ''.join(f"<img src='{b64(HERE/'covers'/(c+'.jpg'))}' style='margin-right:-30px'>" for c in cover.split('+'))
    return f"<div class='strip'><div style='display:flex'>{imgs}</div><div class='t' style='margin-left:20px'><div class='bk'>{book}</div><div class='fx'>{facts}</div><div class='cta'>{cta}</div></div></div>"

def top(kicker, h1, sub=''):
    s = f"<div class='sub'>{sub}</div>" if sub else ''
    return f"<div class='top'><div class='kicker'>{kicker}</div><h1>{h1}</h1>{s}</div>"

def ws_pin(p):
    title, grid, words = ws_puzzle(p['src'], p['n'])
    missing = [w for w in words if not find(grid, w)]
    assert not missing, (p['n'], missing)
    assert len(words) == p['count'], (p['n'], len(words))
    cells = ''.join(f'<div>{ch}</div>' for row in grid for ch in row)
    wl = ''.join(f'<span class="long">{w}</span>' if len(w)>9 else f'<span>{w}</span>' for w in words)
    inner = top(p['kicker'], p['h1']) + f"<div class='body'><div class='card'><div class='ttl'>{title}</div><div class='grid'>{cells}</div><div class='words'>{wl}</div></div></div>" + strip(p['cover'], p['book'], p['facts'], p['cta'])
    return inner

def trivia_pin(p):
    qs = ''
    for q, opts in p['qs']:
        o = ''.join(f'<span><i>{"ABCD"[k]}</i>{x}</span>' for k, x in enumerate(opts))
        qs += f"<div class='q'><b>{q}</b><div class='opts'>{o}</div></div>"
    ans = f"<div class='ans'>{p['ans']}</div>" if p.get('ans') else ''
    return top(p['kicker'], p['h1'], p.get('sub', '')) + f"<div class='body'><div class='card'>{qs}{ans}</div></div>" + strip(p['cover'], p['book'], p['facts'], p['cta'])

def crypto_pin(p):
    fs = p.get('cfs', 48)
    lines = ''.join(f"<div style='white-space:nowrap;font-size:{fs}px'>{l}</div>" for l in p['cipher'])
    return top(p['kicker'], p['h1'], p.get('sub', '')) + f"<div class='body'><div class='card'><div class='ttl'>{p['ref']}</div><div class='cipher'>{lines}</div><div class='start'>STARTER LETTERS &nbsp; {p['starters']}</div><div class='blanks'>{p['hint']}</div></div></div>" + strip(p['cover'], p['book'], p['facts'], p['cta'])

def steps_pin(p):
    s = ''.join(f"<div class='s'><div class='n'>{k+1}</div><div><b>{a}</b><p>{b}</p></div></div>" for k, (a, b) in enumerate(p['steps']))
    return top(p['kicker'], p['h1'], p.get('sub', '')) + f"<div class='body'><div class='card steps'>{s}</div></div>" + strip(p['cover'], p['book'], p['facts'], p['cta'])

KIND = {'ws': ws_pin, 'trivia': trivia_pin, 'crypto': crypto_pin, 'steps': steps_pin}

if __name__ == '__main__':
    pins = json.load(open(HERE / 'pins.json'))
    only = sys.argv[1:]
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1000, 'height': 1500})
        for p in pins:
            if only and p['id'] not in only: continue
            html = page(KIND[p['kind']](p), p['kind'])
            pg.set_content(html, wait_until='networkidle')
            pg.wait_for_timeout(300)
            # overflow check: body card bottom must sit above the strip
            over = pg.evaluate("()=>{const c=document.querySelector('.card').getBoundingClientRect();const s=document.querySelector('.strip').getBoundingClientRect();return c.bottom - s.top}")
            pg.screenshot(path=str(HERE / 'out' / (p['id'] + '.png')))
            print(p['id'], 'overlap_px=%d' % over)
        br.close()
