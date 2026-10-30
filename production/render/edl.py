# Edit decision list for Shawn in China ep. 1.
# Each paragraph of the approved script maps to the shots that play under it.
# Shot spec: "Folder/File" or "Folder/File@start" (seconds into the clip).
# "nat:N" after a shot = let it play N seconds with natural sound, no VO.
# pool("12 Oct", "17:5", "19:3") = extra footage from that day/time window, used to fill.
W = "from_wechat/"
P = [
 # 0 cold open
 dict(id="P01", anchor="That's not CGI", shots=[W+"6fe5e4fcdec8065ce4c81bbea8f9c5e1.mp4", W+"a709704270343b6f0724127d74f2f8db.mp4", W+"3faeaaa435368838861e3fbccf7832ac.mp4", W+"118e9c31620f52122bdafc3977f4b0d8.mp4"], music="drone"),
 dict(id="P02", anchor="I spent six days here", shots=["14 Oct/IMG_8580.MOV@40", "13 Oct/IMG_8247.MOV", "14 Oct/IMG_8470.MOV", "14 Oct/IMG_8590.MOV", "15 Oct/IMG_8722.MOV"]),
 dict(id="P03", anchor="So this video does two things", shots=["16 Oct/IMG_8916.MOV@20", "15 Oct/IMG_8714.MOV", W+"3c126a79426b816bc5be8f9bbdbbed7e.mp4"], card="CHONGQING · 6 DAYS · 1 STUDY MISSION"),
 # 1 who I am
 dict(id="P04", anchor="I'm Shawn, I'm Singaporean", shots=["12 Oct/IMG_8029.jpg", "12 Oct/IMG_8031.jpg", "12 Oct/IMG_8037.jpg"], title="SHAWN IN CHINA"),
 # 2 day 1
 dict(id="P05", anchor="First question everyone asked me", shots=["12 Oct/IMG_8030.jpg", "12 Oct/IMG_8050.jpg"], chapter="DAY 1 · Before you go", card="Singapore passport: 30 days visa-free (since 9 Feb 2024)"),
 dict(id="P06", anchor="Not Singaporean?", shots=["12 Oct/IMG_8058.jpg", "12 Oct/IMG_8066.jpg"], card="Other passports: check 240-hour visa-free transit"),
 dict(id="P07", anchor="Second question: how do you pay", shots=["12 Oct/IMG_8092.MOV", "16 Oct/IMG_8913.MOV", "17 Oct/IMG_8994.MOV", "17 Oct/IMG_8997.MOV"], card="Alipay + WeChat Pay accept foreign cards · set up before you fly"),
 dict(id="P08", anchor="Third: Google, WhatsApp", shots=["17 Oct/IMG_8962.MOV", "17 Oct/IMG_9001.MOV", "17 Oct/IMG_9002.MOV"]),
 dict(id="P09", anchor="Then: welcome dinner", shots=["12 Oct/IMG_8059.MOV", "12 Oct/IMG_8070.MOV", "12 Oct/IMG_8089.MOV", "12 Oct/IMG_8074.MOV", "12 Oct/IMG_8086.MOV", "12 Oct/IMG_8094.MOV"]),
 # 3 day 2
 dict(id="P10", anchor="Quick context, because Chongqing", shots=["15 Oct/IMG_8704.MOV", "17 Oct/IMG_8965.MOV"], chapter="DAY 2 · The 8D city"),
 dict(id="P11", anchor="It's built on mountains", shots=["15 Oct/IMG_8685.MOV", "15 Oct/IMG_8686.MOV", "17 Oct/IMG_8966.MOV", "15 Oct/IMG_8682.MOV", "17 Oct/IMG_9001.MOV"], card="8D = mountains + two rivers + no flat ground"),
 dict(id="P12", anchor="We started at the Planning Exhibition", shots=["13 Oct/IMG_8126.MOV", "13 Oct/IMG_8134.MOV", "13 Oct/IMG_8137.MOV"], pool=("13 Oct", "09:15", "10:30")),
 dict(id="P13", anchor="Then a briefing I didn't expect", shots=["13 Oct/IMG_8247.MOV", "13 Oct/IMG_8249.MOV", "13 Oct/IMG_8320.MOV", "13 Oct/IMG_8321.MOV", "13 Oct/IMG_8319.MOV"], pool=("13 Oct", "11:00", "12:20")),
 dict(id="P14", anchor="Even the hospital we visited", shots=[], pool=("13 Oct", "16:35", "17:35")),
 dict(id="P15", anchor="And at night, Guanyinqiao", shots=["13 Oct/IMG_8397.MOV", "13 Oct/IMG_8398.MOV"], pool=("13 Oct", "20:10", "21:00")),
 # 4 day 3
 dict(id="P16", anchor="Day three. Our group split", shots=[], pool=("14 Oct", "09:50", "10:10"), chapter="DAY 3 · Robots & medtech"),
 dict(id="P17", anchor="First stop: Liangjiang Life Science", shots=["14 Oct/IMG_8409.MOV", "14 Oct/IMG_8428.MOV"], pool=("14 Oct", "09:50", "10:20")),
 dict(id="P18", anchor="Then Haifu Medical", shots=["14 Oct/IMG_8470.MOV"], pool=("14 Oct", "10:20", "11:12")),
 dict(id="P19", anchor="And then the afternoon everyone", shots=["14 Oct/IMG_8580.MOV@5"], nat=("14 Oct/IMG_8580.MOV@60", 7)),
 dict(id="P20", anchor="This humanoid danced for us", shots=["14 Oct/IMG_8580.MOV@120", "14 Oct/IMG_8590.MOV", "14 Oct/IMG_8580.MOV@200"], pool=("14 Oct", "14:50", "16:01"), card="CVTE · Guangyu Mingdao · Qiteng Robotics"),
 dict(id="P21", anchor="Dinner. Okay, honest answer", shots=["14 Oct/IMG_8606.MOV", "14 Oct/IMG_8611.MOV", "14 Oct/IMG_8613.MOV@10", "14 Oct/IMG_8609.MOV", "14 Oct/IMG_8619.MOV", "14 Oct/IMG_8617.MOV", "16 Oct/IMG_8909.MOV"]),
 # 5 day 4
 dict(id="P22", anchor="If you think Chongqing is only neon", shots=["15 Oct/IMG_8624.MOV", "15 Oct/IMG_8635.MOV"], pool=("15 Oct", "09:15", "10:15"), chapter="DAY 4 · Eling & Hongyadong"),
 dict(id="P23", anchor="In the afternoon, the Connectivity", shots=["15 Oct/IMG_8684.MOV", "15 Oct/IMG_8687.MOV", "15 Oct/IMG_8690.MOV", "15 Oct/IMG_8697.MOV"]),
 dict(id="P24", anchor="And then the night everyone comes for", shots=["15 Oct/IMG_8705.MOV"], nat=("15 Oct/IMG_8714.MOV", 4)),
 dict(id="P25", anchor="It's a cliffside complex", shots=["15 Oct/IMG_8722.MOV", "15 Oct/IMG_8724.MOV", "15 Oct/IMG_8718.MOV", "15 Oct/IMG_8741.MOV"], card="Hongyadong tip: go after 8pm · watch from the river side"),
 dict(id="P26", anchor="Is it safe at night", shots=["15 Oct/IMG_8723.MOV", "15 Oct/IMG_8748.MOV"], pool=("15 Oct", "20:10", "21:35")),
 dict(id="P27", anchor="And stand on the river side", shots=["15 Oct/IMG_8737.MOV", "15 Oct/IMG_8739.MOV", "15 Oct/IMG_8740.MOV", "15 Oct/IMG_8704.MOV"]),
 # 6 day 5
 dict(id="P28", anchor="Day five was the nerdy day", shots=["16 Oct/IMG_8780.MOV"], pool=("16 Oct", "09:30", "10:10"), chapter="DAY 5 · Data, ageing & food"),
 dict(id="P29", anchor="Ever heard of", shots=["MAP", W+"d77eaa66a900830a7d95e6cc5429fc85.mp4"]),
 dict(id="P30", anchor="The other theme that week was ageing", shots=[], pool=("15 Oct", "10:55", "12:30"), pool2=("16 Oct", "16:45", "17:45")),
 dict(id="P31", anchor="Then, food", shots=["16 Oct/IMG_8911.MOV", "16 Oct/IMG_8913.MOV", "16 Oct/IMG_8914.MOV", "16 Oct/IMG_8916.MOV@40"], nat=("16 Oct/IMG_8916.MOV@70", 5)),
 dict(id="P32", anchor="Is it expensive?", shots=["16 Oct/IMG_8910.mov", "16 Oct/IMG_8859.MOV", "16 Oct/IMG_8916.MOV@95"]),
 # 7 day 6
 dict(id="P33", anchor="Last morning: a reflection session", shots=["17 Oct/IMG_8924.MOV"], chapter="DAY 6 · On my own"),
 dict(id="P34", anchor="Getting around is easier", shots=["17 Oct/IMG_8928.MOV", "17 Oct/IMG_8970.MOV", "17 Oct/IMG_8974.MOV", "17 Oct/IMG_9010.MOV"]),
 dict(id="P35", anchor="I took the cableway", shots=[W+"280a911cf4097c4ed0c1e822876e59f1.mp4", "17 Oct/IMG_8937.MOV", "17 Oct/IMG_8953.MOV", "17 Oct/IMG_8959.MOV", "17 Oct/IMG_9012.MOV", "17 Oct/IMG_9013.MOV", "17 Oct/IMG_9003.MOV", "17 Oct/IMG_9004.MOV"]),
 # 8 close
 dict(id="P36", anchor="So, is a study trip worth it", shots=["17 Oct/IMG_8985.MOV", "17 Oct/IMG_8988.MOV"], chapter="Was it worth it?"),
 dict(id="P37", anchor="For me, yes", shots=[W+"d77eaa66a900830a7d95e6cc5429fc85(1).mp4", "14 Oct/IMG_8617.MOV", "13 Oct/IMG_8249.MOV"]),
 dict(id="P38", anchor="The programme I went on is Ngee Ann", shots=["13 Oct/IMG_8126.MOV", "15 Oct/IMG_8684.MOV"], card="NP Travel & Learn to Chongqing · link in description"),
 dict(id="P39", anchor="When should you go", shots=["15 Oct/IMG_8679.MOV", "17 Oct/IMG_8986.MOV"]),
 dict(id="P40", anchor="Got a question about Chongqing", shots=[W+"13382ed6c6fb285482475810b36d1ae9.mp4", W+"fa6c95b5a1e95c26e55f500bfefcdd4d.mp4"], end=True),
]
