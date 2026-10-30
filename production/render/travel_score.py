"""Light, happy travel bed for the day reels (the series trailer keeps the hype score from reels_score.py).
Ukulele-style strums (Karplus-Strong), bouncy bass, soft kick, claps, shaker and a glockenspiel hook in D major,
I–V–vi–IV, 100 BPM so the beat lands on the reels' 0.3 s cut grid. Same timeline as reels_score.score():
music stops on silence segments, thins out (uke + glock, no drums) on 'low' segments, a lift (crash + fill) on
'drop' segments, and a bright final chord on the end card.
score(timeline, total, end_t, out_wav)   timeline = [dict(t, d, kind, flags)] from reels_build.py
"""
import numpy as np
from trailer_score import SR, BEAT, hz, tt, lp, bp, write, fftconvolve

rng = np.random.default_rng(11)
BAR = 4 * BEAT
# D major, I–V–vi–IV: chord tones as MIDI notes (uke voicing around middle C) and bass roots
CHORDS = [(62, 66, 69, 74), (61, 64, 69, 73), (62, 66, 71, 74), (62, 67, 71, 74)]   # D, A, Bm, G
ROOTS = [38, 33, 35, 31]
CHORDS_B = [CHORDS[2], CHORDS[3], CHORDS[0], CHORDS[1]]                              # B section: vi–IV–I–V
ROOTS_B = [ROOTS[2], ROOTS[3], ROOTS[0], ROOTS[1]]
HOOK = [(0, 78), (0.5, 76), (1, 74), (1.5, 76), (2, 78), (3, 81), (4, 78), (4.5, 76), (5, 74), (6, 71), (6.5, 74)]  # beats, note
HOOK_B = [(0, 83), (1, 81), (1.5, 78), (2.5, 76), (4, 79), (5, 78), (5.5, 76), (6, 74)]

def pluck(f, d=1.2, bright=0.5, g=1.0):
    """Karplus-Strong string: nylon/ukulele-like pluck"""
    n = int(d * SR); p = max(2, int(SR / f)); buf = lp(rng.uniform(-1, 1, p), 2500 + 5000 * bright)
    out = np.zeros(n); b = buf.copy(); k = 0
    while k < n:
        m = min(p, n - k); out[k:k + m] = b[:m]
        b = 0.996 * 0.5 * (b + np.roll(b, -1)); k += p
    return g * out * np.exp(-np.arange(n) / SR / (d * 0.6))

def strum(notes, down=True, g=1.0, d=1.0):
    """ukulele strum plus a nylon guitar an octave below, with a little wooden body resonance"""
    x = np.zeros(int((d + 0.1) * SR))
    for i, n in enumerate(notes if down else notes[::-1]):
        o = int(i * 0.011 * SR)
        y = pluck(hz(n), d, 0.6 if down else 0.45, 0.45 * g); x[o:o + len(y)] += y[:len(x) - o]
        y = pluck(hz(n - 12), d * 1.2, 0.35, 0.28 * g)[:len(x) - o]; x[o:o + len(y)] += y
    return x + 0.6 * bp(x, 180, 600)

def keys(notes, d, g=1.0):
    """soft electric-piano chord with a gentle tremolo, under the strums"""
    t = tt(d); env = np.minimum(1, t / 0.02) * np.exp(-t / 1.6) * (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))
    return g * 0.08 * sum(np.sin(2 * np.pi * hz(n) * t) + 0.2 * np.sin(4 * np.pi * hz(n) * t) for n in notes) * env

def tamb(g=1.0):
    t = tt(0.18); return g * 0.2 * bp(rng.standard_normal(len(t)), 6000, 14000) * np.exp(-t / 0.05)

def kick(g=1.0):
    t = tt(0.35); f = 50 + 70 * np.exp(-t / 0.03)
    return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)

def clap(g=1.0):
    t = tt(0.25); x = bp(rng.standard_normal(len(t)), 900, 5000)
    env = sum(np.exp(-np.clip(t - o, 0, None) / 0.008) * (t >= o) for o in (0, 0.012, 0.024)) + 0.5 * np.exp(-t / 0.08)
    return g * 0.35 * x * env

def shaker(g=1.0):
    t = tt(0.09); return g * 0.12 * bp(rng.standard_normal(len(t)), 5000, 12000) * np.sin(np.pi * t / 0.09) ** 2

def glock(n, d=1.4, g=1.0):
    t = tt(d); f = hz(n)
    return g * 0.22 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.08)) * np.exp(-t / 0.5)

def bass(n, d, g=1.0):
    t = tt(d); f = hz(n)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return g * 0.5 * x * np.minimum(1, t / 0.01) * np.exp(-t / 0.45)

def crash(g=1.0):
    t = tt(2.0); return g * 0.18 * bp(rng.standard_normal(len(t)), 3000, 14000) * np.exp(-t / 0.7)

class Bus:
    def __init__(s, total): s.x = np.zeros((int((total + 4) * SR), 2))
    def add(s, at, y, g=1.0, pan=0.0):
        i = int(at * SR)
        if i >= len(s.x) or i < 0: return
        y = y[:len(s.x) - i] * g
        s.x[i:i + len(y), 0] += y * ((1 - pan) / 2) ** 0.5; s.x[i:i + len(y), 1] += y * ((1 + pan) / 2) ** 0.5

def room(x, wet=0.18):
    n = int(1.2 * SR); te = np.arange(n) / SR; y = x.copy()
    for k in (0, 1):
        ir = lp(rng.standard_normal(n), 6000) * np.exp(-te / 0.35); ir[:int(0.012 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
        y[:, k] += wet * fftconvolve(x[:, k], ir)[:len(x)]
    return y

def score(tl, total, end_t, out):
    B = Bus(total); t0 = tl[0]['t']
    def seg_at(t):
        for s in tl:
            if s['t'] - 1e-6 <= t < s['t'] + s['d']: return s
        return None
    beat = 0; t = t0
    while t < end_t - 1e-6:
        s = seg_at(t)
        if s is None or s['kind'] == 'silence': t += BEAT / 2; beat += 0.5; continue
        low = bool(s['flags'].get('low')); intro = t - t0 < 2 * BAR
        sec_b = int(beat // 16) % 2 == 1                 # A (I–V–vi–IV) and B (vi–IV–I–V) alternate every 4 bars
        bi = int(beat // 4) % 4; pos = beat % 4; ch = (CHORDS_B if sec_b else CHORDS)[bi]; root = (ROOTS_B if sec_b else ROOTS)[bi]
        if pos == 0: B.add(t, keys([n - 12 for n in ch[:3]], BAR), 0.8 if not low else 1.0, 0.2)
        # uke strum pattern on eighths: D . D U . U D U
        pat = {0: 'D', 1: 'D', 1.5: 'U', 2.5: 'U', 3: 'D', 3.5: 'U'}
        if pos in pat: B.add(t, strum(ch, pat[pos] == 'D', 1.0 if pat[pos] == 'D' else 0.7, 0.9), 0.9 if not low else 0.7, -0.25)
        if not low:
            if pos in (0, 2): B.add(t, kick(0.8 if not intro else 0.45))
            if pos in (1, 3) and not intro: B.add(t, clap(0.7), 1.0, 0.1); B.add(t, tamb(0.8), 1.0, -0.3)
            B.add(t, shaker(0.5), 1.0, 0.35); B.add(t + BEAT / 4, shaker(0.9), 1.0, 0.35)      # 16ths, offbeat accent
            if pos in (0, 1.5, 2, 3.5) and not intro:
                n = root + (12 if pos in (1.5, 3.5) else 0); B.add(t, bass(n, BEAT * 0.9), 1.0)
        # glockenspiel hook every other 2 bars (and over low sections, softly)
        hb = beat % 16
        if hb < 8:                                       # hook in the first 2 bars of each 4-bar phrase only
            for hbt, n in (HOOK_B if sec_b else HOOK):
                if abs(hb - hbt) < 1e-6: B.add(t, glock(n), 0.3 if low else 0.42, 0.3)
        t += BEAT / 2; beat += 0.5
    for s in tl:                                        # lifts into drops
        if s['flags'].get('drop'):
            B.add(s['t'], crash(1.0), 1.0, -0.2)
            for k in range(4): B.add(s['t'] - BEAT + k * BEAT / 4, clap(0.5 + 0.12 * k), 1.0, 0.1)
    # end card: bright final chord, glock arpeggio, crash, gentle tail
    B.add(end_t, kick(1.0)); B.add(end_t, crash(1.2)); B.add(end_t, strum((62, 66, 69, 74, 78), True, 1.3, 2.5), 1.0)
    B.add(end_t, bass(38, 2.0), 1.0)
    for k, n in enumerate((74, 78, 81, 86)): B.add(end_t + 0.15 * k, glock(n, 2.0), 0.7, 0.3 * (-1) ** k)
    x = room(B.x)
    for s in tl:                                        # silence segments: music stops dead
        if s['kind'] == 'silence':
            i0, i1 = int(s['t'] * SR), int((s['t'] + s['d']) * SR); f = int(0.01 * SR)
            x[i0 - f:i0] *= np.linspace(1, 0, f)[:, None]; x[i0:i1] = 0
    x = x[:int(total * SR)]; f = int(1.6 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.2) * 0.89
    write(x, out, 'loudnorm=I=-16:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')
