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

## Practical limits on Shawn's Mac

- Keep new working files under 3 GB (the Mac had 8 GB free). Originals are read in place, never copied or transcoded in bulk.
- The Mac VM: 4 cores, 3 GB RAM, ffmpeg 4.4. Split long jobs into calls under 3 minutes; 2 render workers.
- **Never delete `$HOME/tmp` on the Mac VM**: the remote shell keeps its socket there.

## Tools worth knowing

- **vidIQ connector** (connected): keyword research, title scoring, music generation, and once the channel is linked, updating titles, descriptions and thumbnails of uploaded videos.
- **Metricool / OpusClip connectors**: scheduling uploads and cutting Shorts from the long video.
- Open source used here: ffmpeg, Pillow, NumPy, Noto Color Emoji, Inter, Anton, Natural Earth land shapes (world-atlas).
