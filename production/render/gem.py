import json, itertools, time, urllib.request, urllib.error
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

