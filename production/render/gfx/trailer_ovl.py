"""9:16 overlays for the trailer: word-group captions in the Reels safe zone, the opening hook, stickers and
location tags carried over from the main edit, the friend-footage credit, and a full-screen end card that
sends viewers to the long video.
usage: trailer_ovl.py <workdir> <thumbnail.jpg>     reads trailer.json, writes tovl/<n>.mov and tovl/end.mp4
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motion
motion.W, motion.H = 1080, 1920
from motion import Layer, render, big_text, rich, rpill, font, ImageDraw, Image, ANTON, INTERB, INTERX, YEL, INK
from sticker import emoji
W, H = motion.W, motion.H
WD, THUMB = sys.argv[1:3]
T = json.load(open(f'{WD}/trailer.json')); OUT = f'{WD}/tovl'; os.makedirs(OUT, exist_ok=True)
CAP_Y = 1240                      # caption centre: above the Reels/TikTok bottom UI, below the face area
FIX = {'Sean': 'Shawn', 'Haifu': 'HIFU'}

def chunks(words, seg_end):
    """group words into 1–3 word captions; break after punctuation"""
    out, cur = [], []
    for w, t in words:
        if cur and t - cur[-1][1] > 0.55: out.append(cur); cur = []      # a pause in the VO ends a caption
        cur.append((w, t))
        if len(cur) == 3 or re.search(r'[.,?!]$', w) or sum(len(x) + 1 for x, _ in cur) > 15:
            out.append(cur); cur = []
    if cur: out.append(cur)
    k = 0
    while k < len(out) - 1:            # don't leave "A" / "THE" alone on screen
        if len(out[k]) == 1 and len(out[k][0][0]) <= 3: out[k:k + 2] = [out[k] + out[k + 1]]
        else: k += 1
    res = []
    for k, c in enumerate(out):
        t0 = c[0][1]; t1 = out[k + 1][0][1] if k + 1 < len(out) else min(seg_end, c[-1][1] + 0.9)
        txt = ' '.join(FIX.get(w.strip('.,?!'), w) for w, _ in c).upper().rstrip(',')
        res.append((txt, t0, max(t0 + 0.2, t1)))
    return res

def caption(txt):
    words = txt.split(); im = big_text(txt, 92, 'white', 9)
    if im.width > W - 120: im = im.resize((W - 120, int(im.height * (W - 120) / im.width)), Image.LANCZOS)
    return im

def friend():
    return rpill('📱 filmed by a friend', 30, bg=(16, 17, 22, 170), pad=(20, 8))

for n, s in enumerate(T['segs']):
    t0, d = s['t'], s['d']; L = []
    for txt, a, b in chunks(s['words'], t0 + d):
        im = caption(txt); blank = Image.new('RGBA', (1, 1)); life = b - a
        L.append(Layer(lambda t, im=im, life=life: im if t < life else blank, W / 2, CAP_Y, a - t0 - 0.02, 'pop', 0.12))   # hard cut to the next caption
    side = 1
    for f in s['fx']:
        at = max(0.0, f['t'] - t0)
        if f['kind'] == 'sticker':
            im = emoji(f['arg'], 190, 9); x = W - 190 if side > 0 else 190; side = -side
            L.append(Layer(im, x, 640, at, 'pop', 0.4, min(d - 0.2, at + 2.4), wiggle=True, rot=6 * side))
        elif f['kind'] == 'loc':
            im = rpill('📍 ' + f['arg'], 40, accent=YEL)
            if im.width > W - 100: im = im.resize((W - 100, int(im.height * (W - 100) / im.width)), Image.LANCZOS)
            L.append(Layer(im, W / 2, 330, at, 'slide-up', 0.35, min(d - 0.2, at + 3.0)))
    for sh in s['shots']:
        if sh['f'].startswith('from_wechat/'):
            im = friend(); L.append(Layer(im, 60 + im.width / 2, 220, sh['t'] - t0 + 0.2, 'fade', 0.3, sh['t'] - t0 + sh['d'] - 0.25))
    if n == 0:   # the hook
        L.append(Layer(big_text('NOT CGI.', 230, 'white', 12), W / 2, 760, 0.05, 'pop', 0.35))
    if n == 1:
        L.append(Layer(big_text('6 DAYS IN CHONGQING', 104, YEL, 8), W / 2, 380, 0.1, 'slide-up', 0.4, d - 0.3))
    render(L, d, f'{OUT}/{n:02d}.mov')
    print(n, s['beat'], len(L), file=sys.stderr)

# end card
a, dur = T['end']
th = Image.open(THUMB).convert('RGBA'); th = th.resize((940, int(th.height * 940 / th.width)), Image.LANCZOS)
m = Image.new('L', th.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, th.width - 1, th.height - 1], 28, fill=255); th.putalpha(m)
bg = Image.new('RGBA', (W, H), (12, 13, 18, 255))
L = [Layer(big_text('WATCH THE', 120, 'white', 8), W / 2, 420, 0.0, 'pop', 0.35),
     Layer(big_text('FULL VIDEO', 150, YEL, 9), W / 2, 560, 0.15, 'pop', 0.35),
     Layer(th, W / 2, 940, 0.35, 'slide-up', 0.45),
     Layer(rich('Chongqing Isn’t Real… So I Went Inside', 50, 'white', INTERX), W / 2, 1290, 0.6, 'fade', 0.4),
     Layer(rpill('▶  YouTube · Shawnlemuel', 48, fg='white', bg=(230, 33, 40, 255), pad=(34, 14)), W / 2, 1420, 0.9, 'pop', 0.35),
     Layer(rpill('🔗 link in bio', 44, fg=INK, bg=YEL + (255,), pad=(30, 12)), W / 2, 1530, 1.2, 'pop', 0.35)]
render(L, dur, f'{OUT}/end.mp4', bg=bg)
print('end card', file=sys.stderr)
