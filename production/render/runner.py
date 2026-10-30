import json, os, sys, time, subprocess, concurrent.futures as cf
# ROOT = the shoot folder (default: the Mac VM mount); segments and stills go under ROOT/_work/render2
H = os.environ['HOME']; ROOT = os.environ.get('ROOT', H + '/mnt/shawn-in-china'); WORKERS = int(os.environ.get('WORKERS', 2))
SEG = os.environ.get('SEG', ROOT + '/_work/render2/seg'); os.makedirs(SEG, exist_ok=True); os.makedirs(ROOT + '/_work/render2/img', exist_ok=True)
J = json.load(open(sys.argv[1])); budget = float(sys.argv[2]); t0 = time.time()
x = lambda s: s.replace('{ROOT}', ROOT).replace('{HOME}', H).replace('{SEG}', SEG)
if J['images']: from PIL import Image, ImageOps
for src, dst in J['images']:
    src, dst = x(src), x(dst)
    if os.path.exists(dst): continue
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB'); im.thumbnail((3840, 3840)); im.save(dst, quality=92)
def ok(j): return os.path.exists(x(j['out']) + '.ok')
todo = [j for j in J['jobs'] if not ok(j)]
if len(sys.argv) > 3: todo = [j for j in todo if j['para'] in sys.argv[3].split(',')]
def go(j):
    if time.time() - t0 > budget: return None
    r = subprocess.run([x(c) for c in j['cmd']], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode == 0: open(x(j['out']) + '.ok', 'w').write('1'); return j['n'], 'ok'
    return j['n'], 'FAIL ' + r.stderr[-400:]
done = fail = 0
with cf.ThreadPoolExecutor(WORKERS) as ex:
    for res in ex.map(go, todo):
        if res is None: continue
        if res[1] == 'ok': done += 1
        else: fail += 1; print(res)
left = sum(1 for j in J['jobs'] if not ok(j))
print(f'done {done} fail {fail} left {left} of {len(J["jobs"])} in {time.time()-t0:.0f}s')
