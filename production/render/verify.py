import json, sys, subprocess, base64, os, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gem import gemini
WD = sys.argv[1]; ids = [int(x) for x in sys.argv[2].split(',')]
ch = json.load(open(f'{WD}/vo/chunks.json'))['chunks']
exp = json.load(open(sys.argv[3]))
VOCAB = "Chongqing, Jiefangbei, Guanyinqiao, Liangjiang, Liziba, Hongyadong, Eling, Suzhou, Tianjin, Austria, mala, yuanyang, HIFU, Haifu, Ngee Ann Polytechnic, SkillsFuture, Yangtze, Jialing, drones, tourist"
def go(i):
    a, b = ch[i]
    mp3 = subprocess.run(['ffmpeg','-nostdin','-v','error','-ss',str(a),'-to',str(b),'-i',f'{WD}/vo_raw.wav','-ac','1','-b:a','96k','-f','mp3','-'],capture_output=True).stdout
    r = gemini([{"text": f"A Singaporean narrator is reading a travel-vlog script about Chongqing. Proper nouns that may appear: {VOCAB}. "
                 f"The script line around this point is: \"{exp.get(str(i),'')}\". Listen carefully and transcribe EXACTLY what is said (do not just copy the script; report real slips, but do not treat accent as a slip). "
                 "Return JSON {\"heard\": \"...\", \"slip\": true|false, \"slip_detail\": \"what differs in substance from the script, or empty\", \"word_times\": [[word, start_s, end_s], ...]} with times relative to this clip."},
                {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}], models=['gemini-2.5-flash','gemini-3.5-flash'])
    return i, r
out = {}
with cf.ThreadPoolExecutor(4) as ex:
    for i, r in ex.map(go, ids): out[i] = r
json.dump(out, open(f'{WD}/vo/verify.json','w'), ensure_ascii=False, indent=1)
for i in ids: print(i, ch[i], '|', out[i].get('heard'), '| slip:', out[i].get('slip'), out[i].get('slip_detail'))
