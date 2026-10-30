"""Chinese-style trap bed from a produced track (music/guofeng_ai_100bpm.flac: a Lyria RealTime take, pipa, guzheng,
erhu, 808 and trap hats, stretched to exactly 100 BPM), laid onto a reel's timeline so its beats land on the 0.3 s
cut grid. Same timeline contract as reels_score.score() / guofeng_score.score(): music stops dead on silence segments,
dips on 'low' segments, a motorbike rev + gong + big drum on 'drop' segments, and a gong + drum hit on the end card.
score(timeline, total, end_t, out_wav)
"""
import os, subprocess
import numpy as np
from trailer_score import SR, write, taiko, lp
from guofeng_score import rev, gong, Bus

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music', 'guofeng_ai_100bpm.flac')
PHASE = 0.07                                                          # first beat in SRC (librosa beat fit)

def load(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(float)

def score(tl, total, end_t, out):
    src = load(SRC); t0 = tl[0]['t']
    x = np.zeros((int((total + 1) * SR), 2)); i0 = int(t0 * SR); s0 = int(PHASE * SR)
    n = min(len(x) - i0, len(src) - s0); x[i0:i0 + n] = src[s0:s0 + n]
    f = int(0.03 * SR); x[i0:i0 + f] *= np.linspace(0, 1, f)[:, None]
    for s in tl:                                                      # quiet beats: -6 dB and darker, back up after
        if s['flags'].get('low'):
            a, b = int(s['t'] * SR), int((s['t'] + s['d']) * SR)
            x[a:b] = 0.5 * np.stack([lp(x[a:b, k], 2500) for k in (0, 1)], 1)
    B = Bus(total)
    for s in tl:
        if s['flags'].get('drop'):
            B.add(s['t'] - 1.6, rev(1.6), 0.8, -0.1); B.add(s['t'], gong(0.8)); B.add(s['t'], taiko(0.9))
    B.add(end_t, gong(1.0, 5.0)); B.add(end_t, taiko(0.9)); B.add(end_t + 0.6, taiko(0.6))
    x[:len(B.x)] += B.x[:len(x)]
    for s in tl:                                                      # silence segments: music stops dead
        if s['kind'] == 'silence':
            a, b = int(s['t'] * SR), int((s['t'] + s['d']) * SR); f = int(0.01 * SR)
            x[a - f:a] *= np.linspace(1, 0, f)[:, None]; x[a:b] = 0
            g = int(0.02 * SR); x[b:b + g] *= np.linspace(0, 1, g)[:, None]
    x = x[:int(total * SR)]; f = int(2.2 * SR); x[-f:] *= np.linspace(1, 0, f)[:, None] ** 1.5
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    write(x, out, 'loudnorm=I=-16:TP=-1.0:LRA=11,aresample=48000,alimiter=limit=0.89:level=false')
