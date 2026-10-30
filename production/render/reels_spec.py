"""The ep. 1 reels (approved 30 Oct 2026): the series trailer and one reel per day, from day_reels_script_v1.md.
A line is one or more WHOLE recorded takes (beat id, take index in timeline2.json); ('B55', 0, 1) means "the first
sentence of that take only", cut at the real pause after it. Pictures are real clips; P/L orientation is in
shot_log.csv. Optional lines from the script are left out to keep each reel at about a minute.

Segment kinds:  ('line', takes, clips, text)   ('music', seconds, clips)   ('silence', seconds)
Flags (dict, optional 5th item): drop = riser + hit into this segment, low = closing pad + piano from here on,
stop = music cuts dead at the end of this segment, thud = heavy hit on the following silence, cues = {text: word}
"""
WC = 'from_wechat/'
def c(day, n, ext='MOV'): return f'{day} Oct/IMG_{n}.{ext}'
DRONE = WC + '6fe5e4fcdec8065ce4c81bbea8f9c5e1.mp4'; DRONE2 = WC + 'a709704270343b6f0724127d74f2f8db.mp4'
DANCE = WC + '9bda1fa54f8880986d740e6d04642348.mp4'; CABLE = WC + '280a911cf4097c4ed0c1e822876e59f1.mp4'
CROWD = WC + 'fa6c95b5a1e95c26e55f500bfefcdd4d.mp4'; GROUP = WC + 'd77eaa66a900830a7d95e6cc5429fc85.mp4'
GROUP2 = WC + 'd77eaa66a900830a7d95e6cc5429fc85(1).mp4'; LAMB = WC + '63e5c062c790adcfc249d8d240c0f395.mp4'
YURT = WC + '4ffc4d595bfa60' ; RIVER = WC + '2951345ced15cc'; CROWNS = WC + '064ceb5f22044b'   # prefixes, resolved by meta

REELS = {
 'trailer': dict(title='Series trailer', out='shawn_in_china_ep1_trailer_v3_9x16.mp4', tag=None, hook=None,
   cover=dict(f=DRONE, st=16.0, top='📍 CHONGQING, CHINA', big='NOT CGI.', sub='6 DAYS INSIDE', title='THE 8D CITY'),
   segs=[
    ('line', [('B01', 0)], [(DRONE, 16.0)], 'NOT CGI.'),
    ('line', [('B03', 0)], [(c(15, 8741), 0.8), (c(17, 9003), 1.0), (c(17, 9001), 0.3), (c(16, 8877), 0.8)], '6 DAYS.|NOT A TOURIST.',
     dict(cues={'6 DAYS.': 'six', 'NOT A TOURIST.': 'not'})),
    ('line', [('B04', 2)], [(c(13, 8325), 0.67), (c(13, 8359), 0.26), (c(13, 8303), 2.96)], '🔒'),
    ('music', 1.2, [(c(17, 8928), 0.89)], '', dict(drop=True)),
    ('line', [('B07', 1)], [(c(17, 9010), 0.8)], '❓'),
    ('line', [('B10', 1)], [(c(17, 8997), 0.8), (c(16, 8913), 0.8)], '❓'),
    ('line', [('B15', 1)], [(c(16, 8902), 0.6), (c(15, 8682), 1.11), (c(13, 8318), 0.0), (c(17, 8965), 1.44)], '8D?!', dict(cues={'8D?!': '8d'})),
    ('line', [('B27', 0)], [(c(14, 8591), 0.12), (c(14, 8590), 4.46), (c(14, 8580), 38.0)], '🤖', dict(cues={'🤖': 'robots'})),
    ('line', [('B55', 0, 1)], [(c(16, 8904), 0.3), (c(16, 8909), 0.3), (c(16, 8910, 'mov'), 4.0)], '🌶️🌶️🌶️', dict(stop=True, cues={'🌶️🌶️🌶️': 'spicy'})),
    ('silence', 1.0),
    ('line', [('B47', 0)], [(c(15, 8723), 0.8), (DANCE, 13.83), (c(15, 8722), 1.26)], '🌃', dict(drop=True)),
    ('music', 4.8, [(DRONE2, 9.0), (c(15, 8724), 1.31), (LAMB, 3.0), (c(15, 8624), 0.59), (c(16, 8916), 20.0), (CABLE, 4.72),
                    (CROWD, 10.0), (GROUP, 6.97)], '', dict(montage=True)),
    ('line', [('B65', 0)], [(c(15, 8678), 0.0, dict(sp=0.55, push=1.15))], 'IS IT|WORTH IT?', dict(low=True, cues={'IS IT': 'worth', 'WORTH IT?': 'worth'})),
    ('line', [('B05', 3)], [(c(13, 8325), 3.0, dict(sp=0.5, push=1.12))], '', dict(thud=True)),
    ('silence', 1.2),
   ]),
 'day1': dict(title='Day 1 · Before you go', out='shawn_in_china_ep1_day1_9x16.mp4', tag='CHONGQING · DAY 1/6', hook='DO THIS BEFORE CHINA',
   cover=dict(f=c(17, 9010), st=1.0, top='CHONGQING IN 6 DAYS', big='DAY 1', sub='DO THIS', title='BEFORE CHINA'),
   segs=[
    ('line', [('B13', 1)], [(c(17, 8945), 3.0), (c(17, 8959), 3.0)], 'GOOGLE ❌ WHATSAPP ❌|INSTAGRAM ❌'),
    ('line', [('B13', 2), ('B13', 3)], [(c(17, 9002), 0.5), (c(17, 8973), 0.5)], 'AMAP ✅ TRANSLATE ✅', dict(drop=True)),
    ('line', [('B07', 1)], [(c(17, 9010), 0.8)], '❓'),
    ('line', [('B08', 0), ('B08', 1)], [(c(17, 9003), 1.0), (c(13, 8125), 0.69), (c(13, 8121), 0.5)], '🇸🇬 VISA-FREE|30 DAYS'),
    ('line', [('B09', k) for k in range(5)], [(c(17, 8967), 0.5), (c(17, 8971), 0.5), (c(17, 9014), 0.5)], '240-HOUR TRANSIT|CHECK THE OFFICIAL LIST'),
    ('line', [('B10', 1), ('B10', 2), ('B10', 3)], [(c(12, 8092), 0.5), (c(17, 8935), 0.5)], '💵❌ 💳❌'),
    ('line', [('B11', 0), ('B11', 1)], [(c(17, 8994), 0.4), (c(17, 8997), 0.8)], 'ALIPAY ✅|WECHAT PAY ✅'),
    ('line', [('B14', 0), ('B14', 1)], [(c(12, 8059), 0.5), (c(12, 8070), 0.5), (c(12, 8086), 0.5), (c(12, 8089), 0.5), (c(12, 8094), 0.5)],
     'DAY 1 · WELCOME DINNER 🥢'),
   ]),
 'day2': dict(title='Day 2 · The 8D city', out='shawn_in_china_ep1_day2_9x16.mp4', tag='CHONGQING · DAY 2/6', hook='WHY IS IT CALLED THE 8D CITY?',
   cover=dict(f=c(15, 8682), st=1.5, top='CHONGQING IN 6 DAYS', big='DAY 2', sub='THE', title='8D CITY'),
   segs=[
    ('line', [('B15', 1)], [(c(17, 8965), 1.44), (c(17, 8966), 0.5)], '8D?!'),
    ('line', [('B16', 0), ('B16', 1)], [(c(15, 8685), 0.5), (c(15, 8686), 0.5)], '📍 YANGTZE + JIALING', dict(drop=True)),
    ('line', [('B17', 0)], [(c(15, 8682), 1.11)], ''),
    ('line', [('B17', 1)], [(c(15, 8644), 0.5)], ''),
    ('line', [('B17', 2)], [(c(17, 9001), 0.3)], 'G → 8F'),
    ('line', [('B17', 3)], [(c(13, 8318), 0.0), (c(13, 8320), 0.0)], '🗺️❓'),
    ('line', [('B19', 0), ('B19', 1), ('B19', 2)], [(c(13, 8182), 0.5), (c(13, 8134), 0.5)], '32,000,000|≈ AUSTRIA'),
    ('line', [('B20', 0), ('B20', 1)], [(c(13, 8247), 0.5), (c(13, 8249), 0.5)], '🇸🇬🤝🇨🇳'),
    ('line', [('B21', 0)], [(c(13, 8316), 0.5), (c(13, 8321), 0.5)], '#3 · SUZHOU|TIANJIN · CHONGQING'),
    ('line', [('B23', 0), ('B23', 1), ('B23', 2)], [(c(13, 8393), 0.5), (c(13, 8395), 0.5), (c(13, 8396), 1.06), (c(13, 8400), 0.5)], '📍 GUANYINQIAO'),
   ]),
 'day3': dict(title='Day 3 · Robots and a whole roast lamb', out='shawn_in_china_ep1_day3_9x16.mp4', tag='CHONGQING · DAY 3/6',
   hook='ARE ROBOTS REALLY EVERYWHERE?',
   cover=dict(f=c(14, 8580), st=38.5, z=1.2, top='CHONGQING IN 6 DAYS', big='DAY 3', sub='ROBOTS &', title='A WHOLE LAMB'),
   segs=[
    ('line', [('B27', 0)], [(c(14, 8591), 0.12), (c(14, 8580), 38.0)], '🤖?'),
    ('line', [('B28', 0)], [(c(14, 8581), 0.5)], '', dict(drop=True)),
    ('line', [('B28', 1)], [(c(14, 8590), 4.46)], '🐕'),
    ('line', [('B28', 2)], [(c(14, 8589), 0.5), (c(14, 8587), 0.5)], ''),
    ('line', [('B28', 3)], [(c(14, 8595), 0.5)], ''),
    ('line', [('B29', 0), ('B31', 0)], [(c(14, 8602), 0.5), (YURT, 1.0)], '⛺'),
    ('line', [('B32', 0)], [(c(14, 8605), 0.5), (c(14, 8606), 0.5)], ''),
    ('line', [('B33', 0), ('B33', 1)], [(c(14, 8609), 3.72), (LAMB, 3.0)], '🐑 WHOLE ROAST LAMB'),
    ('line', [('B34', 0), ('B34', 1)], [(c(14, 8611), 0.5), (c(14, 8616), 0.5), (c(14, 8621), 0.5)], '🧤'),
    ('line', [('B35', 0)], [(c(14, 8619), 0.5), (c(14, 8617), 0.5)], 'NO MALA 🙅'),
    ('line', [('B36', 0)], [(c(14, 8618), 0.3)], ''),
   ]),
 'day4': dict(title='Day 4 · Eling and Hongyadong', out='shawn_in_china_ep1_day4_9x16.mp4', tag='CHONGQING · DAY 4/6', hook='NOT JUST NEON',
   cover=dict(f=c(15, 8722), st=1.5, top='CHONGQING IN 6 DAYS', big='DAY 4', sub='THE NIGHT', title='EVERYONE COMES FOR'),
   segs=[
    ('line', [('B37', 0)], [(c(15, 8666), 0.5)], ''),
    ('line', [('B38', 0)], [(c(15, 8629), 0.5), (c(15, 8630), 0.5)], '📍 ELING NO. 2 FACTORY|1940s 💴', dict(drop=True)),
    ('line', [('B39', 0)], [(c(15, 8672), 0.3), (c(15, 8673), 5.0), (c(15, 8640), 0.5), (c(15, 8624), 0.59)], '🎮', dict(cues={'🎮': 'playstation'})),
    ('line', [('B43', 0)], [(c(15, 8741), 0.8)], '📍 HONGYADONG'),
    ('line', [('B44', 0)], [(c(15, 8722), 1.26), (c(15, 8724), 1.31)], '✨'),
    ('line', [('B45', 0), ('B45', 1), ('B45', 2)], [(c(15, 8718), 0.5), (c(15, 8720), 0.5)], '⏰ AFTER 8 PM'),
    ('line', [('B46', 0), ('B46', 1)], [(c(15, 8723), 0.8)], ''),
    ('line', [('B47', 0), ('B47', 1), ('B47', 2)], [(DANCE, 13.83), (c(15, 8748), 0.3)], 'SAFE? ✅|MIND YOUR PHONE'),
    ('line', [('B48', 0), ('B48', 1)], [(RIVER, 2.0), (c(15, 8737), 0.5), (c(15, 8704), 0.5), (c(15, 8740), 0.5)], '', dict(low=True)),
   ]),
 'day5': dict(title='Day 5 · Data centres and hotpot', out='shawn_in_china_ep1_day5_9x16.mp4', tag='CHONGQING · DAY 5/6',
   hook='HOW SPICY IS CHONGQING HOTPOT?',
   cover=dict(f=c(16, 8909), st=0.5, top='CHONGQING IN 6 DAYS', big='DAY 5', sub='HOW SPICY IS', title='THE HOTPOT?'),
   segs=[
    ('line', [('B49', 0)], [(c(16, 8780), 0.5)], 'THE NERDY DAY 🤓'),
    ('line', [('B50', k) for k in range(4)], [('VIZ:map', 0.0, dict(d_max=9.9))], '', dict(drop=True)),
    ('line', [('B51', 0), ('B51', 1), ('B51', 2)], [(c(16, 8808), 0.5), (c(16, 8790), 0.5), (GROUP, 6.97)], '📵'),
    ('line', [('B54', 0)], [(c(16, 8902), 0.6), (c(16, 8903), 0.5)], ''),
    ('line', [('B55', 0)], [(c(16, 8904), 0.3), (c(16, 8906), 0.0)], '🌶️🌶️🌶️🌶️🌶️'),
    ('line', [('B56', 0)], [(c(16, 8909), 0.3)], '麻 + 辣|NUMB + HOT'),
    ('line', [('B57', 0), ('B57', 1), ('B57', 2)], [(c(16, 8910, 'mov'), 4.0)], '☯️'),
    ('line', [('B58', k) for k in range(6)], [(c(16, 8923), 0.5), (c(16, 8916), 20.0), (c(16, 8913), 0.8), (c(16, 8911), 0.5), (c(16, 8914), 0.5)],
     '📍 JIEFANGBEI FOOD STREET'),
    ('line', [('B59', 0)], [(c(16, 8917), 0.5)], '💸?'),
   ]),
 'day6': dict(title='Day 6 · On my own, and was it worth it?', out='shawn_in_china_ep1_day6_9x16.mp4', tag='CHONGQING · DAY 6/6',
   hook='A TRAIN THROUGH A BUILDING?',
   cover=dict(f=c(17, 8928), st=1.5, z=1.1, top='CHONGQING IN 6 DAYS', big='DAY 6', sub='A TRAIN THROUGH', title='A BUILDING?'),
   segs=[
    ('line', [('B60', 1)], [(c(17, 8931), 0.5), (c(17, 8936), 2.0)], 'DAY 6 · ON MY OWN'),
    ('line', [('B61', 0)], [(c(17, 8970), 0.5), (c(17, 8928), 0.89), (c(17, 8924), 0.5)], '📍 LIZIBA 🚝', dict(drop=True)),
    ('line', [('B61', 1)], [(c(15, 8637), 0.5)], '👟'),
    ('line', [('B62', 0)], [(CABLE, 4.72)], '🚡'),
    ('line', [('B63', 0)], [(c(17, 8937), 0.5)], ''),
    ('line', [('B64', 0), ('B64', 1)], [(c(17, 8953), 3.0), (c(17, 8946), 3.0), (c(17, 9012), 0.5)], ''),
    ('line', [('B65', 0)], [(c(17, 8988), 0.5)], 'WORTH IT?', dict(low=True)),
    ('line', [('B66', 0), ('B66', 1), ('B66', 2)], [(GROUP2, 3.0), (c(13, 8156), 0.5), (CROWNS, 1.0)], ''),
    ('line', [('B67', 0), ('B67', 1)], [(c(16, 8815), 0.5), (c(16, 8818), 0.5)], 'NP TRAVEL & LEARN|CHONGQING'),
   ]),
}
