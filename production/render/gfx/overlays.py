"""Build one transparent overlay clip per beat from timeline2.json: chapter cards, stickers, pills,
location tags, kinetic headlines, counters, the 8D card, the spice meter, title, end card and the
'filmed by a friend' credit on WeChat clips. Full-screen viz shots (VIZ:map) are rendered here too.
usage: overlays.py <workdir> [beat ids...]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion import *
from sticker import emoji, die_cut
import mapviz
WD = sys.argv[1]; ONLY = set(sys.argv[2:])
T = json.load(open(f'{WD}/timeline2.json'))
OUT = f'{WD}/ovl'; os.makedirs(OUT, exist_ok=True)
TOPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'land-50m.json')   # world-atlas (Natural Earth)
NAMED = dict(tl=('l', 'top'), tr=('r', 'top'), bl=('l', 'bot'), br=('r', 'bot'), tc=('c', 'top'), bc=('c', 'bot'), c=('c', 'mid'))
def place(im, pos):
    if isinstance(pos, (list, tuple)): return pos
    hx, vy = NAMED[pos]
    x = {'l': 90 + im.width / 2, 'r': W - 90 - im.width / 2, 'c': W / 2}[hx]
    y = {'top': 110 + im.height / 2, 'bot': H - 120 - im.height / 2, 'mid': H / 2}[vy]
    return x, y
def chapter_img(text):
    a, _, b = text.partition(' · ')
    t1 = big_text(a, 150, YEL, 8); t2 = rich(b.upper(), 50, 'white', INTERX, stroke=4) if b else None
    im = Image.new('RGBA', (max(t1.width, t2.width if t2 else 0) + 20, t1.height + (t2.height + 6 if t2 else 0)), (0, 0, 0, 0))
    im.alpha_composite(t1, (0, 0))
    if t2: im.alpha_composite(t2, (10, t1.height + 6))
    return im
def counter_layers(value, fmt, label, t0, out):
    L = [Layer(Image.new('RGBA', (1, 1)), 0, 0)]
    panel = Image.new('RGBA', (1300, 420), (0, 0, 0, 0)); ImageDraw.Draw(panel).rounded_rectangle([0, 0, 1299, 419], 40, fill=(12, 14, 20, 175))
    L = [Layer(panel, W / 2, H / 2 - 10, t0, 'fade', 0.3, out)]
    L.append(Layer(counter(value, 1.1 if value < 1000 else 1.6, 190, fmt), W / 2, H / 2 - 60, t0, 'pop', 0.4, out))
    L.append(Layer(rich(label, 54, 'white', INTERX), W / 2, H / 2 + 115, t0 + 0.3, 'slide-up', 0.4, out))
    return L
def eightd_layers(t0, out):
    L = [Layer(big_text('8D', 300, YEL, 12), W / 2, H / 2 - 90, t0, 'pop', 0.45, out)]
    for k, s in enumerate(['⛰️ mountains', '🌊 two rivers', '🚫 flat ground']):
        L.append(Layer(rpill(s, 50), W / 2 - 520 + k * 520, H / 2 + 170, t0 + 0.35 + k * 0.3, 'pop', 0.4, out))
    return L
def spice_layers(t0, out):
    L = [Layer(rpill('SPICE LEVEL', 44, fg=INK, bg=YEL + (255,)), W / 2, 150, t0, 'pop', 0.35, out)]
    for k in range(5):
        L.append(Layer(emoji('🌶️', 130, 7), W / 2 - 340 + k * 170, 300, t0 + 0.15 + k * 0.12, 'pop', 0.35, out))
    L.append(Layer(big_text('VERY.', 120, (255, 80, 60), 7), W / 2, 460, t0 + 0.9, 'pop', 0.4, out))
    return L
def title_layers(t0, out):
    return [Layer(big_text('SHAWN IN CHINA', 170, 'white', 9), W / 2, H * 0.72, t0, 'pop', 0.45, out),
            Layer(rich('EP. 1 · CHONGQING 重庆', 54, YEL, INTERX, stroke=4), W / 2, H * 0.72 + 125, t0 + 0.3, 'slide-up', 0.4, out)]
def endcard_layers(t0):
    shade = Image.new('RGBA', (W, H), (8, 10, 16, 165))
    L = [Layer(shade, W / 2, H / 2, t0, 'fade', 0.6)]
    L.append(Layer(big_text('SHAWN IN CHINA', 150, 'white', 8), W / 2, 190, t0 + 0.2, 'pop', 0.45))
    L.append(Layer(rpill('🎓 NP Travel & Learn to Chongqing · link in the description', 44, fg=INK, bg=YEL + (255,)), W / 2, 330, t0 + 0.5, 'slide-up'))
    sub = Image.new('RGBA', (430, 104), (0, 0, 0, 0)); d = ImageDraw.Draw(sub); d.rounded_rectangle([0, 0, 429, 103], 20, fill=(230, 33, 40, 255))
    d.text((215, 52), 'SUBSCRIBE', font=font(INTERX, 54), fill='white', anchor='mm')
    L.append(Layer(sub, W / 2, 900, t0 + 0.8, 'pop'))
    L.append(Layer(rich('💬 Drop your Chongqing questions in the comments', 40, 'white', INTERB), W / 2, 1010, t0 + 1.1, 'fade'))
    return L
def friend_tag():
    return rpill('📱 filmed by a friend', 30, bg=(16, 17, 22, 170), pad=(20, 8))

beats = {b['id']: b for b in T['beats']}
for b in T['beats']:
    if ONLY and b['id'] not in ONLY: continue
    a0, a1 = b['span']; dur = a1 - a0
    L = []; slots = {}
    items = sorted([f for f in T['fx'] if f['beat'] == b['id'] and f['kind'] != 'sfx'], key=lambda f: f['t'])
    for k, f in enumerate(items):
        t0 = max(0.0, f['t'] - a0); kind = f['kind']; ex = f.get('extra', [])
        end_all = dur - 0.25
        if kind == 'chapter':
            im = chapter_img(f['text']); L.append(Layer(im, 110 + im.width / 2, H * 0.42, t0, 'slide-right', 0.45, min(end_all, t0 + 3.0)))
        elif kind in ('pill', 'loc'):
            if kind == 'loc':
                im = rpill('📍 ' + f['arg'], 44, accent=YEL); pos = (110 + im.width / 2, H - 150 - im.height / 2); out = min(end_all, t0 + 4.0); anim = 'slide-right'
            else:
                im = rpill(f['arg'], 46); pos = place(im, ex[0] if ex else 'bc'); out = end_all; anim = 'pop'
            key = str(ex[0]) if (kind == 'pill' and ex and isinstance(ex[0], str)) else None
            if key and key in slots: slots[key].out = min(slots[key].out or 1e9, t0)
            lay = Layer(im, pos[0], pos[1], t0, anim, 0.4, out)
            if key: slots[key] = lay
            L.append(lay)
        elif kind == 'sticker':
            im = emoji(f['arg'], 170, 9); pos = place(im, ex[0] if ex else 'tr')
            L.append(Layer(im, pos[0], pos[1], t0, 'pop', 0.45, min(end_all, t0 + 2.6), wiggle=True, rot=-6 if k % 2 else 6))
        elif kind == 'big':
            im = big_text(f['arg'], 190, YEL if f['arg'] != 'NOT CGI.' else 'white', 10)
            L.append(Layer(im, W / 2, H / 2, t0, 'pop', 0.4, min(end_all, t0 + (2.6 if f['arg'] == 'NOT CGI.' else 1.7))))
        elif kind == 'count':
            L += counter_layers(f['arg'], ex[1] if len(ex) > 1 else '{:,.0f}', ex[0], t0, min(end_all, t0 + 4.2))
        elif kind == 'eightd': L += eightd_layers(t0, min(end_all, t0 + 3.6))
        elif kind == 'spice': L += spice_layers(t0, min(end_all, t0 + 3.4))
        elif kind == 'title': L += title_layers(t0, end_all)
        elif kind == 'endcard': L += endcard_layers(t0)
    for s in T['shots']:
        if s['beat'] == b['id'] and s['f'].startswith('from_wechat/'):
            im = friend_tag(); L.append(Layer(im, W - 70 - im.width / 2, H - 60 - im.height / 2, s['t'] - a0 + 0.3, 'fade', 0.3, s['t'] - a0 + s['d'] - 0.3))
        if s['beat'] == b['id'] and s['f'] == 'VIZ:map':
            words = [w for p in b['pieces'] for w in p['words']]
            def wt(w, d, after=0.0):
                for x, t in words:
                    if t - s['t'] >= after and x.lower().strip(',.?').startswith(w): return t - s['t'] - 0.1
                return d
            tc = wt('richest', 3.0); td = wt('demand', 6.0, tc); tw = wt('land', 8.8, td)
            mapviz.build(TOPO, f'{OUT}/viz_map.mp4', s['d'], tc, td, tw)
            print('viz_map', round(tc, 2), round(td, 2), round(tw, 2), file=sys.stderr)
    if L:
        render(L, dur, f'{OUT}/{b["id"]}.mov')
        print(b['id'], round(dur, 2), len(L), 'layers', file=sys.stderr)
