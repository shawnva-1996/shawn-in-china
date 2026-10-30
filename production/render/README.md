# Episode 1 render pipeline

How `final/shawn_in_china_ep1_chongqing.mp4` (1080p30, 9:05) was made on 23 Oct 2026.

1. **VO clean-up** (`vo_process.py`, `verify.py`): Shawn's 11 VO files were joined, split on pauses into 183 phrases, and transcribed with Gemini. A second Gemini pass picked the clean take of each script line. Doubtful phrases were re-checked with the script as context, and four phrases were trimmed at micro-pauses ("30 million" slip, "So the build…" false start, a repeated "Liziba", and an unfinished "and it was…"). The keep/drop list is in `vo_decisions.json`. 22 phrases were dropped and 161 kept. The voice is then denoised, compressed and normalised to -16 LUFS.
2. **Edit plan** (`edl.py`, `plan_build.py`): every script paragraph maps to its shots. Footage with no explicit in-point is filled from the same itinerary slot in `shot_log.csv`, and shot lengths are fitted to the VO timing. The planner writes one ffmpeg job per shot, plus graphics (chapter cards, lower thirds, the data-centre map and the end card).
3. **Render** (`runner.py`, `mix.py`): runs on the Mac VM against the original footage, so nothing is uploaded. It renders 151 segments, concatenates them, and mixes in the VO, ducked location sound and two original music beds generated with vidIQ. The mix comes out at about -15 LUFS.

API keys are read from `new_gemini_pool.json` in the shoot folder and are never committed.

# Episode 1 v2 (30 Oct 2026)

`final/shawn_in_china_ep1_chongqing_v2.mp4`: 1080p30, 8:42 (521.9 s), 664 MB, -14.1 LUFS. Built from Shawn's single new VO take (`vo.m4a`).
See [../PLAYBOOK.md](../PLAYBOOK.md) for the rules and step list. In short:

1. `vo2_tx.py` (scratch) split the VO into 158 phrases and transcribed them with word times; 13 phrases were dropped (retakes, false starts, off-mic remarks).
2. `edl2.py` is the edit: 70 beats, each with its kept VO phrases, shots cued to words (`"Folder/File.MOV ~word"`), and graphics/SFX cues. 174 different clips, none repeated except one continuous shot.
3. `plan2.py` → `timeline2.json`, `captions_en.srt`, `chapters.txt`.
4. `gfx/overlays.py` renders one transparent overlay per beat plus the East-Data-West-Computing map (`gfx/mapviz.py`, timed to the VO words).
5. `vo_build.py` (clean VO, -16 LUFS) and `bed_build.py` (music ducked under speech + 106 SFX).
6. On the Mac: `make_v2.py` probes the clips, re-plans (and refuses to continue if the timeline drifts from the overlays), writes per-shot jobs (`jobs2.py`), renders them (`runner.py`, 3 workers, 16 min for 176 shots natively on the M-series Mac), and mixes (`mix2.py`). The run used Remote Control on the Mac with Homebrew ffmpeg 9 because the Mac VM shell was unavailable.
