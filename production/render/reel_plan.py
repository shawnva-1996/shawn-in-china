"""Edit list for the ep. 1 hype reel (production/reel_script_v1.md, approved 30 Oct 2026). Every cut is placed on
the trailer score's grid (trailer_score.py: 100 BPM, one beat = 0.6 s), so hits land on cuts.
v2 (30 Oct): portrait clips wherever a beat has one (20 of 31); landscape clips are centre-cropped.
usage: reel_plan.py <timeline2.json> <out reel.json>
The VO lines are the ones already in vo_clean.wav (same ranges as trailer_score.VO); caption words are taken from
the main timeline and moved to reel time.
"""
import json, sys
from trailer_score import VO, TOTAL, TITLE

WC = 'from_wechat/'
F = {k: v for k, v in [
    ('drone', WC + '6fe5e4fcdec8065ce4c81bbea8f9c5e1.mp4'), ('drone2', WC + 'a709704270343b6f0724127d74f2f8db.mp4'),
    ('dance', WC + '9bda1fa54f8880986d740e6d04642348.mp4'), ('cable', WC + '280a911cf4097c4ed0c1e822876e59f1.mp4'),
    ('crowd', WC + 'fa6c95b5a1e95c26e55f500bfefcdd4d.mp4'), ('group', WC + 'd77eaa66a900830a7d95e6cc5429fc85.mp4')]}
def c(day, n): return f'{day} Oct/IMG_{n}.' + ('mov' if n == 8910 else 'MOV')

# (segment, start, end, on-screen text, [(clip, in-point, duration, options)])  options: z = punch-in, push = slow
# push-in to that zoom, sp = speed (<1 is slow motion from the 60 fps originals), hold = freeze the last frame (s)
SEGS = [
    ('cgi', 0.0, 3.0, 'NOT CGI.', [(F['drone'], 16.0, 3.0, dict(push=1.12))]),
    ('tourist', 3.0, 6.9, '6 DAYS.|NOT A TOURIST.', [(c(15, 8741), 0.8, 1.2, {}), (c(17, 9003), 1.0, 0.9, dict(z=1.15)),
                                                    (c(17, 9001), 0.3, 0.9, {}), (c(16, 8877), 0.8, 0.9, dict(z=1.15))]),
    ('doors', 6.9, 10.2, '🔒', [(c(13, 8325), 0.67, 0.55, {}), (c(13, 8359), 0.26, 0.55, dict(z=1.2)), (c(13, 8303), 2.96, 0.55, {}),
                               (c(13, 8325), 2.6, 0.55, dict(z=1.2)), (c(13, 8359), 3.5, 0.55, {}), (c(13, 8303), 6.0, 0.55, dict(z=1.2))]),
    ('drop', 10.2, 11.4, '', [(c(17, 8928), 0.89, 1.2, dict(push=1.1))]),
    ('visa', 11.4, 13.2, '❓', [(c(17, 9010), 0.8, 0.9, {}), (c(17, 9010), 3.4, 0.9, dict(z=1.18))]),
    ('pay', 13.2, 14.7, '❓', [(c(17, 8997), 0.8, 0.75, {}), (c(16, 8913), 0.8, 0.75, dict(z=1.15))]),
    ('8d', 14.7, 18.0, '8D?!', [(c(16, 8902), 0.6, 1.1, {}), (c(15, 8682), 1.11, 1.1, dict(z=1.15)), (c(13, 8318), 0.0, 1.1, {})]),
    ('robots', 18.0, 21.0, '🤖', [(c(14, 8591), 0.12, 1.0, dict(z=1.25)), (c(14, 8590), 4.46, 1.0, dict(z=1.3)), (c(14, 8580), 38.0, 1.0, dict(z=1.35))]),
    ('hotpot', 21.0, 23.6, '🌶️🌶️🌶️', [(c(16, 8909), 0.3, 1.3, dict(push=1.15)), (c(16, 8910), 4.0, 1.3, dict(z=1.15))]),
    ('silence', 23.6, 24.6, '', [('BLACK', 0, 1.0, {})]),
    ('safe', 24.6, 27.0, '🌃', [(c(15, 8723), 0.8, 0.8, {}), (F['dance'], 13.83, 0.8, dict(z=1.15)), (c(15, 8722), 1.26, 0.8, {})]),
    ('montage', 27.0, 31.8, '', [(F['drone2'], 9.0, 0.6, {}), (c(15, 8724), 1.31, 0.6, dict(z=1.15)), (WC + '63e5c062c790adcfc249d8d240c0f395.mp4', 3.0, 0.6, {}),
                                 (c(15, 8624), 0.59, 0.6, dict(z=1.15)), (c(16, 8916), 20.0, 0.6, {}), (F['cable'], 4.72, 0.6, dict(z=1.15)),
                                 (F['crowd'], 10.0, 0.6, {}), (F['group'], 6.97, 0.6, dict(z=1.1))]),
    ('worth', 31.8, 36.6, 'IS IT WORTH IT?', [(c(15, 8678), 0.0, 4.8, dict(sp=0.55, push=1.15))]),
    ('behind', 36.6, 39.4, '', [(c(13, 8325), 3.0, 2.8, dict(sp=0.5, hold=0.6, push=1.12))]),
    ('thud', 39.4, TITLE, '', [('BLACK', 0, round(TITLE - 39.4, 3), {})]),
]

def main(tl_path, out):
    tl = json.load(open(tl_path)); words = [w for b in tl['beats'] for p in b['pieces'] for w in p['words']]
    vo = []
    for (at, a, e), end in zip(VO, '...???????.'):
        ws = [[w, round(at + t - a, 3)] for w, t in words if a - 0.02 <= t < e - 0.05]
        if ws and ws[-1][0][-1] not in '.?!': ws[-1][0] += end
        vo.append(dict(at=at, src=[a, e], words=ws, text=' '.join(w for w, _ in ws)))
    segs, shots = [], []
    for name, t0, t1, text, cuts in SEGS:
        t = t0
        for f, st, d, o in cuts:
            shots.append(dict(seg=len(segs), f=f, st=st, d=d, t=round(t, 3), z=o.get('z', 1.0), push=o.get('push'),
                              sp=o.get('sp', 1.0), hold=o.get('hold', 0.0))); t += d
        assert abs(t - t1) < 1e-6, (name, t, t1)
        segs.append(dict(name=name, t=t0, d=round(t1 - t0, 3), text=text,
                         words=[w for v in vo for w in v['words'] if t0 <= w[1] < t1]))
    json.dump(dict(total=TOTAL, end=[TITLE, round(TOTAL - TITLE, 3)], segs=segs, shots=shots, vo=vo), open(out, 'w'), indent=1, ensure_ascii=False)
    print(len(segs), 'segments', len(shots), 'shots', file=sys.stderr)

if __name__ == '__main__': main(*sys.argv[1:3])
