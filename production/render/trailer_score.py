"""Movie-trailer score for the ep. 1 hype reel, synthesised to the reel's timeline (reel_script_v1.md), so every
hit, stop and swell lands where the picture needs it. D minor, 100 BPM (one beat = 0.6 s = one montage cut).
Sections: A tension build (ticks, pulse, riser) / B drop + question pulse, stopping dead after the hotpot line /
C braam back in + power montage / D low pad + piano under the closing lines, door thud / E title hit + tail.
usage: trailer_score.py <out.wav> [vo_clean.wav preview.wav]      (needs numpy + scipy; runs anywhere)
with a VO file it also writes a rough preview with the reel's lines placed on the timeline.
"""
import subprocess, sys
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi, fftconvolve, sawtooth

SR = 48000; BEAT = 0.6; TOTAL = 44.0
rng = np.random.default_rng(7)
def hz(n): return 440.0 * 2 ** ((n - 69) / 12)            # MIDI note -> Hz
D1, D2, A2, D3, F3, A3 = 26, 38, 45, 50, 53, 57
def tt(d): return np.arange(int(d * SR)) / SR

# reel timeline: where each recorded line sits, (reel time, start, end in vo_clean.wav)
VO = [(0.35, 1.58, 3.33), (3.0, 10.52, 13.56), (6.9, 20.93, 23.73), (11.4, 42.76, 43.78), (13.2, 71.37, 72.08),
      (14.7, 118.84, 121.11), (18.0, 225.20, 227.22), (21.0, 400.33, 402.75), (24.6, 337.10, 338.23),
      (32.4, 476.79, 480.04), (36.6, 31.76, 34.53)]
DROP, STOP, BACK, MONT, LOW, THUD, TITLE = 10.2, 23.6, 24.6, 27.0, 31.8, 39.4, 40.8

def lp(x, f, order=2):
    return sosfilt(butter(order, min(f, SR * 0.45), 'low', fs=SR, output='sos'), x)
def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, min(hi, SR * 0.45)], 'band', fs=SR, output='sos'), x)
def sweep_lp(x, cut):
    """time-varying low-pass: cut is an array of cutoffs (one per 256-sample block)"""
    y = np.zeros_like(x); zi = None; B = 256
    for k in range(0, len(x), B):
        sos = butter(2, float(np.clip(cut[min(k // B, len(cut) - 1)], 30, SR * 0.45)), 'low', fs=SR, output='sos')
        if zi is None: zi = sosfilt_zi(sos) * 0
        y[k:k + B], zi = sosfilt(sos, x[k:k + B], zi=zi)
    return y
def saws(f, d, cents=(-8, 0, 8)):
    t = tt(d); return sum(sawtooth(2 * np.pi * f * 2 ** (c / 1200) * t + rng.uniform(0, 6)) for c in cents) / len(cents)

def braam(d=3.0, notes=(D1, D2, A2, D3, F3), bright=2600):
    t = tt(d); x = sum(saws(hz(n), d) * (1.0 if n < 40 else 0.6) for n in notes)
    x = sweep_lp(x, bright * np.exp(-np.arange(0, d, 256 / SR) / 0.7) + 220)
    env = np.minimum(1, t / 0.015) * np.exp(-t / 1.6)
    return np.tanh(2.2 * x * env) * 0.55 + np.sin(2 * np.pi * hz(D1) * t) * env * 0.5
def boom(d=2.5, f0=72, f1=31):
    t = tt(d); ph = 2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t / 0.25)) / SR
    click = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.012) * 0.6
    return np.tanh(1.6 * np.sin(ph) * np.exp(-t / 0.9)) + click
def taiko(g=1.0):
    t = tt(0.9); ph = 2 * np.pi * np.cumsum(52 + 70 * np.exp(-t / 0.04)) / SR
    skin = bp(rng.standard_normal(len(t)), 180, 900) * np.exp(-t / 0.05) * 0.5
    return g * np.tanh(1.4 * (np.sin(ph) * np.exp(-t / 0.28) + skin))
def snare(g=0.5):
    t = tt(0.4); return g * (bp(rng.standard_normal(len(t)), 900, 6000) * np.exp(-t / 0.09) + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.03) * 0.4)
def tick(hi=True):
    t = tt(0.05); return np.sin(2 * np.pi * (3200 if hi else 2400) * t) * np.exp(-t / 0.006) * 0.35 + bp(rng.standard_normal(len(t)), 2000, 8000) * np.exp(-t / 0.003) * 0.3
def stab(n, d, bright):
    t = tt(d); x = saws(hz(n), d) + 0.5 * saws(hz(n + 12), d)
    return lp(x, bright) * np.minimum(1, t / 0.004) * np.exp(-t / (d * 0.45))
def pad(notes, d, bright=700):
    t = tt(d); x = sum(saws(hz(n), d, (-11, -4, 4, 11)) for n in notes) / len(notes)
    return lp(x, bright) * np.minimum(1, t / 0.8) * np.minimum(1, (d - t) / 0.6)
def piano(n, d=3.5, g=0.35):
    t = tt(d); f = hz(n)
    x = sum(np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t * (0.9 + 0.7 * k)) / k ** 1.3 for k in range(1, 9))
    return g * x * np.minimum(1, t / 0.003)
def riser(d, f0=180, f1=900):
    t = tt(d); x = rng.standard_normal(len(t))
    noise = sweep_lp(x, np.geomspace(400, 9000, int(d * SR / 256) + 1)) * (t / d) ** 2.2 * 0.5
    ph = 2 * np.pi * np.cumsum(f0 * (f1 / f0) ** (t / d)) / SR
    return noise + np.sin(ph) * (t / d) ** 2 * 0.25 + 0.15 * np.sin(2 * ph) * (t / d) ** 3
def swell(d=0.8):
    """reverse cymbal-ish swell that ends exactly on the next hit"""
    t = tt(d); x = bp(rng.standard_normal(len(t)), 2500, 12000) * np.exp(-t / 0.35)
    return x[::-1] * 0.6

class Stem:
    def __init__(s, wet=0.25): s.x = np.zeros((int((TOTAL + 4) * SR), 2)); s.wet = wet
    def add(s, at, y, g=1.0, pan=0.0):
        i = int(at * SR); y = y[:len(s.x) - i] * g
        s.x[i:i + len(y), 0] += y * ((1 - pan) / 2) ** 0.5
        s.x[i:i + len(y), 1] += y * ((1 + pan) / 2) ** 0.5
    def out(s, cut=None, fade=0.03, start=None):
        n = int(2.6 * SR); te = np.arange(n) / SR
        ir = [lp(rng.standard_normal(n), 5000) * np.exp(-te / 0.75) for _ in (0, 1)]
        for k in (0, 1): ir[k][:int(0.02 * SR)] = 0; ir[k] /= np.sqrt(np.sum(ir[k] ** 2))
        y = s.x.copy()
        for k in (0, 1): y[:, k] += s.wet * fftconvolve(s.x[:, k], ir[k])[:len(y)]
        if cut is not None:
            i = int(cut * SR); f = int(fade * SR); y[i - f:i] *= np.linspace(1, 0, f)[:, None]; y[i:] = 0
        return y

def bar_roots(t0, t1, roots):
    """16th-note string ostinato over a chord-root cycle, one root per 4 beats"""
    out = []; k = 0; t = t0
    while t < t1 - 1e-6:
        r = roots[(k // 16) % len(roots)]; out.append((t, r + (12 if k % 4 == 2 else 0), k % 4 == 0)); k += 1; t += BEAT / 4
    return out

def write(x, path, filt):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', filt, path],
                   input=x.astype(np.float32).tobytes(), check=True)

def main():
    A, B, C, Dd, E = Stem(0.3), Stem(0.22), Stem(0.25), Stem(0.4), Stem(0.45)
    # A: tension build 0 - 10.2
    A.add(0.0, braam(4.0), 0.9); A.add(0.0, boom(), 0.9)
    A.add(0.0, pad((D2, A2), 10.2, 380), 0.35)
    for k, t in enumerate(np.arange(1.8, DROP - 0.05, BEAT / 2)): A.add(t, tick(k % 2 == 0), 0.6, 0.4 if k % 2 else -0.4)
    for t, n, acc in bar_roots(3.0, DROP, [D3, D3, 46, 45]):
        A.add(t, stab(n, 0.14, 600 + 2400 * (t - 3.0) / 7.2), 0.16 * (1.4 if acc else 1) * (0.5 + 0.5 * (t - 3.0) / 7.2), 0.25 if n % 2 else -0.25)
    for t in np.arange(6.0, DROP - 0.05, BEAT): A.add(t, taiko(0.55 + 0.05 * (t - 6)))
    A.add(DROP - 2.4, riser(2.4), 0.8); A.add(DROP - 0.8, swell(), 0.8)
    # B: the drop, then the question pulse; stops dead at STOP
    B.add(DROP, braam(3.0, bright=3400), 1.0); B.add(DROP, boom(3.0, 90, 30), 1.0); B.add(DROP, swell(0.5)[::-1], 0.5)
    for t, n, acc in bar_roots(DROP + 1.2, STOP, [D3, 46, 43, 45]):
        B.add(t, stab(n, 0.12, 1900 + 900 * (t - DROP) / 13), 0.17 * (1.35 if acc else 1), 0.3 if n % 2 else -0.3)
    for k, t in enumerate(np.arange(DROP + 1.2, STOP - 0.01, BEAT)):
        B.add(t, taiko(0.75 if k % 2 == 0 else 0.5))
        if k % 2 == 1: B.add(t, snare(0.25))
    B.add(DROP + 1.2, pad((D2, A2, D3), STOP - DROP - 1.2, 520), 0.3)
    for at, _, _ in VO[3:8]: B.add(at - 0.02, boom(1.2, 60, 34), 0.45); B.add(at - 0.02, stab(D2, 0.5, 1200), 0.35)
    for k, t in enumerate(np.arange(STOP - 2.4, STOP - 0.01, BEAT / 4)): B.add(t, snare(0.12 + 0.3 * k / 16), 1.0, 0.2 * (-1) ** k)
    B.add(STOP - 2.4, riser(2.4, 220, 1400), 0.7)
    # C: braam back in on "Is it safe at night?", then the power montage on the beat
    C.add(BACK, braam(3.5), 1.0); C.add(BACK, boom(), 0.9)
    C.add(BACK, pad((D2, A2, D3, F3), MONT - BACK, 650), 0.35)
    C.add(MONT - 1.2, riser(1.2, 300, 1500), 0.7); C.add(MONT - 0.6, swell(0.6), 0.8)
    for k, t in enumerate(np.arange(MONT, LOW - 0.01, BEAT)):
        C.add(t, taiko(0.95)); C.add(t, boom(0.8, 80, 40), 0.35); C.add(t + BEAT / 2, taiko(0.45))
        C.add(t + BEAT / 2, snare(0.35)); C.add(t, stab([D2, D2, 46 - 12, 45 - 12][(k // 2) % 4], 0.45, 2400), 0.5)
    for t, n, acc in bar_roots(MONT, LOW, [D3 + 12, 58, 55, 57]):
        C.add(t, stab(n, 0.11, 3200), 0.12 * (1.3 if acc else 1), 0.35 if n % 2 else -0.35)
    # D: the low pad under the closing lines; the door thud
    Dd.add(LOW, braam(5.0, (D1, D2, A2), 1400), 0.9); Dd.add(LOW, boom(3.0), 0.8)
    for k, (ch, d) in enumerate([((D2, A2, D3, F3), 2.4), ((46 - 12, D3, F3), 2.4), ((43 - 12, 46, D3), 2.8)]):
        Dd.add(LOW + 0.3 + 2.4 * k, pad(ch, d + 0.5, 600), 0.42)
    for at, n in [(32.2, 74), (33.4, 69), (34.6, 65), (35.8, 64), (37.0, 62)]: Dd.add(at, piano(n), 1.0, 0.2)
    for k, t in enumerate(np.arange(36.6, THUD - 0.05, BEAT / 2)): Dd.add(t, tick(k % 2 == 0), 0.45 + 0.3 * k / 10, 0.3 if k % 2 else -0.3)
    Dd.add(THUD, boom(2.2, 55, 28), 1.2); Dd.add(THUD, lp(taiko(1.0), 400), 0.8)
    # E: the title hit and the tail
    E.add(TITLE - 0.6, swell(0.6), 0.9)
    E.add(TITLE, braam(3.4, bright=3800), 1.05); E.add(TITLE, boom(3.2, 95, 28), 1.1); E.add(TITLE + 0.6, piano(74, 3.0, 0.4), 1.0)

    mix = (A.out(DROP, 0.03) + B.out(STOP, 0.012) + C.out(LOW + 0.25, 0.25) + Dd.out(THUD + 1.1, 0.6) + E.out())[:int(TOTAL * SR)]
    f = int(1.6 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.3) * 0.89

    write(mix, sys.argv[1], 'loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')

    if len(sys.argv) > 3:      # rough preview: score + the reel's VO lines, score dipped a little under the voice
        src = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[2], '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                                           capture_output=True, check=True).stdout, np.float32)
        vo = np.zeros(len(mix), np.float32); F = int(0.012 * SR)
        for at, a, e in VO:
            x = src[int(a * SR):int(e * SR)].copy(); x[:F] *= np.linspace(0, 1, F); x[-F:] *= np.linspace(1, 0, F)
            i = int(at * SR); vo[i:i + len(x)] += x
        env = np.convolve(np.abs(vo), np.ones(int(0.25 * SR)) / (0.25 * SR), 'same'); g = 1 - 0.55 * np.clip(env / 0.02, 0, 1)
        pre = mix * g[:, None] * 0.75 + vo[:, None] * 1.6
        write(pre, sys.argv[3], 'loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')
    print('score', TOTAL, 's', file=sys.stderr)

if __name__ == '__main__': main()
