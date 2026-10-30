"""Join the rendered segments and mix the final audio on the Mac.
nat sound (from the segments) ducks under the VO; the bed (music already ducked + sound effects) sits under both.
usage: mix2.py <jobs2.json> <out.mp4>     kit files (vo_clean.m4a, bed.m4a) are read from the jobs file's folder
"""
import json, os, sys, subprocess
H = os.environ['HOME']; ROOT = os.environ.get('ROOT', H + '/mnt/shawn-in-china'); SEG = os.environ.get('SEG', ROOT + '/_work/render2/seg')
J = json.load(open(sys.argv[1])); K = os.path.dirname(os.path.abspath(sys.argv[1])); T = J['total']; out = sys.argv[2]
assert all(os.path.exists(f'{SEG}/{j["n"]:04d}.mov.ok') for j in J['jobs']), 'segments missing'
with open(SEG + '/list.txt', 'w') as f:
    for j in J['jobs']: f.write(f"file '{SEG}/{j['n']:04d}.mov'\n")
fc = ("[1:a]aformat=channel_layouts=stereo,asplit=2[vo1][vo2];"
      "[0:a][vo2]sidechaincompress=threshold=0.03:ratio=4:attack=50:release=400[nat];"
      "[vo1][nat][2:a]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=9,aresample=48000[a]")
subprocess.run(['ffmpeg', '-y', '-nostdin', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', SEG + '/list.txt', '-i', K + '/vo_clean.m4a', '-i', K + '/bed.m4a',
                '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
                '-movflags', '+faststart', '-t', f'{T:.3f}', out], check=True)
print('wrote', out)
