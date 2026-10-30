"""Trailer audio: the VO is cut from the main episode's clean VO (same ranges as the picture), the music bed runs
hotter than in the long video (Reels are watched loud and fast), and the SFX come from the main edit's cues plus
a whoosh on every jump between moments.
usage: trailer_audio.py <workdir> <music.wav> <sfx_dir> <outdir>
reads trailer.json + vo_clean.wav, writes <outdir>/vo_clean.m4a and <outdir>/bed.m4a (names mix2.py expects)
"""
import json, os, subprocess, sys
import numpy as np
WD, MUS, SFX, OUT = sys.argv[1:5]; os.makedirs(OUT, exist_ok=True)
SR = 48000; T = json.load(open(f'{WD}/trailer.json')); N = int(T['total'] * SR)
def load(p, ch=2):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                                        capture_output=True, check=True).stdout, np.float32).reshape(-1, ch).copy()
src = load(f'{WD}/vo_clean.wav', 1)[:, 0]; vo = np.zeros(N, np.float32); F = int(0.01 * SR); ramp = np.linspace(0, 1, F, dtype=np.float32)
for s in T['segs']:
    a, e = (int(x * SR) for x in s['src']); x = src[a:e].copy(); x[:F] *= ramp; x[-F:] *= ramp[::-1]
    i = int(s['t'] * SR); vo[i:i + len(x)] += x[:N - i]
def enc(x, ch, path):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-', '-af', 'alimiter=limit=0.89',
                    '-c:a', 'aac', '-b:a', '192k', path], input=x.astype(np.float32).tobytes(), check=True)
enc(vo, 1, f'{OUT}/vo_clean.m4a')
m = load(MUS); m = np.concatenate([m] * (N // len(m) + 1))[:N]
hop = SR // 100; env = np.array([np.sqrt(np.mean(vo[i:i + hop] ** 2)) for i in range(0, N, hop)])
talk = np.convolve((20 * np.log10(env + 1e-9) > -38).astype(np.float32), np.ones(25) / 25, 'same') > 0.05
g = np.where(talk, 10 ** (-11 / 20), 10 ** (-3 / 20)).astype(np.float32)
for i in range(1, len(g)): g[i] = g[i - 1] + (g[i] - g[i - 1]) * (0.12 if g[i] < g[i - 1] else 0.03)
gain = np.interp(np.arange(N), np.arange(len(g)) * hop, g).astype(np.float32) * 0.6
fo = int(1.5 * SR); gain[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
bed = m * gain[:, None]
LEVEL = dict(pop=0.32, tick=0.35, ding=0.4, boing=0.45, whoosh=0.4, swoosh=0.4, impact=0.5, riser=0.4, chaching=0.45, sparkle=0.4, shutter=0.5)
cues = [(f['t'], f['arg']) for s in T['segs'] for f in s['fx'] if f['kind'] == 'sfx']
cues += [(s['t'] - 0.15, 'swoosh') for s in T['segs'][4:]] + [(T['end'][0] - 0.2, 'whoosh'), (T['end'][0] + 0.9, 'pop')]
cache = {}
for t, name in cues:
    if name not in cache: cache[name] = load(f'{SFX}/{name}.wav')
    x = cache[name] * LEVEL.get(name, 0.4); i = max(0, int(t * SR)); j = min(N, i + len(x)); bed[i:j] += x[:j - i]
enc(bed, 2, f'{OUT}/bed.m4a')
print(f'trailer audio {T["total"]:.1f}s, {len(cues)} sfx', file=sys.stderr)
