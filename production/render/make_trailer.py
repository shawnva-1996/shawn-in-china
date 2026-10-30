"""Render the 9:16 trailer on the machine that holds the footage. Run from the trailer kit folder:
    ROOT=<shoot folder> WORKERS=3 python3 make_trailer.py
Needs: trailer.json, tovl/ (overlays + end.mp4), vo_clean.m4a, bed.m4a here, and the probed clip list in
../render2/meta.json (written by make_v2.py). Reuses runner.py and mix2.py from ../render2.
Writes final/shawn_in_china_ep1_trailer_9x16.mp4 and qa/ stills + preview, then deletes its segments."""
import json, os, subprocess, sys, time
K = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.setdefault('ROOT', os.path.abspath(K + '/../..'))
SEG = os.environ.setdefault('SEG', K + '/seg'); PY = sys.executable; R2 = os.path.abspath(K + '/../render2')
W, H, FPS = 1080, 1920, 30
T = json.load(open(K + '/trailer.json')); meta = json.load(open(R2 + '/meta.json'))
FINAL = ROOT + '/final/shawn_in_china_ep1_trailer_9x16.mp4'
MAXD, CUT = 1.25, 1.05          # Reels pacing: no shot longer than MAXD; long shots become ~CUT-second cuts
def fill(m, zoom=1.0):
    """cover-crop any source to 9:16 (landscape clips keep their centre); zoom > 1 punches in"""
    w, h = int(W * zoom) // 2 * 2, int(H * zoom) // 2 * 2
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
def quick(sh):
    """split a long shot into fast cuts from different moments of the same clip, alternating a punch-in.
    The first cut keeps the original in-point, so the shot still lands on the word it was cued to."""
    m = meta.get(sh['f'], {}); n = max(1, round(sh['d'] / CUT)) if sh['d'] > MAXD else 1
    if n == 1 or m.get('kind') != 'video': return [dict(sh, zoom=1.0)]
    sub = sh['d'] / n; need = sub * sh['speed']
    hi = m['dur'] - need - 0.15; lo = max(0.0, sh['st'] - 6.0)
    pts = [sh['st'] + k * 2.2 for k in range(n)]                       # walk forward through the clip
    if pts[-1] > hi: pts = [sh['st']] + [lo + (hi - lo) * k / max(1, n - 1) for k in range(1, n)]   # or spread over it
    return [dict(sh, st=round(max(0.0, min(p, hi)), 3), t=round(sh['t'] + k * sub, 3), d=round(sub, 3), zoom=1.0 if k % 2 == 0 else 1.18)
            for k, p in enumerate(pts)]
jobs = []; n = 0; imgs = set()
for k, s in enumerate(T['segs']):
    for sh in [q for x in s['shots'] for q in quick(x)]:
        d = sh['d']; sp = sh['speed']; out = f'{{SEG}}/{n:04d}.mov'
        if sh['f'].startswith('VIZ:'):          # 16:9 diagrams: centre them on a blurred copy of themselves
            m = dict(kind='viz'); ins = ['-ss', f"{sh['st']:.3f}", '-t', f'{d:.3f}', '-i', f"{R2}/viz_{sh['f'][4:]}.mp4"]
            ch = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30[bg];"
                  f"[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,setsar=1,fps={FPS}")
        else:
            m = meta[sh['f']]
            if m['kind'] == 'video':
                ins = ['-ss', f"{sh['st']:.3f}", '-t', f'{d * sp + 0.1:.3f}', '-i', f"{ROOT}/{sh['f']}"]
                ch = (f"setpts=(PTS-STARTPTS)/{sp}," if sp != 1 else '') + fill(m, sh['zoom'])
            else:
                imgs.add(sh['f']); ins = ['-loop', '1', '-t', f'{d:.3f}', '-i', f"{R2}/img/{sh['f'].replace('/', '_')}"]; ch = fill(m)
        ins += ['-ss', f"{sh['t'] - s['t']:.3f}", '-t', f'{d:.3f}', '-i', f"{K}/tovl/{k:02d}.mov"]
        fc = f"[0:v]{ch}[v0];[1:v]setpts=PTS-STARTPTS,format=rgba[o];[v0][o]overlay=eof_action=pass:format=auto,format=yuv420p[v]"
        if m.get('audio') and sp == 1:
            gain = 0.08 if sh['f'].startswith('from_wechat') else 0.15
            fc += f";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain},apad,afade=t=in:d=0.05,afade=t=out:st={max(0, d - 0.06):.3f}:d=0.06[a]"; amap = ['-map', '[a]']
        else:
            ins += ['-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']; amap = ['-map', '2:a']
        cmd = ['ffmpeg', '-y', '-nostdin', '-v', 'error'] + ins + ['-filter_complex', fc, '-map', '[v]'] + amap
        cmd += ['-t', f'{d:.3f}', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-threads', '2', '-pix_fmt', 'yuv420p',
                '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', out]
        jobs.append(dict(n=n, out=out, cmd=cmd, para=s['beat'], f=sh['f'], d=round(d, 2))); n += 1
a, d = T['end']
jobs.append(dict(n=n, out=f'{{SEG}}/{n:04d}.mov', para='END', f='end', d=d, cmd=['ffmpeg', '-y', '-nostdin', '-v', 'error', '-i', f'{K}/tovl/end.mp4',
    '-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a', '-t', f'{d:.3f}', '-r', str(FPS),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', f'{{SEG}}/{n:04d}.mov']))
missing = [f for f in imgs if not os.path.exists(f"{R2}/img/{f.replace('/', '_')}")]
json.dump(dict(jobs=jobs, images=[[f"{ROOT}/{f}", f"{R2}/img/{f.replace('/', '_')}"] for f in missing], total=T['total']), open(K + '/jobs_trailer.json', 'w'), indent=0)
t0 = time.time()
os.makedirs(ROOT + '/final', exist_ok=True)
if not os.path.exists(FINAL):
    subprocess.run([PY, R2 + '/runner.py', K + '/jobs_trailer.json', '1e9'], check=True)
    subprocess.run([PY, R2 + '/mix2.py', K + '/jobs_trailer.json', FINAL], check=True)
os.makedirs(K + '/qa', exist_ok=True)
for i in range(0, int(T['total']), 4):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(i + 1), '-i', FINAL, '-frames:v', '1', '-vf', 'scale=360:-2', f'{K}/qa/t{i:03d}.jpg'])
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', FINAL, '-vf', 'scale=360:-2', '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast',
                '-c:a', 'aac', '-b:a', '64k', K + '/qa/preview.mp4'], check=True)
for f in os.listdir(SEG): os.remove(os.path.join(SEG, f))
os.rmdir(SEG)
print(f'done in {time.time() - t0:.0f}s ->', FINAL, os.path.getsize(FINAL) // 2**20, 'MB')
