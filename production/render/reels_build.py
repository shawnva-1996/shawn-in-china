"""Build the render kit for each reel in reels_spec.py (series trailer + one reel per day).
  1. VO: every take is cut from the RAW recording at real pauses (reel_vo.start_of / end_of), whole takes only;
     a take marked "first sentence" ends at the pause after that sentence. Each cut is checked by transcript
     (Gemini via gem.py) and the build stops if any line is not the complete expected sentence.
  2. Timeline: a 0.2 s cover (the thumbnail as the first frames), then the segments on a 0.3 s grid (100 BPM).
  3. Shots: fast cuts (about 0.6–1.2 s) cycling through each line's clips at different in-points, alternating punch-ins.
  4. Overlays (rovl/), cover text (rovl/cover.png), hype score (reels_score.py), VO + ducked bed.
usage: reels_build.py <workdir> <timeline2.json> <vo_raw.wav> <meta.json> <thumbnail.jpg> [reel ...] [--no-verify]
writes <workdir>/<reel>/ = the kit make_reel.py renders on the Mac
"""
import json, math, os, re, subprocess, sys, base64, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/gfx')
from reels_spec import REELS
from reel_vo import energy, start_of, end_of, quiet, HOP
import reels_score, travel_score, guofeng_score, guofeng_ai
# series trailer = hype; day reels: 'travel' rejected 30 Oct (not Chinese), now Chinese-style trap ('guofeng' = synthesised,
# 'guofeng_ai' = produced track fitted to the timeline)
MUSIC = {'hype': reels_score.score, 'travel': travel_score.score, 'guofeng': guofeng_score.score, 'guofeng_ai': guofeng_ai.score}

GRID, T0, END = 0.3, 0.2, 3.2
SR = 48000
VO_CHAIN = 'highpass=f=80,afftdn=nr=12:nf=-40,equalizer=f=6500:t=q:w=2:g=-3,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2'
# takes whose timeline text dropped words that are in the recording (checked by a free transcript of the take)
# (word times are placed by the voice activity in the take; they only drive the captions)
TEXT = {('B36', 0): ('This might be the best meal we had in Chongqing.',
                     [['This', 0.01], ['might', 0.22], ['be', 0.5], ['the', 0.63], ['best', 0.84], ['meal', 1.1], ['we', 1.3], ['had', 1.42],
                      ['in', 1.55], ['Chongqing.', 1.63]]),
        ('B28', 1): ('A robot dog walked around the hall.',
                     [['A', 0.03], ['robot', 0.15], ['dog', 0.68], ['walked', 1.08], ['around', 1.5], ['the', 1.85], ['hall.', 2.0]]),
        ('B33', 1): ('brought out by the chef.', [['brought', 0.09], ['out', 0.32], ['by', 0.62], ['the', 0.74], ['chef.', 0.8]]),
        ('B27', 0): 'drop then'}      # he says "And in the afternoon"

FIX = {'Sean': 'Shawn', 'Haifu': 'HIFU', 'visa': 'Visa', 'mastercard': 'Mastercard'}

def split_end(edb, r0, r1):
    """end of the first sentence inside a take: the deepest pause (>= 80 ms) between r0 and r1"""
    i0, i1 = int(r0 / HOP), int(r1 / HOP); q = quiet(edb, i0); best = None
    k = i0
    while k < i1:
        if edb[k] < q:
            j = k
            while j < i1 and edb[j] < q: j += 1
            if j - k >= 8 and (best is None or j - k > best[1] - best[0]): best = (k, j)
            k = j
        else: k += 1
    if best is None: raise RuntimeError('no pause found to split the take')
    return (best[0] + min(10, (best[1] - best[0]) // 2)) * HOP

LEAD, TAIL = 0.15, 0.20      # room tone kept before the first sound and after the last one (as far as the pause allows)

def pad_cut(edb, s, f):
    """start_of/end_of cut right at the edge of the voice (often 20 ms before the first sound, so the 20 ms fade-in can
    soften a soft first consonant). Move both cuts out into the surrounding pause, never past its far end."""
    i, j = int(round(s / HOP)), int(round(f / HOP)); q = quiet(edb, i); k = i
    while k > max(0, i - int(LEAD / HOP)) and edb[k - 1] < q: k -= 1
    q = quiet(edb, j); m = j
    while m < min(len(edb) - 4, j + int((TAIL - 0.1) / HOP)) and np.all(edb[m:m + 4] < q): m += 1   # end_of already left 0.1 s
    return round(k * HOP, 3), round(m * HOP, 3)

def cut_takes(spec, tl, edb):
    beats = {b['id']: b for b in tl['beats']}; out = {}
    for seg in spec['segs']:
        if seg[0] != 'line': continue
        for tk in seg[1]:
            key = tuple(tk); p = beats[tk[0]]['pieces'][tk[1]]
            s = start_of(edb, p['src'][0])
            words = p['words']; text = p['text']
            if TEXT.get(key) == 'drop then':
                text = text.replace('And then in', 'And in'); words = [w for w in words if w[0] != 'then']
            elif key in TEXT: text, words = TEXT[key]
            if len(tk) > 2:          # first sentence only
                k = next(i for i, (w, _) in enumerate(words) if re.search(r'[.?!]$', w))
                text = re.split(r'(?<=[.?!])\s', p['text'])[0]; words = words[:k + 1]
                t_next = p['words'][k + 1][1]; r_next = p['src'][0] + (t_next - p['at'])
                r_last = p['src'][0] + (words[-1][1] - p['at'])
                f = split_end(edb, r_last + 0.15, r_next + 0.1)
            else:
                f = end_of(edb, p['src'][1])
            s, f = pad_cut(edb, s, f)
            out[key] = dict(raw=[round(s, 3), round(f, 3)], text=text, onset=round(p['src'][0] - s, 3),
                            words=[[FIX.get(w.strip('.,?!'), w.strip('.,?!')) + w[len(w.rstrip('.,?!')):], round(t - p['at'], 3)] for w, t in words])
    return out

def end_alts(edb, f, limit=1.6):
    """later ends to try when a take fails the check: a longer tail, then the end of each following pause"""
    i = int(f / HOP); q = quiet(edb, i); n = i + int(limit / HOP); out = [f + 0.15, f + 0.3]; k = i
    while k < n:
        while k < n and edb[k] < q: k += 1
        while k < n and edb[k] >= q: k += 1
        if k < n and np.all(edb[k:k + 12] < q): out += [k * HOP + 0.10, k * HOP + 0.25]
    return [round(x, 3) for x in out]

def start_alts(edb, s, limit=1.0):
    """earlier starts to try: a longer lead, then the start of each earlier pause"""
    i = int(s / HOP); q = quiet(edb, i); n = max(5, i - int(limit / HOP)); out = [s - 0.1, s - 0.2]; k = i
    while k > n:
        while k > n and edb[k] < q: k -= 1
        while k > n and edb[k] >= q: k -= 1
        if k > n and np.all(edb[k - 5:k] < q): out.append((k - 1) * HOP)
    return [round(max(0, x), 3) for x in out]

def repair(key, v, edb, raw):
    """re-cut a failed take: try later ends first (most failures lose the last word), then earlier starts"""
    s0, f0 = v['raw']; on0 = v['onset']; chk = v.get('check', {})
    tries = [(s0, f) for f in end_alts(edb, f0)] if (chk.get('last_word_clipped') or not chk.get('first_word_clipped')) else []
    tries += [(s, f0) for s in start_alts(edb, s0)] + [(s, f) for s in start_alts(edb, s0)[:2] for f in end_alts(edb, f0)[:2]]
    for s, f in tries:
        v['raw'] = [s, f]; v['onset'] = round(on0 + (s0 - s), 3); v.pop('check', None)
        if not verify_takes({key: v}, raw): print('  fixed', key, (s0, f0), '->', (s, f), file=sys.stderr); return True
    v['raw'] = [s0, f0]; v['onset'] = on0; v['check'] = chk; return False

def verify_takes(takes, raw):
    from gem import gemini
    norm = lambda t: re.sub(r'[^a-z0-9 ]', '', t.lower().replace("'", '').replace('-', ' ')).split()
    bad = []
    for key, v in takes.items():
        if v.get('check', {}).get('ok'): continue
        if v['raw'] in v.setdefault('failed', []): bad.append(key); continue      # a cut that failed once is never retried
        s, f = v['raw']
        with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-t', str(f - s), '-i', raw, '-af', 'highpass=f=80,afftdn=nr=12:nf=-40',
                            '-ar', '16000', '-ac', '1', tmp.name], check=True)
            b = base64.b64encode(open(tmp.name, 'rb').read()).decode()
        r = gemini([{"inline_data": {"mime_type": "audio/wav", "data": b}},
                    {"text": f'A voice clip cut out of a longer narration. Expected words: "{v["text"]}". Listen carefully to the very '
                             'start and the very end. Return JSON: {"transcript": verbatim words you hear, "first_word_clipped": bool, '
                             '"last_word_clipped": bool, "missing_words": [expected words you did not hear], '
                             '"extra_words": [whole or partial words heard that are not in the expected text]}'}])
        if isinstance(r, list): r = r[0] if r else {}
        heard, exp = norm(r.get('transcript', '')), norm(v['text'])
        ok = not (r.get('first_word_clipped') or r.get('last_word_clipped') or r.get('missing_words') or r.get('extra_words'))
        ok = ok and heard[:1] == exp[:1] and heard[-1:] == exp[-1:]
        v['check'] = dict(r, ok=ok)
        if not ok: bad.append(key); v['failed'].append(list(v['raw']))
        print('  ok  ' if ok else '  FAIL', key, v['text'][:60], '=>', r.get('transcript', '')[:60], file=sys.stderr)
    return bad

def resolve(meta, f):
    if f in meta or f.startswith(('VIZ:', 'BLACK')): return f
    ks = [k for k in meta if k.startswith(f)]
    assert len(ks) == 1, f; return ks[0]

def plan(name, spec, takes, meta):
    t = T0; segs, shots, vo = [], [], []
    for seg in spec['segs']:
        kind = seg[0]; flags = seg[4] if len(seg) > 4 else {}
        if kind == 'line':
            cur = t + 0.12; words = []
            for tk in seg[1]:
                v = takes[tuple(tk)]; L = v['raw'][1] - v['raw'][0]
                vo.append(dict(at=round(cur, 3), raw=v['raw'], text=v['text']))
                words += [[w, round(cur + v['onset'] + wt, 3)] for w, wt in v['words']]
                cur += L + 0.06
            d = math.ceil((cur - t + 0.12) / GRID - 1e-6) * GRID
            clips, text = seg[2], seg[3]
        elif kind == 'music':
            d, clips, text, words = seg[1], seg[2], seg[3], []
        else:
            d, clips, text, words = seg[1], [('BLACK', 0.0)], '', []
        d = round(d, 3); segs.append(dict(name=f'{len(segs):02d}', kind=kind, t=round(t, 3), d=d, text=text, words=words, flags=flags))
        # cuts
        U = round(d / GRID); opts = [cl[2] if len(cl) > 2 else {} for cl in clips]
        single = kind == 'silence' or any(o.get('sp') for o in opts) or clips[0][0].startswith('VIZ:')
        n = 1 if single else min(U // 2, max(len(clips), round(d / (0.6 if flags.get('montage') else 0.9))))
        sizes = [U // n + (1 if k < U % n else 0) for k in range(n)]
        tt = t; used = {}
        for k, u in enumerate(sizes):
            cl = clips[k % len(clips)]; f = resolve(meta, cl[0]); o = opts[k % len(clips)]; cd = u * GRID
            rep = used.get(f, 0); used[f] = rep + 1
            sh = dict(seg=len(segs) - 1, f=f, t=round(tt, 3), d=round(cd, 3), z=1.0 if k % 2 == 0 else 1.15, push=o.get('push'),
                      sp=o.get('sp', 1.0), hold=0.0, st=cl[1])
            if f.startswith('VIZ:'): sh['hold'] = round(max(0.0, cd - 8.9), 3); sh['z'] = 1.0
            elif f != 'BLACK':
                dur = meta[f]['dur']; need = (cd - sh['hold']) * sh['sp'] + 0.15
                st = cl[1] + rep * 1.7
                if st + need > dur: st = max(0.0, (cl[1] + rep * 0.9) % max(0.1, dur - need))
                sh['st'] = round(min(st, max(0.0, dur - need)), 3)
                if sh['sp'] != 1.0 and (dur - sh['st']) / sh['sp'] < cd:      # not enough slow-motion footage: hold the end
                    sh['hold'] = round(cd - (dur - sh['st'] - 0.15) / sh['sp'], 3)
                if sh['push']: sh['z'] = 1.0
            shots.append(sh); tt += cd
        t += d
    end_t = round(t, 3); total = round(end_t + END, 3)
    cov = spec['cover']; cover = dict(f=resolve(meta, cov['f']), st=cov['st'], z=cov.get('z', 1.0), d=T0)
    return dict(name=name, title=spec['title'], out=spec['out'], music=spec.get('music', 'hype'), tag=spec['tag'], hook=spec['hook'], total=total, end=[end_t, END],
                cover=cover, t0=T0, segs=segs, shots=shots, vo=vo)

def build_audio(R, raw, kit, vo=True):
    """vo=False keeps the kit's existing vo.wav / vo_clean.m4a and only rebuilds the music bed"""
    N = int(R['total'] * SR)
    if vo: _build_vo(R, raw, kit, N)
    _build_bed(R, kit, N)

def _build_vo(R, raw, kit, N):
    vo = np.zeros(N, np.float32)
    for v in R['vo']:
        s, f = v['raw']
        x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(s), '-t', str(f - s), '-i', raw, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                                         capture_output=True, check=True).stdout, np.float32).copy()
        a, b = int(0.02 * SR), int(0.05 * SR); x[:a] *= np.linspace(0, 1, a); x[-b:] *= np.linspace(1, 0, b)
        i = int(v['at'] * SR); vo[i:i + len(x)] += x[:N - i]
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', VO_CHAIN + ',loudnorm=I=-16:TP=-1.5:LRA=7',
                    '-ar', str(SR), f'{kit}/vo.wav'], input=vo.tobytes(), check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{kit}/vo.wav', '-c:a', 'aac', '-b:a', '256k', f'{kit}/vo_clean.m4a'], check=True)

def _build_bed(R, kit, N):
    tl = [dict(t=s['t'], d=s['d'], kind=s['kind'], flags=s['flags']) for s in R['segs']]
    MUSIC[R.get('music', 'hype')](tl, R['total'], R['end'][0], f'{kit}/score.wav')
    load = lambda p, ch: np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                                                      capture_output=True, check=True).stdout, np.float32).reshape(-1, ch).copy()
    v = load(f'{kit}/vo.wav', 1)[:N, 0]; v = np.pad(v, (0, N - len(v))); bed = load(f'{kit}/score.wav', 2)[:N]; bed = np.pad(bed, ((0, N - len(bed)), (0, 0)))
    hop = SR // 100; env = np.array([np.sqrt(np.mean(v[i:i + hop] ** 2)) for i in range(0, N, hop)])
    talk = np.convolve((20 * np.log10(env + 1e-9) > -38).astype(np.float32), np.ones(20) / 20, 'same') > 0.05
    g = np.where(talk, 10 ** (-4 / 20), 1.0).astype(np.float32)
    for i in range(1, len(g)): g[i] = g[i - 1] + (g[i] - g[i - 1]) * (0.25 if g[i] < g[i - 1] else 0.06)
    bed *= np.interp(np.arange(N), np.arange(len(g)) * hop, g)[:, None].astype(np.float32) * 0.8
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'alimiter=limit=0.89:level=false',
                    '-c:a', 'aac', '-b:a', '256k', f'{kit}/bed.m4a'], input=bed.astype(np.float32).tobytes(), check=True)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    wd, tl_path, raw, meta_path, thumb = args[:5]; names = args[5:] or list(REELS)
    tl = json.load(open(tl_path)); meta = json.load(open(meta_path)); edb = energy(raw)
    cache_p = f'{wd}/takes.json'; cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    for name in names:
        spec = REELS[name]; kit = f'{wd}/{name}'; os.makedirs(kit, exist_ok=True)
        takes = cut_takes(spec, tl, edb)
        for k, v in takes.items():                       # reuse a passed check only if the cut hasn't changed
            old = cache.get(json.dumps(list(k)))
            v['cut'] = list(v['raw'])                    # the automatic cut; 'raw' may later be a repaired one
            v['failed'] = old.get('failed', []) if old and old.get('text') == v['text'] else []
            if old and old.get('check', {}).get('ok') and old['text'] == v['text'] and v['cut'] in (old['raw'], old.get('cut')):
                v.update(raw=old['raw'], onset=old['onset'], check=old['check'])
        if '--no-verify' not in sys.argv:
            print(name, 'checking', len(takes), 'takes', file=sys.stderr)
            bad = verify_takes(takes, raw)
            bad = [k for k in bad if not repair(k, takes[k], edb, raw)]
            for k, v in takes.items(): cache[json.dumps(list(k))] = v
            json.dump(cache, open(cache_p, 'w'), indent=1, ensure_ascii=False)
            if bad: print(name, 'STOP:', len(bad), 'takes failed the transcript check', bad, file=sys.stderr); continue
        R = plan(name, spec, takes, meta)
        json.dump(R, open(f'{kit}/reel.json', 'w'), indent=1, ensure_ascii=False)
        subprocess.run([sys.executable, HERE + '/gfx/reels_ovl.py', kit, thumb], check=True)
        build_audio(R, raw, kit)
        print(name, 'kit ready', R['total'], 's', len(R['shots']), 'shots', file=sys.stderr)

if __name__ == '__main__': main()
