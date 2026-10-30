import json, subprocess, sys, os
base = sys.argv[1]; out = {}
for f in open(sys.argv[2]).read().split('\n'):
    if not f: continue
    p = os.path.join(base, f)
    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
        from PIL import Image, ImageOps
        try:
            im = ImageOps.exif_transpose(Image.open(p)); out[f] = dict(kind='image', w=im.width, h=im.height)
        except Exception as e: out[f] = dict(kind='image', err=str(e))
        continue
    j = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True).stdout or '{}')
    v = [s for s in j.get('streams', []) if s.get('codec_type') == 'video']
    a = [s for s in j.get('streams', []) if s.get('codec_type') == 'audio']
    if not v: out[f] = dict(kind='bad'); continue
    v = v[0]; rot = 0
    for sd in v.get('side_data_list', []):
        if 'rotation' in sd: rot = int(sd['rotation'])
    rot = int(v.get('tags', {}).get('rotate', rot))
    out[f] = dict(kind='video', w=v['width'], h=v['height'], rot=rot, dur=float(j['format']['duration']), audio=bool(a), fps=v.get('r_frame_rate'))
json.dump(out, open(sys.argv[3], 'w'), indent=0)
print(len(out), sum(1 for x in out.values() if x['kind'] == 'bad'))
