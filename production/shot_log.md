# Shot Log: Footage Mapped to the Itinerary

- **Built from:** the capture time and GPS stored in each iPhone file (QuickTime tags for video, EXIF for photos), read in place from the local footage folder on 2026-10-21. No footage was copied.
- **Method:** each clip is placed in the Program A itinerary slot that was running at its local capture time (UTC+8). Slot boundaries start about 15 minutes before the printed time to allow for travel.
- **Caveat:** schedules slipped on the day, so a clip near a boundary can land in the neighbouring slot. Gemini then described every clip (see below), and its view overrides the time-based slot where they disagree. The per-clip list, including the Gemini columns (`ai_*`), is in [shot_log.csv](./shot_log.csv).

## Coverage by itinerary slot

| Day | Itinerary slot (Program A) | Clips | Video secs | Vertical | Photos | Time span |
|---|---|---|---|---|---|---|
| 12 Oct | Arrival day, own time | 0 | 0 | 0 | 4 | 13:02–13:33 |
| 12 Oct | Somerset lobby, welcome dinner | 9 | 115 | 0 | 6 | 17:54–21:53 |
| 13 Oct | Chongqing Planning Exhibition Gallery | 16 | 98 | 0 | 6 | 09:19–10:26 |
| 13 Oct | China-Singapore Demonstration Initiative Admin Bureau | 9 | 38 | 1 | 1 | 11:02–12:27 |
| 13 Oct | Lunch | 1 | 4 | 1 | 0 | 12:30–12:30 |
| 13 Oct | Liangjiang Free Trade Industrial Digitalisation Exchange | 10 | 47 | 2 | 0 | 14:15–16:26 |
| 13 Oct | Raffles Hospital | 2 | 12 | 0 | 14 | 16:37–17:33 |
| 13 Oct | Dinner | 4 | 16 | 2 | 11 | 18:52–19:50 |
| 13 Oct | Free time: Guanyinqiao Pedestrian Street | 5 | 18 | 0 | 0 | 20:15–20:58 |
| 14 Oct | Liangjiang Life Science City Exhibition Hall | 2 | 25 | 0 | 34 | 09:54–10:19 |
| 14 Oct | Chongqing Haifu Medical (HIFU) | 1 | 6 | 0 | 6 | 10:20–11:11 |
| 14 Oct | Lunch | 17 | 50 | 3 | 0 | 12:04–12:48 |
| 14 Oct | CVTE Exhibition Hall | 7 | 421 | 0 | 0 | 14:52–15:05 |
| 14 Oct | Guangyu Mingdao Digital Technology | 2 | 8 | 0 | 1 | 15:53–16:00 |
| 14 Oct | Qiteng Robotics | 6 | 84 | 0 | 0 | 17:32–17:55 |
| 14 Oct | Dinner | 11 | 200 | 2 | 2 | 18:22–19:14 |
| 14 Oct | Free time: Hongyadong | 1 | 145 | 0 | 0 | 21:59–21:59 |
| 15 Oct | Eling No. 2 Factory | 18 | 170 | 4 | 0 | 09:17–10:11 |
| 15 Oct | Xianlichang Digital Technology | 6 | 34 | 1 | 0 | 10:58–12:28 |
| 15 Oct | China-Singapore Connectivity Exhibition Hall | 5 | 31 | 1 | 0 | 14:29–14:41 |
| 15 Oct | BEYOND 2026 Trade Exchange Conference | 1 | 6 | 0 | 0 | 15:42–15:42 |
| 15 Oct | Free time: Chaotianmen | 16 | 86 | 4 | 1 | 20:02–21:31 |
| 16 Oct | Premium Domestic Products Trade Centre | 13 | 56 | 0 | 31 | 09:33–10:09 |
| 16 Oct | Free Trade Zone Development & Management Group | 2 | 35 | 1 | 4 | 10:56–11:58 |
| 16 Oct | Lunch | 10 | 39 | 3 | 0 | 13:00–13:52 |
| 16 Oct | Shiguangge Digital Productivity Institute | 11 | 33 | 5 | 0 | 16:50–17:56 |
| 16 Oct | Dinner | 1 | 14 | 1 | 0 | 18:13–18:13 |
| 16 Oct | Free time: Jiefangbei Food Street | 9 | 251 | 4 | 0 | 21:53–23:00 |
| 17 Oct | After the programme: own exploring before departure | 42 | 401 | 15 | 0 | 13:29–18:19 |

from_wechat (no timestamps or GPS): 33 clips, 44.4 min, 266 images.

## What this means for the edit

- **Strongest story beats by footage:** the CVTE Exhibition Hall (7 min), the 17 Oct afternoon of exploring (6.7 min), Jiefangbei Food Street at night (4.2 min), the Day 3 dinner (3.3 min), Eling No. 2 Factory (2.8 min) and one long Hongyadong clip (2.4 min).
- **Thin or missing coverage:** the Western China Advanced Data Centre has no clips (filming was probably not allowed), and the BEYOND conference has a single 6-second clip. The script should cover these with narration over photos, WeChat clips or a map card.
- **Photo-heavy stops** such as Liangjiang Life Science City (34 photos) and the Premium Domestic Products Trade Centre (31) suit Ken Burns-style moves and quick photo montages.
- **Vertical clips** (50 iPhone clips plus 21 WeChat clips) go straight into the Xiaohongshu cuts.
- **from_wechat** has no capture metadata. These are probably clips and photos shared by other participants, so they will be placed by what Gemini sees in them.

## What Gemini saw (21 Oct 2026)

**Method:** three frames per clip (10%, 50% and 90% through) were sent to Gemini (3.5 Flash, 3.5 Flash-Lite and 2.5 Flash, depending on rate limits). For each clip it returned a scene description, the place, readable signage, shot type, quality (1–5), "wow" factor (1–5), best use and FAQ tags. All 270 video clips are covered: 237 from the iPhone and 33 from WeChat. Photos are not analysed yet. Gemini only saw still frames, so it cannot judge audio, and its place names are guesses until Shawn confirms them.

**Agreement with the time-based slots:** 205 clips match, 37 are unclear and 28 do not match. The mismatches are mostly schedule slips (lunch and dinner started earlier than printed) and drive-by shots between venues. Examples:
- 13 Oct 12:26: lunch was a roast-duck restaurant (Shouchailu), not the Admin Bureau
- 14 Oct 15:53: the exterior with the Qiteng Robot sign was filmed during the "Guangyu Mingdao" slot, so the visit order was swapped
- 14 Oct 17:32–17:55: street food and a yurt-style dinner, not Qiteng Robotics
- 15 Oct 11:20: city viewpoint over the Yangtze and Caiyuanba Bridge (Eling area)
- 16 Oct 17:48–17:56: Guanyinqiao plaza and a hotpot dinner, not Shiguangge

### Best footage

| Use | Clip | What it shows |
|---|---|---|
| **Cold-open hook** | from_wechat 6fe5e4fc, a7097042, 13382ed6, 3faeaaa4 (and 3 more) | **Drone light show over the Chongqing skyline** (a giant bird, a cat, Chinese characters) with crowds filming. Rated 5/5 wow. |
| Hook / skyline | 15 Oct IMG_8704 (20:02) | Night skyline and the red Dongshuimen Bridge from Chaotianmen |
| Hongyadong | 15 Oct IMG_8722, IMG_8714, IMG_8705, IMG_8718, IMG_8723 (20:09–20:30) | Lit stilt-house façade, crowds, a street singer. **Note:** the Hongyadong visit was on 15 Oct, not only the 14 Oct clip |
| River | 15 Oct IMG_8739 (20:49) | Neon river-cruise ship |
| 8D / neon | 15 Oct IMG_8748 (21:31); 13 Oct IMG_8397–8398 (20:50) | Jiefangbei LED towers; Guanyinqiao at night |
| Raffles City | 13 Oct IMG_8320–8321 (14:56) | Low-angle shot of the towers and the sky bridge |
| Robots (insider angle) | 14 Oct IMG_8580 (14:52), IMG_8590 (15:05) | **Humanoid robot demo and a robot dog** on an obstacle course at CVTE |
| City planning | 13 Oct IMG_8126, IMG_8134 (09:28–09:41) | Giant city-model screen; immersive dome projection |
| Eling | 15 Oct IMG_8624, IMG_8635 (09:17–09:24) | PS5 warrior mural on an old factory; a staircase street |
| Cable car | from_wechat 280a911c | Yangtze River Cableway cabins over the river |
| Data centre (fills the gap) | from_wechat d77eaa66 | Montage with a group photo at the Western (Chongqing) Science City Advanced Data Center |
| Food | 14 Oct IMG_8606–8619 (18:23–19:06); 13 Oct IMG_8375; 14 Oct IMG_8509, IMG_8515 | Boiling hotpot, a whole roast lamb carved at the table, a toast, a steamed fish |
| Group bonding | from_wechat KTV, birthday cake and square-dance clips | Social side of the programme, useful for "you won't go alone" |

**How the clips spread across topics** (Gemini tags; a clip can have several): culture 128, programme 102, food 99, 8D city 83, tech 51, Singapore–China 44, nightlife 42, hotpot 34, robotics 16, transit 15, weather 15, history 11. **Thin topics:** payments (1), healthcare (4), data centre (1). The narration has to carry these, so plan screen-recordings of the payment apps or cards.
