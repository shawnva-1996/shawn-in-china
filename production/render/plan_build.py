"""Render Shawn in China ep. 1 from cleaned VO decisions + EDL.
usage: render.py <workdir> [--preview] [--only P05,P06]
workdir contains: vo_raw.wav, vo/decisions.json, vo/chunks.json, vo/transcripts.json,
                  media/<day folder>/<file>, media/meta.json (per-file probe), music/*.wav
"""
import json, os, sys, subprocess, math, random, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl import P
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WD = sys.argv[1]; PREVIEW = '--preview' in sys.argv
ONLY = None
if '--only' in sys.argv: ONLY = set(sys.argv[sys.argv.index('--only') + 1].split(','))
W, H, FPS = (960, 540, 30) if PREVIEW else (1920, 1080, 30)
SEG = f'{WD}/seg_{"p" if PREVIEW else "f"}'; os.makedirs(SEG, exist_ok=True)
GFX = f'{WD}/gfx_{W}'; os.makedirs(GFX, exist_ok=True)
MEDIA = f'{WD}/media'
SHOTLOG = '/home/claude/shawn-in-china/production/shot_log.csv'
ANTON = '/tmp/claude-0/-home-claude-shawn-in-china/10d1323e-8869-5514-b249-eccbe2bba9bf/scratchpad/th/Anton.ttf'
INTER = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
INTERB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
CJK = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
YEL = (255, 212, 0)
meta = json.load(open('/mnt/user-data/uploads/shawn-in-china/_work/render/meta.json'))
DEV = '{HOME}/mnt/shawn-in-china'          # device paths, expanded by the runner
KIT = DEV + '/_work/render'
IMG = '{HOME}/img'
TRIMS = {'14 Oct/IMG_8580.MOV': [0, 38, 58, 118, 198], '14 Oct/IMG_8613.MOV': [8], '14 Oct/IMG_8583.MOV': [20], '16 Oct/IMG_8916.MOV': [18, 38, 68, 93]}
for f, ws in TRIMS.items():
    meta[f] = dict(meta[f'_work/trims/{f.split("/")[1][:-4]}_{ws[0]}.mov'], trims=ws)
def resolve(f, st):
    if f in TRIMS:
        ws = [w for w in TRIMS[f] if w <= st + 0.01] or [TRIMS[f][0]]
        w = ws[-1]; return f'_work/trims/{f.split("/")[1][:-4]}_{w}.mov', max(0.0, st - w)
    return f, st
DGFX = KIT + f'/gfx_{W}'
run = lambda c: subprocess.run(c, check=True, capture_output=True)

# ---------- 1. VO assembly ----------
dec = json.load(open(f'{WD}/vo/decisions.json'))
chunks = json.load(open(f'{WD}/vo/chunks.json'))['chunks']
tr = json.load(open(f'{WD}/vo/transcripts.json'))
kept = sorted([c for c in dec['chunks'] if c.get('keep')], key=lambda c: c['i'])
pid = [p['id'] for p in P]
# enforce non-decreasing paragraph order
last = 0
for c in kept:
    k = pid.index(c['para']) if c.get('para') in pid else last
    if k < last: k = last
    c['para'] = pid[k]; last = k
NAT = {p['id']: p['nat'] for p in P if p.get('nat')}
PARA_GAP, SENT_GAP_MIN, SENT_GAP_MAX = 0.55, 0.18, 0.5
pieces, t = [], 0.6           # 0.6 s of drone-show air before the first line
ptimes = {}                   # para -> [start, end] on the master timeline
subs = []
prev_para, prev_end_src = None, None
for c in kept:
    a, b = chunks[c['i']]
    if prev_para is not None:
        if c['para'] != prev_para:
            t += PARA_GAP
            if prev_para in NAT: t += NAT[prev_para][1]; ptimes[prev_para][1] = t - PARA_GAP / 2
        else:
            gap = a - prev_end_src
            t += min(SENT_GAP_MAX, max(SENT_GAP_MIN, gap))
    ptimes.setdefault(c['para'], [t, t])
    pieces.append((a, b, t)); subs.append((t, t + (b - a), tr[str(c['i'])]))
    t += b - a; ptimes[c['para']][1] = t
    prev_para, prev_end_src = c['para'], b
if prev_para in NAT: t += NAT[prev_para][1]; ptimes[prev_para][1] = t
END_CARD = 8.0
TOTAL = t + 1.0 + END_CARD
# paragraphs with no kept VO still get a slot of 0 length -> skipped
order = [p for p in P if p['id'] in ptimes and (ONLY is None or p['id'] in ONLY)]
# extend each paragraph to the start of the next so video is continuous
ids = [p['id'] for p in P if p['id'] in ptimes]
for j, k in enumerate(ids):
    ptimes[k][0] = 0.0 if j == 0 else ptimes[k][0] - PARA_GAP / 2
    ptimes[k][1] = (ptimes[ids[j + 1]][0] - PARA_GAP / 2) if j + 1 < len(ids) else TOTAL - END_CARD
json.dump(dict(ptimes=ptimes, total=TOTAL), open(f'{WD}/timeline.json', 'w'), indent=1)

if not os.path.exists(f'{WD}/vo_clean.wav') or '--revo' in sys.argv:
    # cut + place each kept chunk with 15 ms fades, then clean up the voice
    fl, inputs = [], []
    for n, (a, b, at) in enumerate(pieces):
        fl.append(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={b-a-0.03:.3f}:d=0.03,adelay={int(at*1000)}:all=1[v{n}]')
    fl.append(''.join(f'[v{n}]' for n in range(len(pieces))) + f'amix=inputs={len(pieces)}:normalize=0,apad=whole_dur={TOTAL:.3f},'
              'highpass=f=80,afftdn=nr=12:nf=-40,equalizer=f=6500:t=q:w=2:g=-3,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,'
              'loudnorm=I=-16:TP=-1.5:LRA=7[vo]')
    open(f'{WD}/vo_filter.txt', 'w').write(';\n'.join(fl))
    run(['ffmpeg', '-y', '-nostdin', '-i', f'{WD}/vo_raw.wav', '-filter_complex_script', f'{WD}/vo_filter.txt', '-map', '[vo]', '-ar', '48000', '-ac', '1', f'{WD}/vo_clean.wav'])
    # captions
    def ts(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f'{int(h):02}:{int(m):02}:{s:06.3f}'.replace('.', ',')
    with open(f'{WD}/captions_en.srt', 'w') as f:
        for n, (a, b, txt) in enumerate(subs, 1):
            txt = re.sub(r'\b(um+|uh+)\b,?\s*', '', txt, flags=re.I).strip()
            f.write(f'{n}\n{ts(a)} --> {ts(b)}\n{txt}\n\n')
if '--vo-only' in sys.argv: sys.exit()

# ---------- 2. shot planning ----------
rows = list(csv.DictReader(open(SHOTLOG)))
def pool(day, t0, t1):
    out = []
    for r in rows:
        if r['day'] != day or not (t0 <= r['local_time'][-8:-3] <= t1): continue
        f = f"{day}/{r['file']}"
        if f not in meta: continue
        q = int(r['ai_quality'] or 3) if r['type'] == 'video' else 3
        if r['type'] == 'video' and (q < 3 or r['ai_best_use'] == 'skip'): continue
        out.append(f)
    return out
def clip_len(f): return meta[f]['dur'] if meta[f]['kind'] == 'video' else 99
def parse(s):
    if s == 'MAP': return ('MAP', 0)
    f, _, st = s.partition('@'); return resolve(f, float(st or 0))
TARGET, MINS, MAXS = 3.2, 1.6, 5.5
plan = []
used_global = set()
for p in P:
    if p['id'] not in ptimes: continue
    a, b = ptimes[p['id']]
    nat = NAT.get(p['id'])
    D = b - a - (nat[1] if nat else 0)
    shots = [parse(s) for s in p['shots'] if s == 'MAP' or s.partition('@')[0] in meta]
    extra = []
    for key in ('pool', 'pool2'):
        if p.get(key): extra += [resolve(f, 0) for f in pool(*p[key]) if resolve(f, 0)[0] not in [s[0] for s in shots]]
    n = max(1, round(D / TARGET))
    random.Random(p['id']).shuffle(extra)
    extra.sort(key=lambda s: s[0] in used_global)   # prefer unused footage
    while len(shots) < n and extra: shots.append(extra.pop(0))
    while len(shots) > 1 and D / len(shots) < MINS: shots.pop()
    if p.get('pool') and len(shots) > 1 and not p['shots']:
        shots.sort(key=lambda s: s[0])              # pool-only paragraphs play chronologically
    # durations: equal split, capped by available clip length, leftover redistributed
    durs = [D / len(shots)] * len(shots)
    for _ in range(4):
        cap = [min(MAXS * 1.6, max(0.8, clip_len(f) - st - 0.1)) if f != 'MAP' else 7 for f, st in shots]
        over = sum(max(0, d - c) for d, c in zip(durs, cap))
        durs = [min(d, c) for d, c in zip(durs, cap)]
        free = [i for i in range(len(durs)) if durs[i] < cap[i] - 0.05]
        if over < 0.01 or not free: break
        for i in free: durs[i] += over / len(free)
    if sum(durs) < D - 0.05:  # not enough footage: loop the list
        k = 0
        while sum(durs) < D - 0.05:
            f, st = shots[k % len(shots)]; c = min(MAXS, clip_len(f) - st - 0.1) if f != 'MAP' else 5
            add = min(c, D - sum(durs)); shots.append((f, st)); durs.append(max(0.8, add)); k += 1
    durs[-1] += D - sum(durs)
    tt = a
    for (f, st), d in zip(shots, durs):
        # long clips with no explicit in-point: start from the middle-ish
        if f != 'MAP' and st == 0 and meta[f]['kind'] == 'video' and clip_len(f) > d + 2:
            st = max(0, (clip_len(f) - d) * 0.35)
        plan.append(dict(para=p['id'], f=f, st=st, d=d, t=tt, nat=False)); tt += d
        used_global.add(f)
    if nat:
        f, st = parse(nat[0])
        plan.append(dict(para=p['id'], f=f, st=st, d=nat[1], t=tt, nat=True)); tt += nat[1]
plan.append(dict(para='END', f=P[-1]['shots'][0].partition('@')[0], st=8, d=END_CARD + 1.0, t=TOTAL - END_CARD - 1.0, nat=False, end=True))
json.dump(plan, open(f'{WD}/plan.json', 'w'), indent=1)

# ---------- 3. graphics ----------
def font(p, s): return ImageFont.truetype(p, s)
def lower_third(text, path):
    s = W / 1920
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(INTERB, int(44 * s))
    if re.search(r'[一-鿿]', text): f = font(CJK, int(44 * s))
    tw = d.textlength(text, font=f); pad = int(28 * s)
    x0, y1 = int(80 * s), H - int(110 * s); y0 = y1 - int(84 * s)
    d.rounded_rectangle([x0, y0, x0 + tw + 2 * pad + int(14 * s), y1], radius=int(14 * s), fill=(15, 15, 18, 215))
    d.rectangle([x0, y0, x0 + int(10 * s), y1], fill=YEL + (255,))
    d.text((x0 + int(14 * s) + pad, (y0 + y1) // 2), text, font=f, fill='white', anchor='lm')
    im.save(path)
def chapter_card(text, path):
    s = W / 1920
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    a, _, b = text.partition(' · ')
    f1, f2 = font(ANTON, int(120 * s)), font(INTERB, int(46 * s))
    d.text((int(80 * s), int(110 * s)), a, font=f1, fill=YEL, stroke_width=int(6 * s), stroke_fill='black')
    if b: d.text((int(86 * s), int(270 * s)), b.upper(), font=f2, fill='white', stroke_width=int(4 * s), stroke_fill='black')
    im.save(path)
def title_card(path):
    s = W / 1920
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((W // 2, int(H * 0.74)), 'SHAWN IN CHINA', font=font(ANTON, int(150 * s)), fill='white', stroke_width=int(8 * s), stroke_fill='black', anchor='mm')
    d.text((W // 2, int(H * 0.74) + int(115 * s)), 'EP. 1 · CHONGQING', font=font(INTERB, int(48 * s)), fill=YEL, stroke_width=int(4 * s), stroke_fill='black', anchor='mm')
    im.save(path)
def map_card(path):
    s = W / 1920
    im = Image.new('RGB', (W, H), (14, 18, 28)); d = ImageDraw.Draw(im)
    # stylised China outline-free diagram: east-coast cities -> Chongqing
    east = [('Beijing', 1430, 330), ('Shanghai', 1540, 600), ('Shenzhen', 1360, 860)]
    cq = ('Chongqing', 760, 640)
    def P_(x, y): return (int(x * s), int(y * s))
    for name, x, y in east:
        d.line([P_(x, y), P_(cq[1], cq[2])], fill=(255, 212, 0), width=max(2, int(6 * s)))
    for name, x, y in east:
        d.ellipse([P_(x - 18, y - 18), P_(x + 18, y + 18)], fill=(90, 170, 255))
        d.text(P_(x + 34, y), name, font=font(INTERB, int(44 * s)), fill='white', anchor='lm')
    d.ellipse([P_(cq[1] - 34, cq[2] - 34), P_(cq[1] + 34, cq[2] + 34)], fill=YEL)
    d.text(P_(cq[1] - 50, cq[2]), 'Chongqing', font=font(INTERB, int(52 * s)), fill=YEL, anchor='rm')
    d.text(P_(cq[1] - 50, cq[2] + 62), 'data centres', font=font(INTER, int(38 * s)), fill='white', anchor='rm')
    d.text(P_(1500, 255), 'DEMAND IN THE EAST', font=font(INTERB, int(40 * s)), fill=(150, 200, 255), anchor='mm')
    d.text(P_(W / s / 2, 110), 'EAST DATA, WEST COMPUTING', font=font(ANTON, int(96 * s)), fill='white', anchor='mm')
    d.text(P_(W / s / 2, 205), '东数西算', font=font(CJK, int(54 * s)), fill=YEL, anchor='mm')
    im.save(path)
def end_card(path):
    s = W / 1920
    im = Image.new('RGBA', (W, H), (0, 0, 0, 150)); d = ImageDraw.Draw(im)
    d.text((W // 2, int(330 * s)), 'SHAWN IN CHINA', font=font(ANTON, int(150 * s)), fill='white', anchor='mm')
    d.text((W // 2, int(470 * s)), 'NP Travel & Learn to Chongqing · link in description', font=font(INTERB, int(46 * s)), fill=YEL, anchor='mm')
    d.rounded_rectangle([W // 2 - int(220 * s), int(580 * s), W // 2 + int(220 * s), int(680 * s)], radius=int(16 * s), fill=(230, 30, 40))
    d.text((W // 2, int(630 * s)), 'SUBSCRIBE', font=font(INTERB, int(52 * s)), fill='white', anchor='mm')
    d.text((W // 2, int(780 * s)), 'Leave your Chongqing questions in the comments', font=font(INTER, int(40 * s)), fill='white', anchor='mm')
    im.save(path)
GF = {}
for p in P:
    for key in ('card', 'chapter'):
        if p.get(key):
            path = f"{GFX}/{p['id']}_{key}.png"
            (lower_third if key == 'card' else chapter_card)(p[key], path); GF[(p['id'], key)] = path
title_card(f'{GFX}/title.png'); map_card(f'{GFX}/map.png'); end_card(f'{GFX}/end.png')

# ---------- 4. per-shot render ----------
HLG = "zscale=t=linear:npl=100:tin=arib-std-b67:min=bt2020nc:pin=bt2020,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
def vchain(f, d):
    m = meta[f]; tm = ''
    if m['kind'] == 'image' and m['h'] > m['w'] * 1.1:
        return (f"scale=-2:{H},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bg];"
                f"[bg][b]overlay=(W-w)/2:0,fps={FPS},format=yuv420p")
    if m['kind'] == 'image':
        z = 1.0 + 0.08
        return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                f"zoompan=z='min(zoom+{0.08/(d*FPS):.5f},{z})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(d*FPS)+2}:s={W}x{H}:fps={FPS},format=yuv420p")
    rot = m.get('rot', 0)
    w, h = (m['h'], m['w']) if abs(rot) in (90, 270) else (m['w'], m['h'])
    if h > w * 1.1:   # vertical: blurred fill behind
        return (f"{tm}scale=-2:{H},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bg];"
                f"[bg][b]overlay=(W-w)/2:0,fps={FPS},format=yuv420p")
    return f"{tm}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p"
def overlays_for(sh):
    out = []
    p = sh['para']; rel0 = sh['t'] - ptimes[p][0] if p in ptimes else 0
    if (p, 'chapter') in GF and rel0 < 0.01: out.append((GF[(p, 'chapter')], 0.2, min(3.2, sh['d'] - 0.1)))
    if (p, 'card') in GF:
        # show card once, on the shot covering paragraph start + 1.0 s
        st = ptimes[p][0] + (3.4 if (p, 'chapter') in GF else 1.0)
        if sh['t'] <= st < sh['t'] + sh['d']:
            out.append((GF[(p, 'card')], st - sh['t'], min(4.5, sh['t'] + sh['d'] - st)))
    if p == 'P04' and rel0 < 0.01: out.append((f'{GFX}/title.png', 0.3, sh['d'] - 0.3))
    if sh.get('end'): out.append((f'{GFX}/end.png', 1.0, sh['d'] - 1.0))
    return out
jobs = []
for n, sh in enumerate(plan):
    d = sh['d']; out = f'{{SEG}}/{n:04d}.mov'
    if sh['f'] == 'MAP':
        cmd = ['ffmpeg', '-y', '-nostdin', '-v', 'error', '-loop', '1', '-t', f'{d:.3f}', '-i', f'{DGFX}/map.png', '-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo',
               '-filter_complex', f"[0:v]fps={FPS},format=yuv420p,fade=t=in:d=0.3[v]", '-map', '[v]', '-map', '1:a']
    else:
        m = meta[sh['f']]
        if m['kind'] == 'video':
            ins = ['-ss', f"{sh['st']:.3f}", '-t', f'{d + 0.05:.3f}', '-i', f"{DEV}/{sh['f']}"]
        else:
            ins = ['-loop', '1', '-t', f'{d:.3f}', '-i', f"{IMG}/{sh['f'].replace('/', '_')}"]
        ov = overlays_for(sh)
        fc = f"[0:v]{vchain(sh['f'], d)}[v0]"
        for k, (png, a0, dd) in enumerate(ov):
            ins += ['-loop', '1', '-framerate', str(FPS), '-t', f'{dd:.3f}', '-i', png.replace(GFX, DGFX)]
            fc += f";[{k+1}:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={max(0.3, dd-0.3):.2f}:d=0.25:alpha=1,setpts=PTS+{a0:.3f}/TB[g{k}];[v{k}][g{k}]overlay=eof_action=pass:format=auto[v{k+1}]"
        fc += f";[v{len(ov)}]null[v]"
        if m.get('audio'):
            gain = 1.0 if sh['nat'] else (0.10 if sh['f'].startswith('from_wechat') else 0.22)
            fc += f";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain},apad,afade=t=in:d=0.08,afade=t=out:st={max(0, d-0.1):.3f}:d=0.1[a]"
            amap = ['-map', '[a]']
        else:
            amap = ['-map', f'{len(ov)+1}:a']; ins += ['-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']
        cmd = ['ffmpeg', '-y', '-nostdin', '-v', 'error'] + ins + ['-filter_complex', fc, '-map', '[v]'] + amap
    cmd += ['-t', f'{d:.3f}', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'veryfast' if PREVIEW else 'medium', '-crf', '26' if PREVIEW else '19', '-threads', '2',
            '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', out]
    jobs.append(dict(n=n, out=out, cmd=cmd, para=sh['para'], f=sh['f'], d=round(d, 2)))
imgs = sorted({sh['f'] for sh in plan if sh['f'] != 'MAP' and meta[sh['f']]['kind'] == 'image'})
json.dump(dict(jobs=jobs, images=[[f"{DEV}/{f}", f"{IMG}/{f.replace('/', '_')}"] for f in imgs], seg=f'{{SEG}}', total=TOTAL,
               switch=ptimes.get('P33', [TOTAL * 0.85])[0]), open(f'{WD}/jobs_{W}.json', 'w'), indent=0)
print(len(jobs), 'jobs,', len(imgs), 'images, total', round(TOTAL, 1), 's', file=sys.stderr)
sys.exit()
# ---------- 5. concat + mix ----------
with open(f'{SEG}/list.txt', 'w') as f:
    for n in range(len(plan)): f.write(f"file '{SEG}/{n:04d}.mp4'\n")
run(['ffmpeg', '-y', '-nostdin', '-f', 'concat', '-safe', '0', '-i', f'{SEG}/list.txt', '-c', 'copy', f'{WD}/pic_{W}.mov'])
# music: upbeat bed, reflective bed from P33 on; drone show plays bed louder before first VO
mus = sorted(os.listdir(f'{WD}/music'))
up = f'{WD}/music/upbeat.wav'; calm = f'{WD}/music/calm.wav' if os.path.exists(f'{WD}/music/calm.wav') else up
sw = ptimes.get('P33', [TOTAL * 0.85])[0]
fc = (f"[2:a]aloop=loop=-1:size=2e9,atrim=0:{sw+2:.3f},afade=t=out:st={sw:.3f}:d=2[m1];"
      f"[3:a]aloop=loop=-1:size=2e9,atrim=0:{TOTAL-sw+1:.3f},afade=t=in:d=2,afade=t=out:st={TOTAL-sw-3:.3f}:d=3,adelay={int(sw*1000)}:all=1[m2];"
      f"[m1][m2]amix=inputs=2:normalize=0,volume=0.55,aformat=channel_layouts=stereo[mus];"
      f"[1:a]aformat=channel_layouts=stereo,asplit=3[vo1][vo2][vo3];"
      f"[mus][vo1]sidechaincompress=threshold=0.02:ratio=8:attack=80:release=600:makeup=1[mduck];"
      f"[0:a][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=50:release=400[nat];"
      f"[vo3][nat][mduck]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=9[a]")
outname = f'{WD}/shawn_in_china_ep1_{"preview" if PREVIEW else "final"}.mp4'
run(['ffmpeg', '-y', '-nostdin', '-i', f'{WD}/pic_{W}.mov', '-i', f'{WD}/vo_clean.wav', '-i', up, '-i', calm,
     '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-shortest', outname])
print('done', outname, file=sys.stderr)
