"""9:16 overlays for the ep. 1 hype reel, movie-trailer style: thin letterbox bars, big title words timed to the
VO (instead of captions where the title already says the line), 1–3 word hard-cut captions elsewhere, one sticker
per question, the friend-footage credit and the end card.
usage: reel_ovl.py <workdir> <thumbnail.jpg>     reads reel.json, writes rovl/<n>.mov and rovl/end.mp4
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion
motion.W, motion.H = 1080, 1920
from motion import Layer, render, big_text, rich, rpill, ImageDraw, Image, INTERX, YEL, INK
from sticker import emoji
W, H = motion.W, motion.H
WD, THUMB = sys.argv[1:3]
R = json.load(open(f'{WD}/reel.json')); OUT = f'{WD}/rovl'; os.makedirs(OUT, exist_ok=True)
CAP_Y, BAR = 1240, 110
BLANK = Image.new('RGBA', (1, 1))
TITLED = {'cgi', 'tourist', 'worth'}          # the title says the line, so no captions under it

def chunks(words, seg_end):
    """1–3 word captions; a pause or punctuation ends one; never leave a short word alone"""
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
    """show im from a to b (segment time), hard cut out"""
    return Layer(lambda t, im=im, life=b - a: im if t < life else BLANK, x, y, a, anim, dur)
def word_t(seg, word):
    return next((t for w, t in seg['words'] if w.lower().strip('.,?!') == word), seg['t']) - seg['t']

bars = Image.new('RGBA', (W, BAR), (0, 0, 0, 255))
for n, s in enumerate(R['segs']):
    t0, d = s['t'], s['d']; L = []
    if s['name'] not in ('silence', 'thud'):
        L += [Layer(bars, W / 2, BAR / 2, 0, 'none', 0.01), Layer(bars, W / 2, H - BAR / 2, 0, 'none', 0.01)]
    if s['name'] not in TITLED:
        for txt, a, b in chunks(s['words'], t0 + d):
            L.append(span(fit(big_text(txt, 92, 'white', 9)), W / 2, CAP_Y, a - t0 - 0.02, b - t0, 'pop', 0.12))
    nm, tx = s['name'], s['text']
    if nm == 'cgi':
        L.append(Layer(big_text('NOT CGI.', 230, 'white', 12), W / 2, 760, 0.05, 'pop', 0.35))
    elif nm == 'tourist':
        a = word_t(s, 'six') - 0.05; b = word_t(s, 'not') - 0.05
        L.append(span(big_text('6 DAYS.', 210, 'white', 10), W / 2, 760, a, b, 'pop', 0.2))
        L.append(span(fit(big_text('NOT A TOURIST.', 150, YEL, 10)), W / 2, 760, b, d, 'pop', 0.2))
    elif nm == 'worth':
        a = word_t(s, 'worth') - 0.1
        L.append(span(fit(big_text('IS IT', 150, 'white', 10)), W / 2, 650, a, d, 'fade', 0.4))
        L.append(span(fit(big_text('WORTH IT?', 190, YEL, 11)), W / 2, 870, a + 0.25, d, 'fade', 0.4))
    elif nm == '8d':
        L.append(span(big_text('8D?!', 260, YEL, 12), W / 2, 700, word_t(s, '8d') - 0.05, d, 'pop', 0.3))
    elif nm == 'hotpot':
        a = word_t(s, 'spicy') - 0.05
        for k in range(3): L.append(span(emoji('🌶️', 200, 9), W / 2 + (k - 1) * 230, 680, a + 0.25 * k, d, 'pop', 0.3))
    elif tx:
        L.append(Layer(emoji(tx, 230, 10), W / 2, 680, 0.1, 'pop', 0.35, wiggle=True))
    for sh in R['shots']:
        if sh['seg'] == n and sh['f'].startswith('from_wechat/'):
            im = rpill('📱 filmed by a friend', 30, bg=(16, 17, 22, 170), pad=(20, 8))
            L.append(span(im, 50 + im.width / 2, BAR + 50, sh['t'] - t0, sh['t'] - t0 + sh['d']))
    render(L, d, f'{OUT}/{n:02d}.mov')
    print(n, nm, len(L), file=sys.stderr)

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
render(L, dur, f'{OUT}/end.mp4', bg=bg)
print('end card', file=sys.stderr)
