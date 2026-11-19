import json, os, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
SR = 44100
D = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(D, '..')
TL = json.load(open(os.path.join(P, 'build', 'timeline.json')))
voice, _ = sf.read(os.path.join(P, 'assets/audio/stems/voice.wav'), dtype='float32')
N = len(voice); rng = np.random.default_rng(7)
def t(n): return np.arange(n)/SR
def env(n, a=0.005, r=0.2):
    e = np.exp(-t(n)/r); k = int(a*SR); e[:k] *= np.linspace(0,1,k); return e
def add(buf, x, at, g=1.0):
    i = int(at*SR); 
    if i >= len(buf): return
    x = x[:len(buf)-i]; buf[i:i+len(x)] += g*x
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def lp(x, f): return sosfilt(butter(2, f, 'low', fs=SR, output='sos'), x)
def mtof(m): return 440*2**((m-69)/12)
# ---- music: 120 bpm, Am-F-C-G
bpm = 120; beat = 60/bpm; mus = np.zeros(N, np.float32)
prog = [(57,[57,60,64]),(53,[53,57,60]),(48,[48,52,55,60]),(55,[55,59,62])]
def pluck(f, dur=0.35):
    n=int(dur*SR); L=max(2,int(SR/f)); buf=rng.uniform(-1,1,L); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%L]; buf[i%L]=0.5*(buf[i%L]+buf[(i+1)%L])*0.996
    return out*env(n,0.002,0.25)
def saw(f, n): ph=(t(n)*f)%1; return 2*ph-1
cache={}
bar = 4*beat; nb = int(TL['end']/bar)+2
for b in range(nb):
    root, ch = prog[b%4]; t0 = b*bar
    n = int(bar*SR)
    pad = sum(saw(mtof(m)*d, n) for m in ch for d in (0.997,1.003))/ (2*len(ch))
    pad = lp(pad, 1400)*0.18; e = np.minimum(1, t(n)/0.3)*np.minimum(1,(bar-t(n))/0.3)
    add(mus, (pad*e).astype(np.float32), t0)
    for k in range(4):   # sub pulse + kick
        n2=int(0.25*SR); kick=np.sin(2*np.pi*(50+90*np.exp(-t(n2)/0.03))*t(n2))*env(n2,0.001,0.09)
        add(mus, kick.astype(np.float32), t0+k*beat, 0.55)
        sub=np.sin(2*np.pi*mtof(root-12)*t(int(beat*SR)))*env(int(beat*SR),0.01,0.25)
        add(mus, sub.astype(np.float32), t0+k*beat, 0.22)
        n3=int(0.05*SR); hat=bp(rng.standard_normal(n3),7000,12000)*env(n3,0.001,0.015)
        add(mus, hat.astype(np.float32), t0+k*beat+beat/2, 0.25)
    for k in range(8):   # arp
        m = ch[k % len(ch)] + 12*(1 if k%4>1 else 0)
        key=m
        if key not in cache: cache[key]=pluck(mtof(m)).astype(np.float32)
        add(mus, cache[key], t0+k*beat/2, 0.22)
fade=np.ones(N); fl=int(1.5*SR); fade[-fl:]=np.linspace(1,0,fl); mus*=fade
# duck under speech
dk = np.ones(N)
for s in TL['sent']:
    a,b=int((s['start']-0.08)*SR),int((s['end']+0.1)*SR); dk[a:b]=10**(-6/20)
dk = np.convolve(dk, np.ones(2205)/2205, 'same'); mus*=dk
# ---- sfx
fx = np.zeros(N, np.float32)
def whoosh(d=0.45):
    n=int(d*SR); x=rng.standard_normal(n); c=np.linspace(400,4000,n)
    y=np.zeros(n); 
    for j in range(0,n,1024):
        seg=x[j:j+1024]; f=c[j]; y[j:j+len(seg)]=bp(seg,f*0.6,min(f*1.6,18000))
    e=np.sin(np.pi*np.clip(t(n)/d,0,1))**2; return y*e
def tick(): n=int(0.06*SR); return (np.sin(2*np.pi*1800*t(n))*env(n,0.001,0.012) + 0.3*bp(rng.standard_normal(n),3000,8000)*env(n,0.001,0.006))
def ding():
    n=int(1.2*SR); return sum(np.sin(2*np.pi*f*t(n))*env(n,0.002,r)*g for f,r,g in [(1318.5,0.5,0.6),(1975.5,0.35,0.35),(2637,0.25,0.2),(659.25,0.6,0.3)])
def pop(): n=int(0.08*SR); return np.sin(2*np.pi*(900-500*t(n)/0.08)*t(n))*env(n,0.002,0.03)
def sparkle():
    out=np.zeros(int(0.7*SR))
    for k,f in enumerate([2093,2637,3136,4186]):
        n=int(0.4*SR); s=np.sin(2*np.pi*f*t(n))*env(n,0.001,0.12); i=int(k*0.06*SR); out[i:i+n]+=s*0.5
    return out
W=whoosh(); TK=tick(); DG=ding(); PP=pop(); SP=sparkle()
S = TL['sent']
add(fx, W, S[0]['start']-0.45, 0.5); add(fx, SP, S[0]['start']+0.3, 0.35)
cues = {'whoosh':[], 'tick':[], 'ding':[]}
for s in S:
    if s['kind']=='q':
        add(fx, W, s['start']-0.08-0.3, 0.55); cues['whoosh'].append(s['start']-0.08)
        for k in range(3): add(fx, PP, s['start']+0.25+k*0.12, 0.35)
        for k in range(3):
            at = s['end']+0.15+k*1.0; add(fx, TK, at, 0.6); cues['tick'].append(at)
    if s['kind']=='a':
        add(fx, DG, s['start']-0.1, 0.45); add(fx, SP, s['start']-0.05, 0.25); cues['ding'].append(s['start']-0.1)
    if s['kind']=='outro':
        add(fx, W, s['start']-0.35, 0.5); add(fx, SP, s['start']+0.1, 0.3)
def rms(x): return 20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
vmask = np.abs(voice)>0.003
def level(x): return rms(x[vmask])
# set music ~ -9 dB, fx peaks independent
mus *= 10**((level(voice)-9 - level(mus))/20)
fx  *= 10**((level(voice)-7 - rms(fx[np.abs(fx)>1e-3]))/20)
mix = voice + mus + fx
def limit(x, ceil=10**(-1/20)):
    a = np.abs(x); look=int(0.005*SR)
    pk = np.maximum.accumulate(a)  # placeholder
    g = np.minimum(1, ceil/np.maximum(a,1e-9))
    g = -np.convolve(-g, np.ones(look), 'same') if False else g
    # min-filter then smooth
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    g = minimum_filter1d(g, look*2); g = uniform_filter1d(g, look)
    return np.clip(x*g, -ceil, ceil)
def lufs(path):
    r = subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',path,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
    return float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
out = os.path.join(P,'assets/audio/soundtrack.wav'); g=1.0
for it in range(6):
    y = limit(mix*g).astype(np.float32); sf.write(out, y, SR); L=lufs(out); print('iter',it,'LUFS',L)
    if abs(L+14)<0.15: break
    g *= 10**((-14-L)/20)
sf.write(os.path.join(P,'assets/audio/stems/music.wav'), mus.astype(np.float32), SR)
sf.write(os.path.join(P,'assets/audio/stems/sfx.wav'), fx.astype(np.float32), SR)
print('voice',level(voice),'music',level(mus),'fx',rms(fx[np.abs(fx)>1e-3]))
json.dump(cues, open(os.path.join(P,'build','cues.json'),'w'))
