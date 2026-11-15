import librosa, numpy as np, json, os, sys
names=sys.argv[1:]
an=json.load(open('audio/analysis.json')); rows=[]
for n in names:
    f='/mnt/user-data/uploads/'+n
    y,sr=librosa.load(f,sr=22050,mono=True); dur=len(y)/sr
    tempo,beats=librosa.beat.beat_track(y=y,sr=sr); bt=librosa.frames_to_time(beats,sr=sr)
    S=np.abs(librosa.stft(y,n_fft=2048,hop_length=512)); fr=librosa.fft_frequencies(sr=sr,n_fft=2048)
    cent=librosa.feature.spectral_centroid(S=S,sr=sr)[0]
    H,P=librosa.decompose.hpss(S); harm=(H**2).sum()/((H**2).sum()+(P**2).sum())
    rms=librosa.feature.rms(S=S)[0]; t=librosa.frames_to_time(np.arange(len(rms)),sr=sr)
    on=librosa.onset.onset_detect(y=y,sr=sr,units='time'); 
    chroma=librosa.feature.chroma_stft(S=S**2,sr=sr)
    # per 4s block: rms, centroid, onsets/s, chroma change (melodic movement)
    blocks=[]
    for b in np.arange(0,dur-4,4):
        m=(t>=b)&(t<b+4)
        cm=chroma[:,m]; mv=np.abs(np.diff(cm,axis=1)).sum(0).mean() if cm.shape[1]>2 else 0
        blocks.append((int(b),round(float(rms[m].mean()),3),int(np.median(cent[m])),round(float(((on>=b)&(on<b+4)).sum()/4),1),round(float(mv),2)))
    lo=(S[fr<250]**2).sum()/(S**2).sum()
    r=dict(name=n,dur=round(dur,1),bpm=round(float(np.atleast_1d(tempo)[0]),1),centroid=int(np.median(cent)),harm=round(float(harm),2),bass=round(float(lo),2),onsets_s=round(len(on)/dur,2),dyn=round(float(np.percentile(rms,95)/(np.percentile(rms,20)+1e-6)),1))
    rows.append(r); print(r); print('  blocks(t,rms,cent,on/s,move):',blocks[:40:2])
    an[n]=dict(tempo=float(np.atleast_1d(tempo)[0]),beats=[round(float(x),3) for x in bt],mean_rms=float(rms.mean()),blocks=blocks)
json.dump(an,open('audio/analysis.json','w')); json.dump(rows,open('audio/audit_soft.json','w'))
