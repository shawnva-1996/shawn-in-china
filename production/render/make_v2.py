"""One-shot driver for the v2 render on the machine that holds the footage.
Run from the kit folder:  ROOT=<shoot folder> WORKERS=3 python3 make_v2.py
Steps: probe the clips -> plan (must match the timeline the overlays were drawn for) -> per-shot jobs -> render
-> mix -> QA sheets + small preview -> delete the segments. Each step is skipped when its output exists, so it
can be re-run after an interruption."""
import json, os, subprocess, sys, time
K = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.setdefault('ROOT', os.path.abspath(K + '/../..'))
SEG = os.environ.setdefault('SEG', K + '/seg'); PY = sys.executable
FINAL = ROOT + '/final/shawn_in_china_ep1_chongqing_v2.mp4'
def run(*a): print('>>', ' '.join(a[1:3]), flush=True); subprocess.run(list(a), check=True, cwd=K)
t0 = time.time()
if not os.path.exists(K + '/meta_probe.json'): run(PY, 'probe.py', ROOT, 'need2.txt', 'meta_probe.json')
meta = json.load(open(K + '/meta_guess.json')); meta.update(json.load(open(K + '/meta_probe.json')))
bad = [f for f in open(K + '/need2.txt').read().split('\n') if f and meta.get(f, {}).get('kind') not in ('video', 'image')]
assert not bad, f'unreadable clips: {bad}'
json.dump(meta, open(K + '/meta.json', 'w'))
run(PY, 'plan2.py', K)
ref = json.load(open(K + '/timeline_ref.json')); new = json.load(open(K + '/timeline2.json'))
drift = max(abs(a['span'][0] - b['span'][0]) for a, b in zip(ref['beats'], new['beats']))
assert drift < 0.01 and abs(ref['total'] - new['total']) < 0.01, f'timeline drifted {drift:.3f}s from the overlays'
run(PY, 'jobs2.py', K)
if not os.path.exists(FINAL):
    run(PY, 'runner.py', K + '/jobs2.json', '1e9')
    os.makedirs(ROOT + '/final', exist_ok=True)
    run(PY, 'mix2.py', K + '/jobs2.json', FINAL)
for a, b in [('captions_en.srt', 'captions_en_v2.srt'), ('chapters.txt', 'chapters_v2.txt')]:
    open(f'{ROOT}/final/{b}', 'w').write(open(f'{K}/{a}').read())
# QA: one still per shot (middle frame) on contact sheets, plus a 360p preview
os.makedirs(K + '/qa', exist_ok=True)
for k, s in enumerate(new['shots']):
    p = f"{K}/qa/s{k:03d}.jpg"
    if not os.path.exists(p):
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f"{s['t'] + s['d'] / 2:.2f}", '-i', FINAL, '-frames:v', '1', '-vf', 'scale=480:-2', p])
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', FINAL, '-vf', 'scale=640:-2', '-c:v', 'libx264', '-crf', '32', '-preset', 'veryfast',
                '-c:a', 'aac', '-b:a', '64k', K + '/qa/preview.mp4'], check=True)
for f in os.listdir(SEG): os.remove(os.path.join(SEG, f))
os.rmdir(SEG)
print(f'done in {time.time() - t0:.0f}s ->', FINAL, os.path.getsize(FINAL) // 2**20, 'MB')
