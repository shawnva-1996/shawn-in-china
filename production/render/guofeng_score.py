"""Chinese-style (国风) trap bed for the day reels, in the spirit of the Chongqing night-motorbike videos:
guzheng plucks and glissandi, a dizi-style flute hook with slides, woodblock, gong and big drums over a modern
808 + trap-hat beat, with a motorbike-rev riser into each drop. D major pentatonic (gong mode), 100 BPM so the beat
lands on the reels' 0.3 s cut grid. Same timeline contract as reels_score.score() / travel_score.score():
music stops on silence segments, strips to guzheng + flute on 'low' segments, rev + gong on 'drop' segments,
gong and glissando on the end card.
score(timeline, total, end_t, out_wav)
"""
import numpy as np
from trailer_score import SR, BEAT, hz, tt, lp, bp, write, fftconvolve, taiko

rng = np.random.default_rng(23)
BAR = 4 * BEAT
PENTA = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86]                  # D major pentatonic D E F# A B
ROOTS = [38, 35, 33, 40]                                              # D, B, A, E (808)
FIFTHS = [(50, 57, 62), (47, 54, 59), (45, 52, 57), (52, 59, 64)]      # open fifths for the pad (no western thirds)
HOOK_A = [(0, 81, 1.0), (1, 78, 0.5), (1.5, 76, 0.5), (2, 78, 1.0), (3, 74, 1.0), (4, 76, 0.5), (4.5, 78, 0.5), (5, 81, 1.5), (6.5, 83, 0.5), (7, 81, 1.0)]
HOOK_B = [(0, 86, 1.0), (1, 83, 1.0), (2, 81, 0.5), (2.5, 78, 0.5), (3, 81, 1.0), (4, 78, 1.0), (5, 76, 0.5), (5.5, 74, 0.5), (6, 76, 2.0)]
SHIFT = [0, -1, -2, 1]                                                # guzheng figure per bar: D, B, A, E areas
ZHENG = [(0, 74), (0.5, 78), (1, 81), (1.5, 78), (2, 83), (2.5, 81), (3, 78), (3.5, 76)]   # 8th-note guzheng figure

def ks(f, d, bright, decay):
    n = int(d * SR); p = max(2, int(SR / f)); b = lp(rng.uniform(-1, 1, p), bright)
    out = np.zeros(n); k = 0
    while k < n:
        m = min(p, n - k); out[k:k + m] = b[:m]; b = decay * 0.5 * (b + np.roll(b, -1)); k += p
    return out

def zheng(n, d=1.6, g=1.0, bend=0.0, bend_at=0.25):
    """guzheng: bright, twangy steel-string pluck (two slightly detuned strings, plectrum click);
    bend = semitones of the pressed-string slide (按音), starting bend_at seconds after the pluck"""
    m = int(d * SR); env = np.exp(-np.arange(m) / SR / 1.1)
    x = (ks(hz(n), d, 9000, 0.9985) + 0.6 * ks(hz(n) * 1.003, d, 9000, 0.9985)) * env
    if bend:
        t = np.arange(m) / SR; rate = 2 ** (bend / 12 * np.clip((t - bend_at) / 0.18, 0, 1))
        x = np.interp(np.cumsum(rate) - rate[0], np.arange(m), x)
    click = bp(rng.standard_normal(int(0.006 * SR)), 2000, 9000) * 0.5
    x[:len(click)] += click
    return g * 0.6 * (x + 0.8 * bp(x, 1800, 6000) + 0.3 * bp(x, 250, 700))

def yao(n, d, g=1.0, rate=13.0):
    """guzheng / pipa tremolo (摇指 / 轮指): fast repeated plucks of one note"""
    x = np.zeros(int((d + 0.6) * SR)); k = 0
    while k / rate < d:
        y = zheng(n, 0.6, g * (0.55 + 0.15 * (k % 2)) * min(1, (k + 1) / 4)); i = int(k / rate * SR)
        x[i:i + len(y)] += y[:len(x) - i]; k += 1
    return x

def gliss(t0, notes, B, g=1.0, step=0.035):
    for k, n in enumerate(notes): B.add(t0 + k * step, zheng(n, 1.3, 0.5 * g), 1.0, -0.6 + 1.2 * k / max(1, len(notes) - 1))

def dizi(notes, g=1.0):
    """bamboo flute (笛子): breathy, buzzing reed-membrane tone (笛膜), grace notes, scoops and vibrato.
    notes = [(start, midi, dur)] in seconds"""
    ev = []
    for s, n, l in notes:                                             # 打音 grace note: upper scale neighbour flicked in
        if l >= 0.35 and n in PENTA and PENTA.index(n) + 1 < len(PENTA) and rng.random() < 0.6:
            ev += [(s, PENTA[PENTA.index(n) + 1], 0.045), (s + 0.045, n, l - 0.045)]
        else: ev.append((s, n, l))
    d = max(s + l for s, _, l in ev) + 0.3; t = tt(d); f = np.zeros(len(t)); a = np.zeros(len(t))
    for s, n, l in ev:
        i0, i1 = int(s * SR), int((s + l) * SR); f[i0:i1] = hz(n); a[i0:i1] = 1
    for i in range(1, len(f)):
        if f[i] == 0: f[i] = f[i - 1]
    f[f == 0] = hz(ev[0][1])
    f = lp(f, 30, 1)                                                  # quick slides between notes
    vib = 1 + 0.012 * np.sin(2 * np.pi * 6.0 * t) * np.clip((t % 1.0) / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    env = lp(a, 40, 1) * (1 + 0.1 * lp(rng.standard_normal(len(t)), 8))
    tone = sum(h * np.sin(k * ph) for k, h in ((1, 1), (2, 0.55), (3, 0.4), (4, 0.22), (5, 0.15), (6, 0.08)))
    buzz = bp(np.tanh(3 * tone), 2500, 7500) * (0.35 + 0.15 * lp(rng.standard_normal(len(t)), 30))
    breath = bp(rng.standard_normal(len(t)), 1200, 8000) * 0.18
    return g * 0.2 * env * (tone + buzz + breath)

def xiaoluo(g=1.0):
    """small Peking-opera gong (小锣): bright 'tang' whose pitch glides UP after the strike"""
    t = tt(0.9); f = 620 * (1 + 0.18 * (1 - np.exp(-t / 0.12)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.4 * np.sin(2.4 * ph) + 0.2 * np.sin(3.9 * ph)
    x += 0.3 * bp(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t / 0.02)
    return g * 0.28 * x * np.exp(-t / 0.35)

def cha(g=1.0, d=0.6):
    """small cymbals (铙钹): metallic crash ring"""
    t = tt(d); x = bp(rng.standard_normal(len(t)), 3000, 12000) + 0.3 * sum(np.sin(2 * np.pi * f * t) for f in (3150, 4420, 5870))
    return g * 0.16 * x * np.exp(-t / (d * 0.3))

def bangu(g=1.0):
    """clapper drum (板鼓): very dry, high, cracking"""
    t = tt(0.06); return g * 0.4 * (bp(rng.standard_normal(len(t)), 1800, 6000) + 0.6 * np.sin(2 * np.pi * 1600 * t)) * np.exp(-t / 0.01)

def k808(n, d, g=1.0, slide=0):
    t = tt(d); f = hz(n) * (1 + slide * np.clip((t - d * 0.6) / (d * 0.4), 0, 1)) * (1 + 1.5 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return g * 0.6 * np.tanh(1.8 * x) * np.minimum(1, t / 0.004) * np.exp(-t / 0.9)

def kick(g=1.0):
    t = tt(0.3); f = 48 + 90 * np.exp(-t / 0.025)
    return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.1)

def snare(g=1.0):
    t = tt(0.3); return g * (0.3 * bp(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t / 0.07) + 0.25 * np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.03))

def hat(g=1.0, open_=False):
    t = tt(0.25 if open_ else 0.05); return g * 0.1 * bp(rng.standard_normal(len(t)), 7000, 15000) * np.exp(-t / (0.08 if open_ else 0.012))

def woodblock(g=1.0, hi=True):
    t = tt(0.08); f = 1250 if hi else 900
    return g * 0.3 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018)

def gong(g=1.0, d=4.0):
    t = tt(d); x = sum(np.sin(2 * np.pi * f * t * (1 + 0.02 * np.exp(-t / 0.4)) + rng.uniform(0, 6)) * a for f, a in
                       ((110, 1), (167, 0.6), (231, 0.5), (298, 0.35), (414, 0.25), (530, 0.15)))
    x += 0.4 * bp(rng.standard_normal(len(t)), 300, 3000) * np.exp(-t / 0.3)
    return g * 0.25 * x * np.minimum(1, t / 0.01) * np.exp(-t / 1.6)

def rev(d=1.6, g=1.0):
    """a motorbike rev rising into the drop: pulsing low saw climbing in pitch, through a growing filter"""
    t = tt(d); f = 55 * 2 ** (2.2 * (t / d) ** 1.6); ph = np.cumsum(f) / SR
    x = 2 * (ph % 1) - 1; x *= 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * f * 0.5 * t / 55 * 9))   # combustion pulse
    x = np.tanh(2.5 * x) + 0.3 * bp(rng.standard_normal(len(t)), 200, 2000)
    w = (t / d) ** 2; out = (1 - w) * lp(x, 300) + w * lp(x, 3800)        # opening filter
    return g * 0.35 * out * np.clip(t / 0.15, 0, 1) * np.clip((d - t) / 0.05, 0, 1)

def pad(notes, d, g=1.0):
    t = tt(d); x = sum(np.sin(2 * np.pi * hz(n) * t) + 0.3 * np.sin(2 * np.pi * hz(n) * 1.003 * t) for n in notes)
    return g * 0.05 * x * np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4 + 1e-3)

class Bus:
    def __init__(s, total): s.x = np.zeros((int((total + 5) * SR), 2))
    def add(s, at, y, g=1.0, pan=0.0):
        i = int(at * SR)
        if i < 0 or i >= len(s.x): return
        y = y[:len(s.x) - i] * g
        s.x[i:i + len(y), 0] += y * ((1 - pan) / 2) ** 0.5; s.x[i:i + len(y), 1] += y * ((1 + pan) / 2) ** 0.5

def hall(x, wet=0.25):
    n = int(2.0 * SR); te = np.arange(n) / SR; y = x.copy()
    for k in (0, 1):
        ir = lp(rng.standard_normal(n), 5500) * np.exp(-te / 0.6); ir[:int(0.02 * SR)] = 0; ir /= np.sqrt(np.sum(ir ** 2))
        y[:, k] += wet * fftconvolve(x[:, k], ir)[:len(x)]
    return y

def score(tl, total, end_t, out):
    B = Bus(total); D = Bus(total); t0 = tl[0]['t']                   # B: melodic (reverb), D: drums (dry)
    def seg_at(t):
        for s in tl:
            if s['t'] - 1e-6 <= t < s['t'] + s['d']: return s
    gliss(t0, PENTA[:9], B, 1.0); B.add(t0, gong(0.8))
    beat, t = 0.0, t0
    while t < end_t - 1e-6:
        s = seg_at(t)
        if s is None or s['kind'] == 'silence': t += BEAT / 2; beat += 0.5; continue
        low = bool(s['flags'].get('low')); intro = t - t0 < 2 * BAR
        bi = int(beat // 4) % 4; pos = beat % 4; sec_b = int(beat // 16) % 2 == 1; ph = beat % 16
        if pos == 0: B.add(t, pad(FIFTHS[bi], BAR + 0.3), 0.5 if not low else 0.8)
        if low and pos == 0: B.add(t, yao(PENTA[5 + SHIFT[bi]], BAR - 0.2, 0.7), 1.0, 0.3)   # tremolo drone under quiet beats
        # guzheng 8th-note figure, transposed to the bar's root area
        zn = dict(ZHENG).get(pos)
        if zn and not (low and pos % 1):
            zn = PENTA[min(len(PENTA) - 1, max(0, PENTA.index(zn) + SHIFT[bi]))]   # move by scale steps, stays pentatonic
            B.add(t, zheng(zn, 1.4, 0.75 if pos % 1 else 0.95, bend=(2 if (pos == 3 and bi in (1, 3)) else 0)), 1.0, -0.35)
        # flute hook on the first two bars of each 4-bar phrase
        if ph in (0, 8) and not intro:
            H = HOOK_B if sec_b else HOOK_A
            if ph == 0: B.add(t, dizi([(b * BEAT, n, l * BEAT) for b, n, l in H]), 0.8 if low else 1.0, 0.25)
        if not low and not intro:
            if pos in (0, 2.5): D.add(t, kick(0.9))
            if pos in (1, 3): D.add(t, snare(0.9), 1.0, 0.05); D.add(t, bangu(0.6), 1.0, 0.4)
            if pos == 3 and bi in (1, 3): D.add(t, xiaoluo(0.9), 1.0, 0.25)        # opera-gong 'tang' every 2 bars
            if pos in (0.5, 1.5, 2.5, 3.5): D.add(t, woodblock(0.35, pos in (0.5, 2.5)), 1.0, -0.45)
            if pos == 0 and bi == 0: D.add(t, cha(0.8), 1.0, -0.2)
            hats = 4 if (bi == 3 and pos >= 3) else 2                 # 16ths, a roll into each 4th bar's turnaround
            for q in range(hats): D.add(t + q * BEAT / 2 / hats, hat(0.9 if q == 0 else 0.6), 1.0, -0.3)
            if pos == 0: D.add(t, k808(ROOTS[bi], BAR * 0.9, 0.9, slide=(0.12 if bi == 3 else 0)))
            if pos == 2 and bi in (1, 3): D.add(t, k808(ROOTS[bi] + 12, BEAT * 0.8, 0.5))
        elif intro and not low:
            if pos in (0, 1, 2, 3): D.add(t, woodblock(0.6, pos in (0, 2)), 1.0, 0.3)
            if pos == 3 and bi in (1, 3): D.add(t, xiaoluo(0.7), 1.0, 0.25)
            if pos == 3.5 and t - t0 > 2 * BAR - BEAT: B.add(t, gong(0.4))
        t += BEAT / 2; beat += 0.5
    for s in tl:                                                      # drops: motorbike rev, then gong + big drum + glissando
        if s['flags'].get('drop'):
            B.add(s['t'] - 1.6, rev(1.6), 1.0, -0.1)
            B.add(s['t'], gong(1.0)); D.add(s['t'], taiko(1.0), 1.0); gliss(s['t'], PENTA[::-1][:8], B, 0.8)
    # end card: glissando up, gong, big drums, a final held flute note
    gliss(end_t, PENTA, B, 1.0, 0.03); B.add(end_t, gong(1.3, 5.0)); D.add(end_t, taiko(1.0)); D.add(end_t + BEAT, taiko(0.7))
    D.add(end_t, k808(38, 2.5, 1.0)); B.add(end_t + 0.4, dizi([(0, 81, 0.4), (0.4, 86, 2.0)]), 1.0, 0.2)
    x = hall(B.x) + D.x + 0.15 * hall(D.x, 0.5)
    for s in tl:                                                      # silence segments: music stops dead
        if s['kind'] == 'silence':
            i0, i1 = int(s['t'] * SR), int((s['t'] + s['d']) * SR); f = int(0.01 * SR)
            x[i0 - f:i0] *= np.linspace(1, 0, f)[:, None]; x[i0:i1] = 0
    x = x[:int(total * SR)]; f = int(1.8 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.3) * 0.89
    write(x, out, 'loudnorm=I=-16:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')
