# Shawn in China: episode playbook

How to take an episode from raw footage + Shawn's voiceover to a YouTube-ready video. Episode 1 v2 (Chongqing,
Oct 2026) is the reference; its pipeline is in [`render/`](./render/README.md). Copy this for each new city.

## Editing rules (from Shawn's feedback)

1. **Every clip appears once.** A shoot has hundreds of clips, so repeats read as lazy. `plan2.py` lists clip usage; the only allowed repeat is a single continuous shot split by a cutaway (marked `@CONT`).
2. **A shot lands on the word that names it.** Each shot in the edit list carries a cue word (`~controller`). The cut happens 0.12 s before Shawn says that word, so the PlayStation controller is on screen when he says "PlayStation controller".
3. **Video over photos.** Use stills only when no video of the moment exists (ep. 1 used 2 photos in 176 shots). Stills get a slow push-in; vertical clips get a blurred fill.
4. **Credit friends' footage.** Anything from `from_wechat/` was filmed by someone else. It gets a small "📱 filmed by a friend" tag, and the narration must not claim Shawn did it. Thank them in the description.
5. **The recorded VO is the script.** Shawn ad-libs. Once the VO is recorded, match the picture to what he actually said and don't ask for a re-record unless a fact is wrong.
6. **Visuals explain, they don't decorate.** Stickers and pills mark a list ("Google ❌ / Amap ✓"), a number gets a count-up, a concept gets a diagram (the East Data West Computing map). About one graphic every 5–8 s, each with a small sound effect.
7. **Facts we can't confirm stay out of the picture.** No programme fees (they change every intake). Visa and payment rules always point to the official links in the description.

## Reels, Shorts and TikToks (lessons from ep. 1, 30 Oct 2026)

Shawn rejected the first two reel cuts. These rules come from that feedback; follow them before showing anything.

**Approval gates, in this order.** (1) The script as a markdown file, (2) the music, (3) the render. Never render before the script and the music are approved. Send the finished MP4 as an attachment so Shawn can watch it on his phone, plus a cover image and the post captions.

**What a reel is for.**
1. **A reel builds hype or gives one self-contained story; it is not a shrunk YouTube video.** The first trailer was rejected for "revealing too much". A hype reel asks the questions and cuts away before the answers; a day reel tells one day and ends with "full video on YouTube".
2. **Every line is a complete sentence.** Use whole recorded takes only. Never start or end a line in the middle of a take.
3. **Every picture in a script is a real clip, named by file.** The first script invented shots (passport, plane window, a door) that were never filmed. Check `shot_log.csv` before writing a picture cell.

**Picture.**
4. **9:16 means portrait clips first.** Check the `orientation` column in `shot_log.csv` (`meta.json` width/height ignore the iPhone rotation flag, so a portrait clip can look landscape there). Use a landscape clip only when the moment has no portrait version, then centre-crop it. Ep. 1: only 50 of 270 clips are portrait, mostly food, Hongyadong, Jiefangbei and the last day.
5. **Fast cuts**: about 0.6–1.2 s per cut, on the music's beat, alternating punch-ins. A single long shot only for a deliberate slow beat.
6a. **Check every on-screen symbol renders.** Anton has no ✓, ⏰ or Chinese characters, so they came out as empty boxes in the first day-reel render. Text with emoji, clock symbols or Chinese goes through `rich()` (Noto Color Emoji + WenQuanYi); use ✅ rather than ✓. Render a sheet of every non-ASCII title before the render.
6. Burned-in captions of 1–3 words, a thin letterbox for the trailer look, the "📱 filmed by a friend" tag on WeChat clips, and an end card that sends people to the full video.

**Voice (the mistake that got the reel rejected).**
7. **Cut VO lines from the raw recording at real pauses, never from word timestamps.** The Gemini word times in `timeline2.json` are only good to about ±0.1 s, and inside a take they can be off by whole words. Lines lifted from the middle of a take came out as "people call it the 8D" and "really everywhere in China". `render/reel_vo.py` finds the room-tone gap before the first word and after the last one in `vo_raw.wav` and cuts there.
8. **Check every line by transcription before rendering**: cut each line as its own clip and ask Gemini for the verbatim words plus whether the first or last word is clipped (see the check in `render/reel_vo.py`'s notes). Then transcribe the final mix too. Anything short of the full expected sentence goes back.
9. Fade only inside the pause (20 ms in, 50 ms out). **Keep 0.15 s of room tone before the first sound and 0.2 s after the last** (as far as the pause allows; `pad_cut` in `reels_build.py`). The first day-reel render cut most lines only 0.02 s before the first sound, so the fade-in could soften a soft first consonant; it was re-cut and re-rendered before anyone saw it.
9a. **The check catches real clipping, so act on it.** In the day-reel build, 18 of 108 whole takes still lost their last word with the automatic cut (soft endings such as "shops", "country", "the hall"). `render/reels_build.py` re-cuts a failed take with a longer tail (+0.15 s, +0.3 s, then the end of each following pause) and re-checks it. **A cut that failed once is never accepted on a retry**, because Gemini can pass the same clipped audio a second time; it must be re-cut.
9b. **The timeline text can be wrong too.** Sometimes the recording has words the transcript dropped ("…the best meal we had *in Chongqing*", "walked around *the hall*") or a misheard word ("shop" for "chef"). Then the take never passes against the old text. Transcribe the take freely (no expected text), and if the audio is complete, fix the text and caption words in `TEXT` in `reels_build.py`.
9c. After the kits are built, transcribe each reel's whole VO track (`vo.wav`) against the script and look at every difference.

**Music and sound.**
10. Trailer feel = braam hits, a ticking pulse, a riser into a drop, one beat of dead silence, a drum montage and a final title hit. `render/trailer_score.py` synthesises one timed to the script (no copyright claims). Day reels can reuse the full video's music bed.
11. Keep the music big but dip it about 4 dB under the voice; mix to -14 LUFS.
11a. Music style for China content: Chinese-style (guofeng) trap, like the Chongqing night motorbike-ride videos. Generic Western travel pop was rejected (30 Oct). Day reels use `render/guofeng_score.py` (synthesised guzheng, bamboo flute, opera gongs, 808, motorbike rev into drops), chosen over a produced AI take (`render/guofeng_ai.py`). The series trailer keeps the hype score. Audition a style on built kits with `MUSIC=<style> render/reels_bed.py <kit>` and send music-only and with-voice previews before rendering.

**Publishing.**
12. Cover: 1080×1920 with all text inside the 3:4 profile-grid crop (y ≈ 240–1680).
13. Captions per platform with a clear call to action: Instagram and TikTok say "link in bio" (put the YouTube link in the bio first); Facebook can carry the link itself. Turn off auto-captions, since captions are burned in.
14. Version every render (`final/..._v2_...`) and never overwrite one Shawn has already seen.

**Getting files to and from the Mac.**
- Render on the Mac with Remote Control (native Homebrew ffmpeg; a 44 s reel renders in about a minute). Build overlays and audio in the cloud and copy the kit across with `device_commit_files` (≤30 MB per file, ≤100 MB and ≤50 files per call) when the device bridge is up. Overlays as PNG `.mov` are huge (551 MB for 7 reels); re-encode them as VP9 with alpha (`.webm`, 45 MB for all 7, `make_reel.py` decodes them with `-c:v libvpx-vp9`) and send one `.tar` per reel. Avoid temporary public branches: the git proxy can't delete them afterwards.
- Overlays can't be built on the Mac: they need the Inter and Noto emoji fonts of the cloud container.
- Dry-run `make_reel.py` in the cloud first with stand-in footage (tiny `testsrc2` clips at every path the kit uses) to catch pipeline bugs before using the Mac.
- Pull QA stills and the final MP4 back with `device_stage_files` to check frames and attach the video.

## Pipeline

| Step | Script | What it does |
|---|---|---|
| 1. Probe | `render/probe.py` (on the Mac) | Duration, fps, rotation, audio for every clip. Never guess rotation: phones store it as metadata. |
| 2. Transcribe the VO | `vo2_tx.py` | Splits the raw VO on pauses and transcribes each phrase with word times (Gemini, key pool from the shoot folder, never committed). Phrases under 0.6 s hallucinate, so drop them. |
| 3. Pick takes | edit list `edl2.py` | Each beat lists the VO phrases to keep. Retakes, false starts and off-mic remarks are simply not listed. |
| 4. Plan | `plan2.py` | Lays the kept phrases on a timeline (0.15–0.45 s gaps inside a beat, 0.4 s between beats), snaps word times to the real speech onsets, times every cut to its cue word and writes `timeline2.json`, captions and chapter times. |
| 5. Graphics | `gfx/overlays.py` (+ `motion.py`, `sticker.py`, `mapviz.py`) | One transparent overlay clip per beat: chapter cards, location tags, emoji stickers with a die-cut border, pills, count-ups, the 8D card, the spice meter, the title and end card, and full-screen maps. |
| 6. Audio | `vo_build.py`, `bed_build.py`, `sfx/make_sfx.py` | Clean VO at -16 LUFS; music bed that ducks 15 dB under speech and switches to a calm track for the outro; sound effects on every graphic cue and a whoosh on each chapter. |
| 7. Render | `jobs2.py` → `runner.py` → `mix2.py` (on the Mac) | One ffmpeg job per shot against the original footage (nothing is uploaded), then concat and final mix at -14 LUFS. |
| 8. QA | frame sheets + a low-res preview | Check every chapter card, each sticker against the shot under it, and the cue sync on named objects. |
| 9. Publish | `youtube_upload_ep*.md` | Title, description, chapters, links, tags, captions, pinned comment. |
| 10. Reels | `reel_plan.py` → `reel_vo.py` → `gfx/reel_ovl.py` → `reel_audio.py` → `make_reel.py` (on the Mac) | 9:16 cuts on a music grid, VO lines cut at real pauses, trailer overlays and end card. See the Reels section above. |
| 11. Series of reels | `reels_spec.py` (scripts as data) → `reels_build.py` (cut + check takes, plan, `reels_score.py` music, `gfx/reels_ovl.py` overlays and cover) → `make_reel.py` (on the Mac) | The series trailer and one reel per day. Cover frame first (also saved as `final/<reel>_cover.jpg`). Verified takes are cached in `takes.json` in the work folder. |

## Practical limits on Shawn's Mac

- Keep new working files under 3 GB (the Mac had 8 GB free). Originals are read in place, never copied or transcoded in bulk.
- The Mac VM: 4 cores, 3 GB RAM, ffmpeg 4.4. Split long jobs into calls under 3 minutes; 2 render workers.
- **Never delete `$HOME/tmp` on the Mac VM**: the remote shell keeps its socket there.

## Tools worth knowing

- **vidIQ connector** (connected): keyword research, title scoring, music generation, and once the channel is linked, updating titles, descriptions and thumbnails of uploaded videos.
- **Metricool / OpusClip connectors**: scheduling uploads and cutting Shorts from the long video.
- Open source used here: ffmpeg, Pillow, NumPy, Noto Color Emoji, Inter, Anton, Natural Earth land shapes (world-atlas).
