"""Turn timeline2.json into per-shot ffmpeg jobs for the Mac runner (runner.py), plus the mix job.
Each segment = source clip (trimmed, speed-ramped, framed to 16:9) + that beat's overlay clip (ovl/<beat>.mov,
seeked to the same moment) + the clip's own sound at a low level (full level on 'nat' beats, muted on WeChat
clips' talk-over and on slowed shots).
usage: jobs2.py <workdir> [--preview]      writes <workdir>/jobs2.json
paths in the jobs use {ROOT} (the shoot folder) and {SEG}; the kit (ovl/, viz_map.mp4, vo_clean.m4a, bed.m4a) lives on the Mac in KIT.
"""
import json, os, sys
WD = sys.argv[1]; PREVIEW = '--preview' in sys.argv
W, H, FPS = (960, 540, 30) if PREVIEW else (1920, 1080, 30)
T = json.load(open(f'{WD}/timeline2.json')); meta = json.load(open(f'{WD}/meta.json'))
DEV = '{ROOT}'; KIT = DEV + '/_work/render2'; IMG = KIT + '/img'
spans = {b['id']: b['span'] for b in T['beats']}
have_ovl = {f[:-4] for f in os.listdir(f'{WD}/ovl') if f.endswith('.mov')}

def frame(m, d):
    """filter chain that fits one source to W x H: verticals get a blurred fill, stills get a slow push-in"""
    if m['kind'] == 'image':
        if m['h'] > m['w'] * 1.1:
            return (f"scale=-2:{H},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bg];"
                    f"[bg][b]overlay=(W-w)/2:0,fps={FPS}")
        return (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
                f"zoompan=z='min(zoom+{0.08/(d*FPS):.5f},1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(d*FPS)+2}:s={W}x{H}:fps={FPS}")
    rot = m.get('rot', 0); w, h = (m['h'], m['w']) if abs(rot) in (90, 270) else (m['w'], m['h'])
    if h > w * 1.1:
        return (f"scale=-2:{H},split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bg];"
                f"[bg][b]overlay=(W-w)/2:0,fps={FPS}")
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"

jobs = []; imgs = set()
for n, s in enumerate(T['shots']):
    d = s['d']; sp = s['speed']; out = f'{{SEG}}/{n:04d}.mov'
    if s['f'].startswith('VIZ:'):
        m = dict(kind='viz'); ins = ['-t', f'{d:.3f}', '-i', f"{KIT}/viz_{s['f'][4:]}.mp4"]; ch = f"scale={W}:{H},fps={FPS}"
    else:
        m = meta[s['f']]
        if m['kind'] == 'video':
            ins = ['-ss', f"{s['st']:.3f}", '-t', f'{d * sp + 0.1:.3f}', '-i', f"{DEV}/{s['f']}"]
            ch = (f"setpts=(PTS-STARTPTS)/{sp}," if sp != 1 else '') + frame(m, d)
        else:
            imgs.add(s['f']); ins = ['-loop', '1', '-t', f'{d:.3f}', '-i', f"{IMG}/{s['f'].replace('/', '_')}"]; ch = frame(m, d)
    fc = f"[0:v]{ch}[v0]"; k = 1
    if s['beat'] in have_ovl:
        off = s['t'] - spans[s['beat']][0]
        ins += ['-ss', f'{off:.3f}', '-t', f'{d:.3f}', '-i', f"{KIT}/ovl/{s['beat']}.mov"]
        fc += f";[1:v]setpts=PTS-STARTPTS,format=rgba[o];[v0][o]overlay=eof_action=pass:format=auto[v1]"; k = 2
    else:
        fc += ";[v0]null[v1]"
    fc += ";[v1]format=yuv420p[v]"
    if m.get('audio') and sp == 1:
        gain = 1.0 if s['nat'] else (0.10 if s['f'].startswith('from_wechat') else 0.22)
        fc += f";[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain},apad,afade=t=in:d=0.06,afade=t=out:st={max(0, d - 0.08):.3f}:d=0.08[a]"
        amap = ['-map', '[a]']
    else:
        ins += ['-f', 'lavfi', '-t', f'{d:.3f}', '-i', 'anullsrc=r=48000:cl=stereo']; amap = ['-map', f'{k}:a']
    cmd = ['ffmpeg', '-y', '-nostdin', '-v', 'error'] + ins + ['-filter_complex', fc, '-map', '[v]'] + amap
    cmd += ['-t', f'{d:.3f}', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'veryfast' if PREVIEW else 'medium', '-crf', '26' if PREVIEW else '19',
            '-threads', '2', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', out]
    jobs.append(dict(n=n, out=out, cmd=cmd, para=s['beat'], f=s['f'], d=round(d, 2)))
json.dump(dict(jobs=jobs, images=[[f"{DEV}/{f}", f"{IMG}/{f.replace('/', '_')}"] for f in sorted(imgs)], total=T['total']),
          open(f'{WD}/jobs2.json', 'w'), indent=0)
print(len(jobs), 'jobs,', len(imgs), 'images, total', round(T['total'], 1), 's', file=sys.stderr)
