"""Assemble the clean VO from timeline2.json: every kept take is cut from the raw recording (with 15 ms
fades so cuts don't click), laid at its planned time, then cleaned (rumble cut, denoise, de-ess,
compress, loudness -16 LUFS).
usage: vo_build.py <workdir>      reads vo_raw.wav + timeline2.json, writes vo_clean.wav + vo_clean.m4a
"""
import json, subprocess, sys
import numpy as np
WD = sys.argv[1]; SR = 48000
T = json.load(open(f'{WD}/timeline2.json'))
raw = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{WD}/vo_raw.wav', '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                                   capture_output=True, check=True).stdout, dtype=np.int16).astype(np.float32)
out = np.zeros(int((T['total'] + 1) * SR), np.float32)
F = int(0.015 * SR); ramp = np.linspace(0, 1, F, dtype=np.float32)
n = 0
for b in T['beats']:
    for p in b['pieces']:
        a, e = (int(x * SR) for x in p['src']); seg = raw[a:e].copy()
        seg[:F] *= ramp; seg[-F:] *= ramp[::-1]
        at = int(p['at'] * SR); out[at:at + len(seg)] += seg; n += 1
out = out[:int(T['total'] * SR)]
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-',
                '-af', 'highpass=f=80,afftdn=nr=12:nf=-40,equalizer=f=6500:t=q:w=2:g=-3,'
                       'acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,loudnorm=I=-16:TP=-1.5:LRA=7',
                '-ar', str(SR), f'{WD}/vo_clean.wav'], input=np.clip(out, -32768, 32767).astype(np.int16).tobytes(), check=True)
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{WD}/vo_clean.wav', '-c:a', 'aac', '-b:a', '192k', f'{WD}/vo_clean.m4a'], check=True)
print(f'{n} takes, {T["total"]:.1f}s', file=sys.stderr)
