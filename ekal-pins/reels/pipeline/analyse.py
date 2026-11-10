import librosa, numpy as np, json, sys, glob, os
out={}
for f in sorted(glob.glob('/mnt/user-data/uploads/*.wav')+glob.glob('/mnt/user-data/uploads/*.mp3')):
    y,sr=librosa.load(f,sr=22050,mono=True,duration=240)
    tempo,beats=librosa.beat.beat_track(y=y,sr=sr)
    bt=librosa.frames_to_time(beats,sr=sr)
    rms=librosa.feature.rms(y=y)[0]; rt=librosa.frames_to_time(np.arange(len(rms)),sr=sr)
    # energy per 16s window starting on beats; prefer windows after 8s
    best=None
    for b in bt:
        if b<6 or b+16>rt[-1]: continue
        m=(rt>=b)&(rt<b+16); e=rms[m].mean()
        # bonus: strong onset at start
        s=(rt>=b)&(rt<b+0.5); pre=(rt>=b-1)&(rt<b)
        jump=rms[s].mean()/(rms[pre].mean()+1e-6)
        sc=e*(1+0.15*min(jump,3))
        if best is None or sc>best[0]: best=(sc,b)
    name=os.path.basename(f)
    out[name]=dict(tempo=float(np.atleast_1d(tempo)[0]),beats=[round(float(x),3) for x in bt],best_start=round(float(best[1]),3),mean_rms=float(rms.mean()))
    print(name, round(out[name]['tempo'],1),'bpm best@',out[name]['best_start'],'dur',round(rt[-1],1))
json.dump(out,open('/home/claude/work/audio/analysis.json','w'))
