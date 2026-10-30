"""Rebuild only the music bed of built reel kits (score.wav + ducked bed.m4a), keeping the voice and overlays.
usage: reels_bed.py <kit dir> [...]   music style from reels_spec.py ('hype' or 'travel')"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reels_spec import REELS
import reels_build
for kit in sys.argv[1:]:
    R = json.load(open(f'{kit}/reel.json')); R['music'] = REELS[R['name']].get('music', 'hype')
    json.dump(R, open(f'{kit}/reel.json', 'w'), indent=1, ensure_ascii=False)
    reels_build.build_audio(R, None, kit, vo=False)
    print(R['name'], R['music'], 'bed rebuilt', file=sys.stderr)
