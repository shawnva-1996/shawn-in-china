"""Synthesise the channel's sound-effect kit (no licences needed). usage: make_sfx.py <outdir>"""
import numpy as np, wave, sys, os
SR = 48000
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)
def t(d): return np.arange(int(SR * d)) / SR
def env(n, a, r, shape=4):
    e = np.ones(n); ai = int(SR * a); ri = int(SR * r)
    if ai: e[:ai] = np.linspace(0, 1, ai) ** 2
    if ri: e[-ri:] *= np.linspace(1, 0, ri) ** shape
    return e
def bandsweep(x, f0, f1, q=2.0):
    """time-varying 2-pole resonant band-pass (state variable filter)"""
    y = np.zeros_like(x); lp = bp = 0.0
    fs = np.geomspace(f0, f1, len(x))
    for i, s in enumerate(x):
        f = 2 * np.sin(np.pi * fs[i] / SR); hp = s - lp - bp / q
        bp += f * hp; lp += f * bp; y[i] = bp
    return y
def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); p = 0.0
    for i, s in enumerate(x): p = (1 - a) * s + a * p; y[i] = p
    return y
def save(name, x, pan_sweep=False):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    if pan_sweep:
        p = np.linspace(-0.8, 0.8, len(x)); L = x * np.sqrt((1 - p) / 2); R = x * np.sqrt((1 + p) / 2)
    else: L = R = x
    st = (np.stack([L, R], 1) * 32767).astype(np.int16)
    with wave.open(f'{out}/{name}.wav', 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
# whoosh: swept noise, rises then falls
n = rng.standard_normal(len(t(0.7)))
save('whoosh', bandsweep(n, 300, 3500, 1.5) * np.sin(np.linspace(0, np.pi, len(n))) ** 1.5, pan_sweep=True)
n = rng.standard_normal(len(t(0.35)))
save('swoosh', bandsweep(n, 900, 6000, 1.2) * np.sin(np.linspace(0, np.pi, len(n))) ** 2, pan_sweep=True)
# pop: quick pitch drop
tt = t(0.14); f = 1100 * np.exp(-tt * 28) + 240
save('pop', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38))
# ding: bell partials
tt = t(1.6); fr = [1318.5, 2637, 3950, 5280 * 1.01]
save('ding', sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * (2.2 + k * 1.6)) / (k + 1) for k, f in enumerate(fr)) * env(len(tt), 0.002, 0.05))
# tick: tiny click for counters
tt = t(0.035); save('tick', rng.standard_normal(len(tt)) * np.exp(-tt * 260) + np.sin(2 * np.pi * 3200 * tt) * np.exp(-tt * 200))
# impact: sub drop + noise burst
tt = t(1.8); f = 95 * np.exp(-tt * 2.5) + 38
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.2)
burst = lowpass(rng.standard_normal(len(tt)), 1800) * np.exp(-tt * 14)
save('impact', sub * 1.0 + burst * 2.5)
# riser: noise + rising tone, 2 s, cut dead at the end
tt = t(2.0); f = 180 * np.exp(tt * 1.4)
r = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + bandsweep(rng.standard_normal(len(tt)), 400, 8000, 3) * 0.8
save('riser', r * (tt / 2.0) ** 2.2 * env(len(tt), 0, 0.02))
# shutter: two clicks
tt = t(0.28); x = np.zeros(len(tt))
for st in (0.0, 0.11):
    i = int(st * SR); seg = t(0.06); x[i:i + len(seg)] += lowpass(rng.standard_normal(len(seg)), 5000) * np.exp(-seg * 90)
save('shutter', x)
# boing: comedic spring
tt = t(0.7); f = 220 + 140 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt * 3) + 120 * tt
save('boing', np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.5) * env(len(tt), 0.005, 0.1))
# cha-ching: rattle + two bells
tt = t(1.2); x = lowpass(rng.standard_normal(len(tt)), 7000) * np.exp(-tt * 30) * 0.6
for st, f0 in ((0.06, 2093), (0.16, 2637)):
    i = int(st * SR); seg = tt[:len(tt) - i]
    x[i:] += (np.sin(2 * np.pi * f0 * seg) + 0.5 * np.sin(2 * np.pi * f0 * 2.76 * seg)) * np.exp(-seg * 4)
save('chaching', x)
# sparkle: quick ascending arpeggio
tt = t(0.9); x = np.zeros(len(tt))
for k, f0 in enumerate([1568, 1976, 2349, 3136]):
    i = int(k * 0.07 * SR); seg = tt[:len(tt) - i]; x[i:] += np.sin(2 * np.pi * f0 * seg) * np.exp(-seg * 7)
save('sparkle', x)
print('ok', sorted(os.listdir(out)))
