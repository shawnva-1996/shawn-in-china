"""Plan a ~90 s vertical trailer (Reels / TikTok / Shorts) from the main episode's timeline.
Each segment is a stretch of the main edit (VO + the shots under it), picked by beat and piece, optionally
starting at a word. Picture, VO, captions and sound effects all come from the same main-timeline range,
so sync is inherited from the main edit.
usage: trailer_plan.py <workdir>     reads timeline2.json, writes trailer.json
"""
import json, re, sys
WD = sys.argv[1]
T = json.load(open(f'{WD}/timeline2.json')); B = {b['id']: b for b in T['beats']}
# (beat, first piece, last piece, start word or None)
SEGS = [('B01', 0, 0, None), ('B02', 0, 0, None), ('B03', 0, 1, None), ('B04', 0, 2, None),
        ('B05', 2, 2, None),
        ('B16', 0, 0, None), ('B17', 1, 2, None),
        ('B23', 1, 2, None),
        ('B28', 0, 1, None),
        ('B33', 0, 0, None),
        ('B39', 0, 0, 'And'),
        ('B44', 0, 0, None),
        ('B55', 0, 0, None), ('B57', 1, 2, None),
        ('B61', 0, 0, 'at'),
        ('B48', 1, 1, None),
        ('B65', 0, 0, None), ('B66', 0, 2, None)]
PAD0, PAD1, END = 0.08, 0.22, 5.0
segs = []; t = 0.0
for bid, p0, p1, w0 in SEGS:
    b = B[bid]; ps = b['pieces'][p0:p1 + 1]
    a = ps[0]['at'] - PAD0
    if w0: a = next(wt for w, wt in ps[0]['words'] if w.strip(',.?') == w0) - PAD0
    e = ps[-1]['at'] + (ps[-1]['src'][1] - ps[-1]['src'][0]) + PAD1
    words = [(w, wt - a + t) for p in ps for w, wt in p['words'] if a <= wt < e]
    shots = []
    for s in T['shots']:
        o0, o1 = max(a, s['t']), min(e, s['t'] + s['d'])
        if o1 - o0 < 0.04: continue
        shots.append(dict(f=s['f'], st=round(s['st'] + (o0 - s['t']) * s['speed'], 3), d=round(o1 - o0, 3), t=round(o0 - a + t, 3),
                          speed=s['speed'], kind=s['kind']))
    # a pad can catch a sliver of the neighbouring beat's shot: give that time to the shot beside it instead
    while len(shots) > 1 and shots[0]['d'] < 0.5:
        x = shots.pop(0); n = shots[0]; n['st'] = round(max(0.0, n['st'] - x['d'] * n['speed']), 3); n['t'] = x['t']; n['d'] = round(n['d'] + x['d'], 3)
    while len(shots) > 1 and shots[-1]['d'] < 0.5:
        x = shots.pop(); shots[-1]['d'] = round(shots[-1]['d'] + x['d'], 3)
    fx = [dict(f, t=round(f['t'] - a + t, 3)) for f in T['fx'] if a <= f['t'] < e and f['kind'] in ('sticker', 'sfx', 'loc')]
    segs.append(dict(beat=bid, src=[round(a, 3), round(e, 3)], t=round(t, 3), d=round(e - a, 3), words=words, shots=shots, fx=fx))
    t += e - a
total = t + END
json.dump(dict(total=round(total, 3), end=[round(t, 3), END], segs=segs), open(f'{WD}/trailer.json', 'w'), indent=1, ensure_ascii=False)
print(f'{len(segs)} segments, {sum(len(s["shots"]) for s in segs)} shots, {total:.1f}s', file=sys.stderr)
