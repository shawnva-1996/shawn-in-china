"""Cut the reel's VO lines from the RAW recording at real pauses, so no word loses its first or last sound.
The main edit's pieces (and the word times) are only accurate to about ±0.1 s, which is fine inside a long take
but clips the edges when a line is lifted out on its own. For each line this finds the quiet gap before the first
word and after the last one in vo_raw.wav, keeps a little room tone either side, and fades only inside that quiet.
usage: reel_vo.py <timeline2.json> <vo_raw.wav> <reel.json> [--verify]
adds 'raw' [start, end] and 'pre' to each reel.json vo line. --verify cuts every line as its own clip and asks Gemini
(gem.py, key pool from the shoot folder) for the words it hears and whether the first or last word is clipped;
each line gets a 'check' entry, and any line that isn't the full expected sentence is printed as FAIL. Expected text
comes from the line's 'text' field in reel.json.
"""
import json, subprocess, sys
import numpy as np

SR = 16000; HOP = 0.01
MARGIN = 7.0         # dB above the local room-tone floor that still counts as a pause (room tone drifts -52..-41 dB)

def energy(path):
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                                     capture_output=True, check=True).stdout, np.float32)
    h = int(HOP * SR); w = 3 * h
    return 20 * np.log10(np.array([np.sqrt(np.mean(x[k:k + w] ** 2)) for k in range(0, len(x) - w, h)]) + 1e-9)

def quiet(edb, i):
    return np.percentile(edb[max(0, i - 150):i + 150], 10) + MARGIN

def start_of(edb, t, back=0.5):
    """latest pause (>= 50 ms of room tone) that ends at or before the voice onset near t; else the deepest valley"""
    i = int(t / HOP) + 4; q = quiet(edb, i)
    for k in range(i, max(5, i - int(back / HOP)), -1):
        if np.all(edb[k - 5:k] < q): return (k - 1) * HOP
    j0 = i - 25; return (j0 + int(np.argmin(edb[j0:i + 1]))) * HOP

def end_of(edb, t, fwd=0.8):
    """first pause (>= 120 ms of room tone) after the last word near t; end 0.1 s into it (natural decay)"""
    i = max(0, int(t / HOP) - 10); q = quiet(edb, i)
    for k in range(i, i + int(fwd / HOP)):
        if np.all(edb[k:k + 12] < q): return k * HOP + 0.10
    j1 = i + int(fwd / HOP); return (i + int(np.argmin(edb[i:j1]))) * HOP

def main(tl_path, raw_path, reel_path):
    tl = json.load(open(tl_path)); pieces = [p for b in tl['beats'] for p in b['pieces']]
    R = json.load(open(reel_path)); edb = energy(raw_path)
    for v in R['vo']:
        a, e = v['src']
        p = next(p for p in pieces if p['at'] - 0.05 <= a < p['at'] + p['src'][1] - p['src'][0])
        ar = p['src'][0] + (a - p['at']); er = p['src'][0] + (e - p['at'])
        s, f = start_of(edb, ar), end_of(edb, er)
        v['raw'] = [round(s, 3), round(f, 3)]; v['pre'] = round(ar - s, 3)      # pre: how much earlier the clip starts
        print(f"{v['at']:5.1f}  {ar:8.2f}->{s:8.2f} ({ar - s:+.2f})   {er:8.2f}->{f:8.2f} ({f - er:+.2f})", file=sys.stderr)
    json.dump(R, open(reel_path, 'w'), indent=1, ensure_ascii=False)

def verify(raw_path, reel_path):
    import base64, re, tempfile
    from gem import gemini
    R = json.load(open(reel_path)); bad = 0
    norm = lambda t: re.sub(r'[^a-z0-9 ]', '', t.lower().replace("'", '')).split()
    for v in R['vo']:
        s, f = v['raw']
        with tempfile.NamedTemporaryFile(suffix='.wav') as tmp:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(s), '-t', str(f - s), '-i', raw_path, '-af', 'highpass=f=80,afftdn=nr=12:nf=-40',
                            '-ar', '16000', '-ac', '1', tmp.name], check=True)
            b = base64.b64encode(open(tmp.name, 'rb').read()).decode()
        r = gemini([{"inline_data": {"mime_type": "audio/wav", "data": b}},
                    {"text": f'A voice clip cut out of a longer narration. Expected words: "{v["text"]}". Return JSON: '
                             '{"transcript": verbatim words you hear, "first_word_clipped": bool, "last_word_clipped": bool, '
                             '"missing_words": [expected words you did not hear], "extra_words": [words heard that are not expected]}'}])
        ok = not (r.get('first_word_clipped') or r.get('last_word_clipped') or r.get('missing_words') or r.get('extra_words'))
        ok = ok and norm(r.get('transcript', ''))[-1:] == norm(v['text'])[-1:]
        v['check'] = dict(r, ok=ok); bad += not ok
        print('ok  ' if ok else 'FAIL', v['text'], '=>', r.get('transcript'), file=sys.stderr)
    json.dump(R, open(reel_path, 'w'), indent=1, ensure_ascii=False)
    return bad

if __name__ == '__main__':
    main(*sys.argv[1:4])
    if '--verify' in sys.argv: sys.exit(1 if verify(sys.argv[2], sys.argv[3]) else 0)
