"""Render a 9:16 reel on the machine that holds the footage. Run from the reel kit folder:
    ROOT=<shoot folder> WORKERS=3 python3 make_reel.py
Needs here: reel.json, rovl/ (overlays, cover.png, end.mp4), vo_clean.m4a, bed.m4a; and $R2 (default
ROOT/_work/render2) with meta.json, runner.py, mix2.py and viz_map.mp4.
If reel.json has a cover, the first T0 seconds are the cover (a still of the cover clip + rovl/cover.png), so the
reel's first frame is its thumbnail; it is also saved as final/<reel>_cover.jpg.
Every cut is explicit in reel.json (no automatic splitting): z = punch-in, push = slow zoom to that scale over the
shot, sp < 1 = slow motion from the 60 fps originals, hold = freeze the last frame for that long, BLACK = black frame.
Writes final/<reel.json out> (or final/$OUT) and qa/ stills + preview, then deletes its segments."""
import json, os, subprocess, sys, time
K = os.path.dirname(os.path.abspath(__file__)); ROOT = os.environ.setdefault('ROOT', os.path.abspath(K + '/../../..'))
SEG = os.environ.setdefault('SEG', K + '/seg'); PY = sys.executable; R2 = os.environ.get('R2', ROOT + '/_work/render2')
W, H, FPS = 1080, 1920, 30
R = json.load(open(K + '/reel.json')); meta = json.load(open(R2 + '/meta.json'))
FINAL = ROOT + '/final/' + os.environ.get('OUT', R.get('out', 'shawn_in_china_ep1_reel_9x16.mp4'))
ENC = ['-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-threads', '2', '-pix_fmt', 'yuv420p',
       '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2']
def frame(sh):
    """cover-crop to 9:16 with a fixed punch-in, or a slow push-in from z to push over the shot"""
    z0 = sh['z']; z1 = sh['push'] or z0; d = sh['d']
    if z1 == z0:
        w, h = int(W * z0) // 2 * 2, int(H * z0) // 2 * 2
        return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={W}:{H}"
    # push-in: cover-crop at 2x, then zoompan back down to 1080x1920 (one output frame per input frame)
    nf = max(1, round(d * FPS))
    return (f"scale={2 * W}:{2 * H}:force_original_aspect_ratio=increase,crop={2 * W}:{2 * H},"
            f"zoompan=z='{z0}+({z1}-{z0})*min(on/{nf},1)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS}")
jobs = []
SILENT = ['-f', 'lavfi', '-t', '{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']
if R.get('cover'):          # the cover: one clean frame of the cover clip held for T0, with the cover text on top
    c = R['cover']; d = c['d']; out = f'{{SEG}}/{len(jobs):04d}.mov'
    ins = ['-ss', f"{c['st']:.3f}", '-t', '1', '-i', f"{ROOT}/{c['f']}", '-loop', '1', '-t', f'{d:.3f}', '-i', f'{K}/rovl/cover.png'] + [x.format(d=d) for x in SILENT]
    fc = (f"[0:v]trim=end_frame=1,setpts=PTS-STARTPTS,fps={FPS}," + frame(dict(z=c['z'], push=None, d=d)) + f",setsar=1,tpad=stop_mode=clone:stop_duration={d + 0.5:.3f}[v0];"
          "[1:v]format=rgba[o];[v0][o]overlay=format=auto,format=yuv420p[v]")
    jobs.append(dict(n=len(jobs), out=out, para='COVER', f=c['f'], d=d, cmd=['ffmpeg', '-y', '-nostdin', '-v', 'error'] + ins +
                     ['-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-t', f'{d:.3f}'] + ENC + [out]))
for sh in R['shots']:
    n = len(jobs)
    s = R['segs'][sh['seg']]; d = sh['d']; out = f'{{SEG}}/{n:04d}.mov'
    o = f"{K}/rovl/{sh['seg']:02d}"      # overlays ship as VP9 with alpha (.webm, needs the libvpx decoder) or PNG .mov
    ovl = ['-ss', f"{sh['t'] - s['t']:.3f}", '-t', f'{d:.3f}'] + (['-c:v', 'libvpx-vp9', '-i', o + '.webm'] if os.path.exists(o + '.webm') else ['-i', o + '.mov'])
    if sh['f'].startswith('VIZ:'):          # 16:9 diagrams: centred on a blurred copy of themselves
        ins = ['-ss', f"{sh['st']:.3f}", '-t', f"{d - sh['hold']:.3f}", '-i', f"{R2}/viz_{sh['f'][4:]}.mp4"] + ovl
        ch = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30[bg];"
              f"[b]scale={W}:-2[fg];[bg][fg]overlay=0:(H-h)/2,setsar=1,fps={FPS}")
        if sh['hold']: ch += f",tpad=stop_mode=clone:stop_duration={sh['hold']:.3f}"
        audio = False
    elif sh['f'] == 'BLACK':
        ins = ['-f', 'lavfi', '-t', f'{d:.3f}', '-i', f'color=c=black:s={W}x{H}:r={FPS}'] + ovl
        ch = 'setsar=1'; audio = False
    else:
        m = meta[sh['f']]; sp = sh['sp']; play = d - sh['hold']
        ins = ['-ss', f"{sh['st']:.3f}", '-t', f'{play * sp + 0.1:.3f}', '-i', f"{ROOT}/{sh['f']}"] + ovl
        ch = (f"setpts=(PTS-STARTPTS)/{sp}," if sp != 1 else 'setpts=PTS-STARTPTS,') + f"fps={FPS}," + frame(sh) + ',setsar=1'
        # hold the last frame for a freeze, and always pad a little so a short read never shortens the segment
        ch += f",tpad=stop_mode=clone:stop_duration={sh['hold'] + 0.3:.3f}"
        audio = m.get('audio') and sp == 1
    fc = f"[0:v]{ch}[v0];[1:v]setpts=PTS-STARTPTS,format=rgba[o];[v0][o]overlay=eof_action=pass:format=auto,format=yuv420p[v]"
    if audio:      # a little natural sound under the score (friend clips are louder, so lower)
        gain = 0.05 if sh['f'].startswith('from_wechat') else 0.1
        fc += f";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain},apad,afade=t=in:d=0.04,afade=t=out:st={max(0, d - 0.05):.3f}:d=0.05[a]"
        amap = ['-map', '[a]']
    else:
        ins += [x.format(d=d) for x in SILENT]; amap = ['-map', '2:a']
    cmd = ['ffmpeg', '-y', '-nostdin', '-v', 'error'] + ins + ['-filter_complex', fc, '-map', '[v]'] + amap + ['-t', f'{d:.3f}'] + ENC + [out]
    jobs.append(dict(n=n, out=out, cmd=cmd, para=s['name'], f=sh['f'], d=d))
n = len(jobs); a, d = R['end']
jobs.append(dict(n=n, out=f'{{SEG}}/{n:04d}.mov', para='END', f='end', d=d, cmd=['ffmpeg', '-y', '-nostdin', '-v', 'error', '-i', f'{K}/rovl/end.mp4',
    '-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo', '-map', '0:v', '-map', '1:a', '-t', f'{d:.3f}'] + ENC + [f'{{SEG}}/{n:04d}.mov']))
json.dump(dict(jobs=jobs, images=[], total=R['total']), open(K + '/jobs_reel.json', 'w'), indent=0)
t0 = time.time()
os.makedirs(ROOT + '/final', exist_ok=True)
if not os.path.exists(FINAL):
    subprocess.run([PY, R2 + '/runner.py', K + '/jobs_reel.json', '1e9'], check=True)
    subprocess.run([PY, R2 + '/mix2.py', K + '/jobs_reel.json', FINAL], check=True)
os.makedirs(K + '/qa', exist_ok=True)
if R.get('cover'):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', FINAL, '-frames:v', '1', '-q:v', '2', FINAL[:-4] + '_cover.jpg'], check=True)
for i in range(0, int(R['total']), 2):
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', str(i + 0.5), '-i', FINAL, '-frames:v', '1', '-vf', 'scale=360:-2', f'{K}/qa/r{i:03d}.jpg'])
subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', FINAL, '-vf', 'scale=360:-2', '-c:v', 'libx264', '-crf', '30', '-preset', 'veryfast',
                '-c:a', 'aac', '-b:a', '96k', K + '/qa/preview.mp4'], check=True)
for f in os.listdir(SEG): os.remove(os.path.join(SEG, f))
os.rmdir(SEG)
print(f'done in {time.time() - t0:.0f}s ->', FINAL, os.path.getsize(FINAL) // 2**20, 'MB')
