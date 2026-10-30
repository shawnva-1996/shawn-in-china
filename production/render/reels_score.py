"""Hype score for any reel, built from its timeline with the instruments of the approved trailer score
(trailer_score.py): braam + boom on the open, ticking pulse while the hook plays, a riser into the drop, a string
ostinato and taiko pulse with a hit on every new line, full drums on montage segments, dead silence on silence
segments, a low pad with piano for closing lines, and a title hit on the end card. D minor, 100 BPM.
score(timeline, total, end_t, out_wav)   timeline = [dict(t, d, kind, flags)] from reels_build.py
"""
import numpy as np
from trailer_score import (SR, BEAT, D1, D2, A2, D3, F3, braam, boom, taiko, snare, tick, stab, pad, piano, riser, swell,
                           bar_roots, write, rng, lp, fftconvolve)

class Stem:
    def __init__(s, total, wet): s.x = np.zeros((int((total + 4) * SR), 2)); s.wet = wet
    def add(s, at, y, g=1.0, pan=0.0):
        i = int(at * SR); y = y[:max(0, len(s.x) - i)] * g
        s.x[i:i + len(y), 0] += y * ((1 - pan) / 2) ** 0.5; s.x[i:i + len(y), 1] += y * ((1 + pan) / 2) ** 0.5
    def out(s, cut=None, fade=0.03):
        n = int(2.4 * SR); te = np.arange(n) / SR; y = s.x.copy()
        for k in (0, 1):
            ir = lp(rng.standard_normal(n), 5000) * np.exp(-te / 0.75); ir[:int(0.02 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
            y[:, k] += s.wet * fftconvolve(s.x[:, k], ir)[:len(y)]
        if cut is not None:
            i = int(cut * SR); f = int(fade * SR); y[max(0, i - f):i] *= np.linspace(1, 0, min(f, i))[:, None]; y[i:] = 0
        return y

def score(tl, total, end_t, out):
    """tl: segments in order, each dict(t, d, kind in line/music/silence, flags dict)"""
    regions = []; cur = None
    for k, s in enumerate(tl):                       # a new region starts after every silence and where 'low' begins
        if s['kind'] == 'silence': cur = None; continue
        if cur is None or s['flags'].get('low') and not cur['low']:
            cur = dict(t0=s['t'], t1=s['t'] + s['d'], low=bool(s['flags'].get('low')), segs=[]); regions.append(cur)
        cur['t1'] = s['t'] + s['d']; cur['segs'].append(s)
    for r, nxt in zip(regions, regions[1:] + [None]):           # a region rings on into the next unless a silence cuts it
        if nxt and abs(nxt['t0'] - r['t1']) < 1e-6: r['fade'] = 0.25; r['cut'] = r['t1'] + 0.25
        else: r['fade'] = 0.012; r['cut'] = r['t1']
    r_end = regions[-1]
    if abs(r_end['t1'] - end_t) < 1e-6: r_end['cut'] = end_t + 0.3; r_end['fade'] = 0.3
    drops = [s['t'] for s in tl if s['flags'].get('drop')]
    first_drop = drops[0] if drops else tl[1]['t']
    mix = np.zeros((int((total + 4) * SR), 2))
    for r in regions:
        S = Stem(total, 0.4 if r['low'] else 0.25)
        if r['low']:
            S.add(r['t0'], braam(4.0, (D1, D2, A2), 1400), 0.8); S.add(r['t0'], boom(2.6), 0.7)
            chords = [(D2, A2, D3, F3), (46 - 12, D3, F3), (43 - 12, 46, D3), (45 - 12, 49, 52)]
            t = r['t0'] + 0.3; k = 0
            while t < r['t1'] - 0.3:
                d = min(2.4, r['t1'] - t + 0.4); S.add(t, pad(chords[k % 4], d + 0.5, 600), 0.42); t += 2.4; k += 1
            for k, t in enumerate(np.arange(r['t0'] + 0.4, r['t1'] - 0.2, 1.2)): S.add(t, piano([74, 69, 65, 64, 62, 69][k % 6]), 1.0, 0.2)
            for k, t in enumerate(np.arange(r['t0'] + 1.2, r['t1'] - 0.05, BEAT / 2)): S.add(t, tick(k % 2 == 0), 0.4, 0.3 if k % 2 else -0.3)
        else:
            if r is regions[0]:
                S.add(r['t0'], braam(4.0), 0.9); S.add(r['t0'], boom(), 0.9)
            for s in r['segs']:
                t0, t1, fl = s['t'], s['t'] + s['d'], s['flags']
                pre = t0 < first_drop
                if fl.get('drop') or (t0 == first_drop):
                    S.add(t0, braam(3.0, bright=3400), 1.0); S.add(t0, boom(3.0, 90, 30), 1.0)
                elif s['kind'] == 'line' and not pre and s is not r['segs'][0]:
                    S.add(t0 - 0.02, boom(1.2, 60, 34), 0.45); S.add(t0 - 0.02, stab(D2, 0.5, 1200), 0.35)
                elif s is r['segs'][0] and r is not regions[0]:
                    S.add(t0, braam(3.5), 1.0); S.add(t0, boom(), 0.9)
                if pre:          # the hook: drone, ticks, a quiet pulse that brightens toward the drop
                    S.add(t0, pad((D2, A2), t1 - t0 + 0.2, 380), 0.35)
                    for k, t in enumerate(np.arange(t0 + 0.6, t1 - 0.05, BEAT / 2)): S.add(t, tick(k % 2 == 0), 0.55, 0.4 if k % 2 else -0.4)
                    span = max(0.6, first_drop - tl[0]['t'])
                    for t, n, acc in bar_roots(t0 + 0.6, t1, [D3, D3, 46, 45]):
                        p = (t - tl[0]['t']) / span; S.add(t, stab(n, 0.14, 600 + 2400 * p), 0.16 * (1.4 if acc else 1) * (0.5 + 0.5 * p), 0.25 if n % 2 else -0.25)
                    for t in np.arange(t0 + max(0.6, (t1 - t0) / 2), t1 - 0.05, BEAT): S.add(t, taiko(0.55))
                elif fl.get('montage'):
                    for k, t in enumerate(np.arange(t0, t1 - 0.01, BEAT)):
                        S.add(t, taiko(0.95)); S.add(t, boom(0.8, 80, 40), 0.35); S.add(t + BEAT / 2, taiko(0.45))
                        S.add(t + BEAT / 2, snare(0.35)); S.add(t, stab([D2, D2, 34, 33][(k // 2) % 4], 0.45, 2400), 0.5)
                    for t, n, acc in bar_roots(t0, t1, [D3 + 12, 58, 55, 57]): S.add(t, stab(n, 0.11, 3200), 0.12 * (1.3 if acc else 1), 0.35 if n % 2 else -0.35)
                else:            # the pulse
                    for t, n, acc in bar_roots(t0, t1, [D3, 46, 43, 45]): S.add(t, stab(n, 0.12, 2200), 0.16 * (1.35 if acc else 1), 0.3 if n % 2 else -0.3)
                    for k, t in enumerate(np.arange(t0, t1 - 0.01, BEAT)):
                        S.add(t, taiko(0.75 if k % 2 == 0 else 0.5))
                        if k % 2 == 1: S.add(t, snare(0.22))
                    S.add(t0, pad((D2, A2, D3), t1 - t0 + 0.3, 520), 0.28)
                nxt = next((x for x in tl if x['t'] >= t1 - 1e-6), None)
                if nxt is not None and nxt['flags'].get('drop') and nxt['t'] == t1:
                    S.add(t1 - 2.4, riser(2.4), 0.75); S.add(t1 - 0.8, swell(), 0.8)
                if fl.get('stop'):
                    for k, t in enumerate(np.arange(t1 - 2.4, t1 - 0.01, BEAT / 4)): S.add(t, snare(0.12 + 0.3 * k / 16), 1.0, 0.2 * (-1) ** k)
                    S.add(t1 - 2.4, riser(2.4, 220, 1400), 0.7)
            if r is r_end and not r['low']:
                S.add(end_t - 1.2, riser(1.2, 300, 1500), 0.6)
        mix += S.out(r['cut'], r['fade'])
    E = Stem(total, 0.45)
    thud = [s for s in tl if s['flags'].get('thud')]
    for s in thud: E.add(s['t'] + s['d'], boom(2.2, 55, 28), 1.2); E.add(s['t'] + s['d'], lp(taiko(1.0), 400), 0.8)
    E.add(end_t - 0.6, swell(0.6), 0.9); E.add(end_t, braam(3.4, bright=3800), 1.05); E.add(end_t, boom(3.2, 95, 28), 1.1)
    E.add(end_t + 0.6, piano(74, 3.0, 0.4), 1.0)
    mix += E.out()
    mix = mix[:int(total * SR)]; f = int(1.4 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.3) * 0.89
    write(mix, out, 'loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')
