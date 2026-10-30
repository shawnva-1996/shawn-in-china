"""Build the music + sound-effect bed for the v2 render (everything except the clips' own sound and the VO).
Music: track A loops (2 s crossfades) until the 'switch' beat, then track B; the music ducks under the VO.
SFX: every fx 'sfx' cue from timeline2.json, plus a whoosh on each chapter card.
usage: bed_build.py <workdir> <music_a.wav> <music_b.wav> <sfx_dir> [switch_beat=B65]
reads timeline2.json + vo_clean.wav, writes bed.m4a (stereo 48 kHz)
"""
import json, subprocess, sys
import numpy as np
WD, MA, MB, SFX = sys.argv[1:5]; SWITCH = sys.argv[5] if len(sys.argv) > 5 else 'B65'
SR = 48000; T = json.load(open(f'{WD}/timeline2.json')); TOT = T['total']; N = int(TOT * SR)
def load(p, ch=2):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                                        capture_output=True, check=True).stdout, np.float32).reshape(-1, ch).copy()
def loop_to(x, n, xf=2.0):
    k = int(xf * SR); fade = np.linspace(0, 1, k, dtype=np.float32)[:, None]; out = x.copy()
    while len(out) < n:
        out = np.concatenate([out[:-k], out[-k:] * (1 - fade) + x[:k] * fade, x[k:]])
    return out[:n]
sw = next(b['span'][0] for b in T['beats'] if b['id'] == SWITCH)
mus = np.zeros((N, 2), np.float32)
a = loop_to(load(MA), int((sw + 2) * SR)); fo = int(2 * SR)
a[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]; mus[:len(a)] += a
b = loop_to(load(MB), N - int(sw * SR)); fi = int(1.5 * SR); fe = int(4 * SR)
b[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)[:, None]; b[-fe:] *= np.linspace(1, 0, fe, dtype=np.float32)[:, None]
mus[int(sw * SR):int(sw * SR) + len(b)] += b
# duck: music sits at -15 dB under speech, -6 dB in the gaps (smoothed VO envelope, 10 ms hop)
vo = load(f'{WD}/vo_clean.wav', 1)[:N, 0]; hop = SR // 100
env = np.array([np.sqrt(np.mean(vo[i:i + hop] ** 2)) for i in range(0, len(vo), hop)])
talk = (20 * np.log10(env + 1e-9) > -38).astype(np.float32)
talk = np.convolve(talk, np.ones(25) / 25, 'same') > 0.05              # bridge short gaps between words
g = np.where(talk, 10 ** (-15 / 20), 10 ** (-6 / 20)).astype(np.float32)
for i in range(1, len(g)):                                               # attack 80 ms, release 500 ms
    c = 0.12 if g[i] < g[i - 1] else 0.02; g[i] = g[i - 1] + (g[i] - g[i - 1]) * c
gain = np.interp(np.arange(N), np.arange(len(g)) * hop, g).astype(np.float32)
mus *= gain[:, None] * 0.55
# sfx
LEVEL = dict(pop=0.32, tick=0.35, ding=0.4, boing=0.45, whoosh=0.45, swoosh=0.45, impact=0.5, riser=0.4, chaching=0.45, sparkle=0.4, shutter=0.5)
cache = {}; sfx = np.zeros((N, 2), np.float32); cues = [(f['t'], f['arg']) for f in T['fx'] if f['kind'] == 'sfx']
cues += [(f['t'] - 0.2, 'whoosh') for f in T['fx'] if f['kind'] == 'chapter']
for t, name in cues:
    if name not in cache: cache[name] = load(f'{SFX}/{name}.wav')
    x = cache[name] * LEVEL.get(name, 0.4); i = max(0, int(t * SR)); j = min(N, i + len(x)); sfx[i:j] += x[:j - i]
bed = mus + sfx
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'alimiter=limit=0.7',
                '-c:a', 'aac', '-b:a', '192k', f'{WD}/bed.m4a'], input=bed.tobytes(), check=True)
print(f'bed {TOT:.1f}s, switch at {sw:.1f}s, {len(cues)} sfx', file=sys.stderr)
