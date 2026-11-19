import sys, json, os
import numpy as np, soundfile as sf
sys.path.insert(0, '/home/claude/quiz-shorts')
from tts import say
SR = 44100
D = os.path.dirname(os.path.abspath(__file__))
# (kind, spoken, caption, q index)
lines = [
 ('intro', "Can you name all five flags?", "Can you name all 5 flags?", -1),
 ('intro2', "Easy to expert. Let's go!", "Easy → expert. Let's go!", -1),
]
Q = [("Flag one. Easy.", "China! Five gold stars on a red field."),
     ("Flag two.", "Greece! Nine blue and white stripes."),
     ("Flag three. Getting harder.", "The Philippines! In wartime, the red goes on top."),
     ("Flag four.", "Cambodia! That's the Angkor Wat temple on the flag."),
     ("Last one. Expert level.", "Mongolia! The gold symbol is called the Soyombo.")]
for i,(q,a) in enumerate(Q):
    lines.append(('q', q, q, i)); lines.append(('a', a, a, i))
lines += [('outro', "How many did you get? Comment your score!", "How many did you get?", -1),
          ('outro2', "And follow for a daily quiz.", "Follow for a daily quiz!", -1)]
t = 0.7; out = []; sent = []
for kind, sp, cap, qi in lines:
    w = say(sp, voice='af_heart', speed=1.08)
    st = t; out.append((st, w)); en = st + len(w)/SR
    sent.append(dict(kind=kind, cap=cap, start=round(st,3), end=round(en,3), q=qi))
    gap = {'intro':0.15,'intro2':0.45,'q':3.25,'a':0.55,'outro':0.15,'outro2':0}[kind]
    t = en + gap
end = t + 1.8
buf = np.zeros(int(end*SR)+SR, np.float32)
for st, w in out:
    i = int(st*SR); buf[i:i+len(w)] += w
buf = buf[:int(end*SR)]
sf.write(os.path.join(D,'..','assets','audio','stems','voice.wav'), buf, SR)
json.dump(dict(end=round(end,3), sent=sent), open(os.path.join(D,'timeline.json'),'w'), indent=1)
print(end); [print(s) for s in sent]
