"""Clean Shawn's VO: split on pauses, transcribe each chunk with Gemini, pick the clean take of
every script line, and map kept chunks to script paragraphs.
usage: vo_process.py <vo_wav_48k_mono> <script.md> <outdir>
"""
import json, sys, os, re, subprocess, base64, itertools, time, urllib.request, urllib.error
import concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from edl import P

wav, script, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
keys = json.load(open('/mnt/user-data/uploads/shawn-in-china/new_gemini_pool.json'))
kc = itertools.cycle(range(len(keys)))
MODELS = ['gemini-2.5-flash', 'gemini-3.5-flash', 'gemini-3.5-flash-lite']

def gemini(parts, json_out=True, models=MODELS, tries=15):
    body = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1}}
    if json_out: body["generationConfig"]["responseMimeType"] = "application/json"
    for a in range(tries):
        m = models[a % len(models)]
        req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent',
            data=json.dumps(body).encode(), headers={'x-goog-api-key': keys[next(kc)], 'Content-Type': 'application/json'})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=180))
            t = d['candidates'][0]['content']['parts'][0]['text']
            return json.loads(t) if json_out else t
        except urllib.error.HTTPError as e:
            time.sleep(2 + a)
        except Exception as e:
            time.sleep(2)
    raise RuntimeError('gemini failed')

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav]))

# 1. speech chunks between pauses
def chunks_from(noise, mind):
    log = subprocess.run(['ffmpeg', '-nostdin', '-i', wav, '-af', f'silencedetect=noise={noise}dB:d={mind}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    ss = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
    se = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
    sil = list(zip(ss, se + [dur] * (len(ss) - len(se))))
    ch, cur = [], 0.0
    for a, b in sil:
        if a - cur > 0.15: ch.append([cur, a])
        cur = b
    if dur - cur > 0.15: ch.append([cur, dur])
    return ch

# noise floor from the quietest 10% of 50 ms windows
vol = subprocess.run(['ffmpeg', '-nostdin', '-i', wav, '-af', 'astats=metadata=1:reset=0.05,ametadata=print:key=lavfi.astats.Overall.RMS_level', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
lv = sorted(float(x) for x in re.findall(r'RMS_level=(-?[\d.]+)', vol) if x not in ('-inf',))
floor = lv[len(lv) // 10] if lv else -50
noise = min(-25, floor + 12)
ch = chunks_from(noise, 0.45)
# split very long chunks further with a shorter pause
fin = []
for a, b in ch:
    if b - a > 14:
        sub = [c for c in chunks_from(noise, 0.25) if c[0] >= a - 0.01 and c[1] <= b + 0.01]
        fin += sub if sub else [[a, b]]
    else:
        fin.append([a, b])
ch = [[max(0, a - 0.08), min(dur, b + 0.12)] for a, b in fin]
json.dump(dict(noise=noise, chunks=ch), open(f'{out}/chunks.json', 'w'))
print(len(ch), 'chunks, noise', noise, file=sys.stderr)

# 2. transcribe each chunk
cache = f'{out}/transcripts.json'
tr = json.load(open(cache)) if os.path.exists(cache) else {}
def tx(i):
    a, b = ch[i]
    mp3 = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(a), '-to', str(b), '-i', wav, '-ac', '1', '-b:a', '64k', '-f', 'mp3', '-'], capture_output=True).stdout
    t = gemini([{"text": "Transcribe this English speech verbatim, including false starts, repeated words, fillers (um, uh), and any off-script remarks. Return JSON {\"text\": \"...\"}. If there is no speech, return {\"text\": \"\"}."},
                {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}])
    return i, t.get('text', '')
todo = [i for i in range(len(ch)) if str(i) not in tr]
with cf.ThreadPoolExecutor(4) as ex:
    for i, t in ex.map(tx, todo):
        tr[str(i)] = t
        json.dump(tr, open(cache, 'w'), ensure_ascii=False)
print('transcribed', file=sys.stderr)

# 3. decide keep/drop and paragraph per chunk
paras = "\n".join(f"{p['id']}: starts with \"{p['anchor']}\"" for p in P)
lines = "\n".join(f"[{i}] ({ch[i][0]:.1f}-{ch[i][1]:.1f}s) {tr[str(i)]}" for i in range(len(ch)))
prompt = f"""You are a video editor cleaning a narrator's voice-over recording for a YouTube travel vlog.
Below is the approved script, the list of script paragraphs (P01..P40), and the recording split into numbered chunks with their transcripts.

Rules:
- Produce a clean read that follows the script order. For every script line, keep exactly one take: the last COMPLETE, fluent take (narrators usually re-read after a mistake).
- Drop false starts, stumbles, repeated takes, fillers-only chunks, coughs, silence, and remarks addressed to the editor ("let me redo that", "okay again").
- The script has lines marked [Shawn to confirm ...]. The narrator replaced these with his own words, so KEEP fluent off-script content that sits where those markers are. Never keep the marker text itself.
- Small wording differences from the script are fine; keep natural paraphrases.
- If a chunk mixes a mistake and a good line, keep it but mention it in "note".
Return JSON: {{"chunks": [{{"i": <chunk number>, "keep": true|false, "para": "P##" (for kept chunks), "reason": "short reason", "note": ""}}], "missing": ["script lines with no usable take"]}}

SCRIPT:
{open(script).read()}

PARAGRAPHS:
{paras}

CHUNKS:
{lines}
"""
dec = gemini([{"text": prompt}], models=['gemini-3.5-flash', 'gemini-2.5-flash'])
json.dump(dec, open(f'{out}/decisions.json', 'w'), ensure_ascii=False, indent=1)
k = sum(1 for c in dec['chunks'] if c.get('keep'))
print(f'kept {k}/{len(ch)}; missing: {dec.get("missing")}', file=sys.stderr)
