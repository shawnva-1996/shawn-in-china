import json, os, sys, subprocess
H = os.environ['HOME']; SEG = H + '/seg'; K = H + '/mnt/shawn-in-china/_work/render'
J = json.load(open(K + '/jobs_1920.json')); T = J['total']; sw = J['switch']
out = sys.argv[1]
assert all(os.path.exists(f'{SEG}/{j["n"]:04d}.mov.ok') for j in J['jobs']), 'segments missing'
with open(SEG + '/list.txt', 'w') as f:
    for j in J['jobs']: f.write(f"file '{SEG}/{j['n']:04d}.mov'\n")
if not os.path.exists(SEG + '/pic.mov'):
    subprocess.run(['ffmpeg', '-y', '-nostdin', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', SEG + '/list.txt', '-c', 'copy', SEG + '/pic.mov'], check=True)
fc = (f"[2:a]aloop=loop=-1:size=2e9,atrim=0:{sw+2:.3f},afade=t=out:st={sw:.3f}:d=2[m1];"
      f"[3:a]aloop=loop=-1:size=2e9,atrim=0:{T-sw+1:.3f},afade=t=in:d=2,afade=t=out:st={T-sw-3:.3f}:d=3,adelay={int(sw*1000)}|{int(sw*1000)}[m2];"
      f"[m1][m2]amix=inputs=2:normalize=0,volume=0.5,aformat=channel_layouts=stereo[mus];"
      f"[1:a]aformat=channel_layouts=stereo,asplit=3[vo1][vo2][vo3];"
      f"[mus][vo1]sidechaincompress=threshold=0.02:ratio=8:attack=80:release=600[mduck];"
      f"[0:a][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=50:release=400[nat];"
      f"[vo3][nat][mduck]amix=inputs=3:normalize=0,alimiter=limit=0.89[a]")
subprocess.run(['ffmpeg', '-y', '-nostdin', '-v', 'error', '-i', SEG + '/pic.mov', '-i', K + '/vo_clean.m4a', '-i', K + '/upbeat.m4a', '-i', K + '/calm.m4a',
                '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', '-t', f'{T:.3f}', out], check=True)
print('wrote', out)
