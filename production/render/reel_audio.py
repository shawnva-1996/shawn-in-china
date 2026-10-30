"""Reel audio: the approved VO lines placed on the reel timeline, and the trailer score as the bed, dipped 4 dB
under the voice (the score already leaves room for it; a trailer bed should stay big).
usage: reel_audio.py <workdir> <vo_clean.wav> <score.wav>     reads reel.json, writes vo_clean.m4a + bed.m4a (mix2.py names)
"""
import json, subprocess, sys
import numpy as np
WD, VOSRC, SCORE = sys.argv[1:4]; SR = 48000
R = json.load(open(f'{WD}/reel.json')); N = int(R['total'] * SR)
def load(p, ch):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                                        capture_output=True, check=True).stdout, np.float32).reshape(-1, ch).copy()
def enc(x, ch, path):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', str(ch), '-i', '-', '-af', 'alimiter=limit=0.89:level=false',
                    '-c:a', 'aac', '-b:a', '256k', path], input=x.astype(np.float32).tobytes(), check=True)
src = load(VOSRC, 1)[:, 0]; vo = np.zeros(N, np.float32); F = int(0.012 * SR)
for v in R['vo']:
    a, e = (int(x * SR) for x in v['src']); x = src[a:e].copy(); x[:F] *= np.linspace(0, 1, F); x[-F:] *= np.linspace(1, 0, F)
    i = int(v['at'] * SR); vo[i:i + len(x)] += x[:N - i]
enc(vo, 1, f'{WD}/vo_clean.m4a')
bed = load(SCORE, 2)[:N]; bed = np.pad(bed, ((0, N - len(bed)), (0, 0)))
hop = SR // 100; env = np.array([np.sqrt(np.mean(vo[i:i + hop] ** 2)) for i in range(0, N, hop)])
talk = np.convolve((20 * np.log10(env + 1e-9) > -38).astype(np.float32), np.ones(20) / 20, 'same') > 0.05
g = np.where(talk, 10 ** (-4 / 20), 1.0).astype(np.float32)
for i in range(1, len(g)): g[i] = g[i - 1] + (g[i] - g[i - 1]) * (0.25 if g[i] < g[i - 1] else 0.06)
bed *= np.interp(np.arange(N), np.arange(len(g)) * hop, g)[:, None].astype(np.float32) * 0.8
enc(bed, 2, f'{WD}/bed.m4a')
print(f'reel audio {R["total"]:.1f}s, {len(R["vo"])} lines', file=sys.stderr)
