"""9:16 overlays for the reels built by reels_build.py: letterbox bars, the series tag and hook on the first line,
the on-screen text from the script (timed to a cue word when given), 1–3 word hard-cut captions, the friend-footage
credit, the cover text (rovl/cover.png, laid over the cover frame on the Mac) and the end card.
usage: reels_ovl.py <kit dir> <thumbnail.jpg>
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion
motion.W, motion.H = 1080, 1920
from motion import Layer, render, big_text, rich, rpill, ImageDraw, Image, INTERX, ANTON, YEL, INK
W, H = motion.W, motion.H
KIT, THUMB = sys.argv[1:3]
R = json.load(open(f'{KIT}/reel.json')); OUT = f'{KIT}/rovl'; os.makedirs(OUT, exist_ok=True)
CAP_Y, BAR = 1240, 110
BLANK = Image.new('RGBA', (1, 1))

def chunks(words, seg_end):
    out, cur = [], []
    for w, t in words:
        if cur and t - cur[-1][1] > 0.55: out.append(cur); cur = []
        cur.append((w, t))
        if len(cur) == 3 or re.search(r'[.,?!]$', w) or sum(len(x) + 1 for x, _ in cur) > 15: out.append(cur); cur = []
    if cur: out.append(cur)
    k = 0
    while k < len(out) - 1:
        if len(out[k]) == 1 and len(out[k][0][0]) <= 3: out[k:k + 2] = [out[k] + out[k + 1]]
        else: k += 1
    res = []
    for k, c in enumerate(out):
        t0 = c[0][1]; t1 = out[k + 1][0][1] if k + 1 < len(out) else min(seg_end, c[-1][1] + 0.9)
        res.append((' '.join(w for w, _ in c).upper().rstrip(','), t0, max(t0 + 0.2, t1)))
    return res

def fit(im, maxw=W - 120):
    return im if im.width <= maxw else im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
def span(im, x, y, a, b, anim='none', dur=0.01):
    return Layer(lambda t, im=im, life=b - a: im if t < life else BLANK, x, y, a, anim, dur)
def title(txt, size, fill='white'):
    """Anton title that can carry emoji"""
    if re.search(r'[\U0001F000-\U0001FAFF☀-➿⬀-⯿]', txt):
        return fit(rich(txt, int(size * 0.8), fill, ANTON, stroke=max(6, size // 14), stroke_fill=INK))
    return fit(big_text(txt, size, fill, max(6, size // 16)))

bars = Image.new('RGBA', (W, BAR), (0, 0, 0, 255))
for n, s in enumerate(R['segs']):
    t0, d = s['t'], s['d']; L = []
    if s['kind'] == 'silence': render(L, d, f'{OUT}/{n:02d}.mov'); continue
    L += [Layer(bars, W / 2, BAR / 2, 0, 'none', 0.01), Layer(bars, W / 2, H - BAR / 2, 0, 'none', 0.01)]
    for txt, a, b in chunks(s['words'], t0 + d):
        L.append(span(fit(big_text(txt, 92, 'white', 9)), W / 2, CAP_Y, a - t0 - 0.02, b - t0, 'pop', 0.12))
    if n == 0 and R['tag']:
        L.append(span(rpill(R['tag'], 40, fg=INK, bg=YEL + (255,), pad=(26, 10)), W / 2, BAR + 70, 0.05, d, 'slide-up', 0.3))
    if n == 0 and R['hook']:
        L.append(span(title(R['hook'], 120, YEL), W / 2, 420, 0.1, d, 'pop', 0.3))
    items = [x for x in s['text'].split('|') if x]
    cues = s['flags'].get('cues', {})
    for k, txt in enumerate(items):
        if R['name'] == 'trailer' and n == 0:
            L.append(Layer(big_text('NOT CGI.', 230, 'white', 12), W / 2, 760, 0.05, 'pop', 0.35)); continue
        cw = cues.get(txt)
        a = next((wt for w, wt in s['words'] if w.lower().strip('.,?!') == cw), None) if cw else None
        a = (a - t0 - 0.05) if a is not None else 0.15 + 0.45 * k
        y = (650 if len(items) > 1 else 700) + k * 170 if not (n == 0 and R['hook']) else 600 + k * 150
        L.append(span(title(txt, 150 if len(items) > 1 else 170, YEL if k == len(items) - 1 else 'white'), W / 2, y, max(0.0, a), d, 'pop', 0.3))
    for sh in R['shots']:
        if sh['seg'] == n and sh['f'].startswith('from_wechat/'):
            im = rpill('📱 filmed by a friend', 30, bg=(16, 17, 22, 170), pad=(20, 8))
            L.append(span(im, 50 + im.width / 2, BAR + (140 if n == 0 and R['tag'] else 50), sh['t'] - t0, sh['t'] - t0 + sh['d']))
    render(L, d, f'{OUT}/{n:02d}.mov')
    print(R['name'], n, s['kind'], len(L), file=sys.stderr)

# cover text: laid over the cover frame (a clean frame of the cover clip) on the Mac
cv = R['cover']; spec_cover = None
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reels_spec import REELS
c = REELS[R['name']]['cover']
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); g = Image.new('L', (1, H))
for y in range(H): g.putpixel((0, y), int(165 * max(0, 1 - y / 950) + 150 * max(0, (y - 1150) / 770)))
shade = Image.new('RGBA', (W, H), (0, 0, 0, 255)); shade.putalpha(g.resize((W, H))); im.alpha_composite(shade)
def put(t, cy): im.alpha_composite(t, (int(W / 2 - t.width / 2), int(cy - t.height / 2)))
put(rpill(c['top'], 46, fg=INK, bg=YEL + (255,), pad=(30, 12)), 360)
put(fit(big_text(c['big'], 250, 'white', 14)), 560)
put(fit(big_text(c['sub'], 100, YEL, 9)), 1370)
put(fit(big_text(c['title'], 150, 'white', 11)), 1500)
im.save(f'{OUT}/cover.png')

# end card
a, dur = R['end']
th = Image.open(THUMB).convert('RGBA'); th = th.resize((940, int(th.height * 940 / th.width)), Image.LANCZOS)
m = Image.new('L', th.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, th.width - 1, th.height - 1], 28, fill=255); th.putalpha(m)
bg = Image.new('RGBA', (W, H), (8, 8, 10, 255))
L = [Layer(big_text('WATCH THE', 120, 'white', 8), W / 2, 420, 0.0, 'pop', 0.35),
     Layer(big_text('FULL VIDEO', 150, YEL, 9), W / 2, 560, 0.1, 'pop', 0.35),
     Layer(th, W / 2, 940, 0.25, 'slide-up', 0.45),
     Layer(rich('Chongqing Isn’t Real… So I Went Inside', 50, 'white', INTERX), W / 2, 1290, 0.5, 'fade', 0.4),
     Layer(rpill('▶  YouTube · Shawnlemuel', 48, fg='white', bg=(230, 33, 40, 255), pad=(34, 14)), W / 2, 1420, 0.8, 'pop', 0.35),
     Layer(rpill('🔗 link in bio', 44, fg=INK, bg=YEL + (255,), pad=(30, 12)), W / 2, 1530, 1.1, 'pop', 0.35)]
if R['tag']: L.append(Layer(rpill(R['tag'], 38, fg=INK, bg=(255, 255, 255, 235), pad=(24, 10)), W / 2, 260, 0.0, 'fade', 0.3))
render(L, dur, f'{OUT}/end.mp4', bg=bg)
print(R['name'], 'end card + cover', file=sys.stderr)
