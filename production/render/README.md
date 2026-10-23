# Episode 1 render pipeline

How `final/shawn_in_china_ep1_chongqing.mp4` (1080p30, 9:05) was made on 23 Oct 2026.

1. **VO clean-up** (`vo_process.py`, `verify.py`): Shawn's 11 VO files were joined, split on pauses into 183 phrases, and transcribed with Gemini. A second Gemini pass picked the clean take of each script line. Doubtful phrases were re-checked with the script as context, and four phrases were trimmed at micro-pauses ("30 million" slip, "So the build…" false start, a repeated "Liziba", and an unfinished "and it was…"). The keep/drop list is in `vo_decisions.json`. 22 phrases were dropped and 161 kept. The voice is then denoised, compressed and normalised to -16 LUFS.
2. **Edit plan** (`edl.py`, `plan_build.py`): every script paragraph maps to its shots. Footage with no explicit in-point is filled from the same itinerary slot in `shot_log.csv`, and shot lengths are fitted to the VO timing. The planner writes one ffmpeg job per shot, plus graphics (chapter cards, lower thirds, the data-centre map and the end card).
3. **Render** (`runner.py`, `mix.py`): runs on the Mac VM against the original footage, so nothing is uploaded. It renders 151 segments, concatenates them, and mixes in the VO, ducked location sound and two original music beds generated with vidIQ. The mix comes out at about -15 LUFS.

API keys are read from `new_gemini_pool.json` in the shoot folder and are never committed.
