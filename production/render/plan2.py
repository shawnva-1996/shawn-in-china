"""Plan the v2 edit: assemble the clean VO in beat order, time every shot to the word it is cued on,
and write the shot list, sound-effect cues, captions and chapter times.
usage: plan2.py <workdir>
workdir: vo_raw.wav, vo/chunks.json, vo/tx.json, vo/verify.json, meta.json (probe of every clip)
writes:  timeline2.json (beats, shots, fx with absolute times), captions_en.srt, chapters.txt, vo_pieces.json
"""
import json, os, re, sys, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edl2 import B
WD = sys.argv[1]
chunks = json.load(open(f'{WD}/vo/chunks.json'))['chunks']
tx = json.load(open(f'{WD}/vo/tx.json'))
ver = json.load(open(f'{WD}/vo/verify.json')) if os.path.exists(f'{WD}/vo/verify.json') else {}
meta = json.load(open(f'{WD}/meta.json'))
PRE_GAP, IN_BEAT_MIN, IN_BEAT_MAX, BEAT_GAP = 0.0, 0.15, 0.45, 0.4
LEAD = 0.12            # cut this long before the cue word starts
MIN_SHOT = 0.9

# ---------- speech envelope (10 ms RMS, dBFS) for exact speech bounds ----------
if not os.path.exists(f'{WD}/env.npy'):
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{WD}/vo_raw.wav', '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout, dtype=np.int16).astype(float)
    np.save(f'{WD}/env.npy', np.array([np.sqrt(np.mean(x[i:i + 160] ** 2) + 1) for i in range(0, len(x) - 160, 160)]))
db = 20 * np.log10(np.load(f'{WD}/env.npy') / 32768)
def speech_bounds(a, b, thr=-44):
    s = np.where(db[int(a * 100):int(b * 100)] > thr)[0]
    return (a + s[0] / 100, a + (s[-1] + 1) / 100) if len(s) else (a, b)
def onsets(a, b, thr=-40):
    s = db[int(a * 100):int(b * 100)] > thr
    return [a + k / 100 for k in range(1, len(s)) if s[k] and not s[k - 1]]

# ---------- VO pieces ----------
def piece(ref):
    if isinstance(ref, list):
        a, b = ref; text = None; words = None
        for k, (ca, cb) in enumerate(chunks):
            if ca <= a + 0.05 and b <= cb + 0.3: words = None
        text = "I'll answer the best ones." if abs(a - 591.03) < 0.01 else ''
        a, b = a - 0.06, b + 0.1
    else:
        a, b = chunks[ref]; v = ver.get(str(ref), {})
        text = (v.get('heard') if v and v.get('heard') and 'NO SPEECH' not in v.get('heard') else tx[str(ref)]['text']).strip()
        src_words = v.get('word_times') if v and v.get('heard') and 'NO SPEECH' not in v.get('heard') else tx[str(ref)].get('words')
        words = [w for w in (src_words or []) if isinstance(w, list) and len(w) >= 3 and all(isinstance(x, (int, float)) for x in w[1:3])]
    s0, s1 = speech_bounds(a, b)
    toks = text.split()
    # word times: Gemini's are often stretched, so rescale them into the measured speech span;
    # with none, spread words by character count
    if words and len(words) >= len(toks) * 0.6:
        w0, w1 = words[0][1], max(w[2] for w in words)
        sc = (s1 - s0) / max(0.1, w1 - w0)
        wt = [(w[0], s0 + (w[1] - w0) * sc) for w in words]
    else:
        tot = sum(len(t) + 1 for t in toks) or 1; acc = 0; wt = []
        for t in toks: wt.append((t, s0 + (s1 - s0) * acc / tot)); acc += len(t) + 1
    # snap each word start to a nearby speech onset (within 0.25 s)
    ons = onsets(a, b)
    snapped = []
    for w, t in wt:
        near = [o for o in ons if abs(o - t) < 0.25]
        snapped.append((w, min(near, key=lambda o: abs(o - t)) if near else t))
    return dict(src=[round(a, 3), round(b, 3)], speech=[s0, s1], text=text, words=snapped)

# ---------- timeline ----------
t = 0.0; beats = []; caps = []
for bi, b in enumerate(B):
    bt = dict(id=b['id'], start=t, pieces=[], cues=[])
    if b.get('pre'): t += b['pre']
    if not b['vo']:
        t += b['natsec']; bt['end'] = t; beats.append(bt); continue
    prev_src_end = None
    for ref in b['vo']:
        p = piece(ref)
        if prev_src_end is not None:
            t += min(IN_BEAT_MAX, max(IN_BEAT_MIN, p['src'][0] - prev_src_end))
        off = t - p['src'][0]
        p['at'] = t; p['words_t'] = [(w, wt + off) for w, wt in p['words']]
        bt['pieces'].append(p); caps.append((p['speech'][0] + off, p['speech'][1] + off, p['text']))
        t += p['src'][1] - p['src'][0]; prev_src_end = p['src'][1]
    t += BEAT_GAP if b['id'] != 'B70' else 0
    bt['end'] = t
    beats.append(bt)
END_CARD = 7.0
TOTAL = t + END_CARD
# beat spans: each beat's picture runs until the next beat starts
for k, bt in enumerate(beats):
    bt['span'] = [bt['start'], beats[k + 1]['start'] if k + 1 < len(beats) else TOTAL]

def find_word(bt, word, after):
    norm = lambda s: re.sub(r"[^\w:'-]", '', s.lower()).replace("’", "'")
    target = norm(word)
    for p in bt['pieces']:
        for w, wt in p['words_t']:
            if wt >= after - 0.01 and (norm(w) == target or norm(w).startswith(target)):
                return wt
    return None

def cue_time(bt, cue, after):
    if isinstance(cue, (int, float)): return bt['start'] + cue
    w = find_word(bt, cue.lstrip('~'), after)
    if w is None:
        print(f"!! {bt['id']}: cue '{cue}' not found in: {' '.join(p['text'] for p in bt['pieces'])}", file=sys.stderr)
    return w

# ---------- shots ----------
def clip_info(f):
    if f.startswith('VIZ:'): return dict(kind='viz', dur=99)
    return meta[f]
shots = []; problems = []
for b, bt in zip(B, beats):
    specs = []
    for s in b['shots']:
        spec, _, cue = s.partition(' ~')
        f, _, st = spec.partition('@')
        specs.append([f, st, cue])
    cuts = [bt['span'][0]]
    last = bt['span'][0]
    for f, st, cue in specs[1:]:
        ct = cue_time(bt, '~' + cue, last) if cue else None
        if ct is None: ct = last + 2.5
        ct = max(last + MIN_SHOT, ct - LEAD)
        cuts.append(ct); last = ct
    cuts.append(bt['span'][1])
    for k, (f, st, cue) in enumerate(specs):
        d = cuts[k + 1] - cuts[k]
        m = clip_info(f); kind = m['kind']
        cont = st == 'CONT'
        if cont:   # continue the previous shot of the same clip
            prev = [s for s in shots if s['f'] == f][-1]; st = prev['st'] + prev['d'] * prev['speed']
        else: st = float(st) if st else None
        speed = 1.0
        if kind == 'video':
            avail = m['dur'] - (st or 0) - 0.15
            if st is None:
                st = max(0.0, (m['dur'] - d) * 0.3) if m['dur'] > d + 0.3 else 0.0
                avail = m['dur'] - st - 0.15
            if avail < d:
                fps = eval(m.get('fps', '30/1'))
                floor = 0.5 if fps >= 50 else 0.8
                speed = max(floor, avail / d)
                if avail / speed < d - 0.05:
                    problems.append(f"{b['id']} {f}: needs {d:.2f}s, has {avail:.2f}s even at {speed:.2f}x")
        shots.append(dict(beat=b['id'], f=f, st=round(st or 0, 3), d=round(d, 3), t=round(cuts[k], 3), speed=round(speed, 3), nat=not b['vo'], kind=kind))

# ---------- fx ----------
fx = []
for b, bt in zip(B, beats):
    if b.get('chapter'): fx.append(dict(beat=b['id'], kind='chapter', text=b['chapter'], t=bt['span'][0] + 0.15))
    for item in b['fx']:
        kind, cue = item[0], item[2]
        if isinstance(cue, (int, float)):
            at = bt['start'] + cue
        else:
            at = cue_time(bt, cue, bt['span'][0])
            if at is None: continue
            at -= 0.05
        fx.append(dict(beat=b['id'], kind=kind, arg=item[1], t=round(at, 3), extra=list(item[3:])))
    if b.get('end'): fx.append(dict(beat=b['id'], kind='endcard', t=round(bt['end'], 3)))

# ---------- captions + chapters ----------
def ts(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f'{int(h):02}:{int(m):02}:{s:06.3f}'.replace('.', ',')
with open(f'{WD}/captions_en.srt', 'w') as fh:
    n = 0
    for a, b_, txt in caps:
        txt = re.sub(r'\b(um+|uh+)\b,?\s*', '', txt, flags=re.I).strip()
        txt = txt.replace('Sean', 'Shawn').replace('Shawn and China', 'Shawn in China').replace('Haifu machines', 'HIFU machines').replace('Liangjiang', 'Liangjiang')
        if not txt: continue
        n += 1; fh.write(f'{n}\n{ts(a)} --> {ts(b_ + 0.15)}\n{txt}\n\n')
chap = [(0.0, 'Not CGI')] + [(f['t'] - 0.15, f['text']) for f in fx if f['kind'] == 'chapter']
with open(f'{WD}/chapters.txt', 'w') as fh:
    for a, name in chap: fh.write(f"{int(a // 60)}:{int(a % 60):02d} {name}\n")
json.dump(dict(total=TOTAL, beats=[{k: v for k, v in bt.items() if k != 'pieces'} | dict(pieces=[dict(src=p['src'], at=p['at'], text=p['text'], words=p['words_t']) for p in bt['pieces']]) for bt in beats],
               shots=shots, fx=fx), open(f'{WD}/timeline2.json', 'w'), indent=1, ensure_ascii=False)
print(f'total {TOTAL:.1f}s, {len(shots)} shots, {len(fx)} fx', file=sys.stderr)
for p in problems: print('short:', p, file=sys.stderr)
