import librosa, numpy as np, glob, os, json, sys
fs=sorted(glob.glob('/mnt/user-data/uploads/*.wav')+glob.glob('/mnt/user-data/uploads/*.mp3'))
rows=[]; an=json.load(open('audio/analysis.json'))
for f in fs:
    n=os.path.basename(f)
    y,sr=librosa.load(f,sr=22050,mono=True)
    dur=len(y)/sr
    tempo,beats=librosa.beat.beat_track(y=y,sr=sr); bt=librosa.frames_to_time(beats,sr=sr)
    S=np.abs(librosa.stft(y,n_fft=2048,hop_length=512))
    freqs=librosa.fft_frequencies(sr=sr,n_fft=2048)
    cent=librosa.feature.spectral_centroid(S=S,sr=sr)[0]
    flat=librosa.feature.spectral_flatness(S=S)[0]
    hf=(S[freqs>5000]**2).sum(0)/((S**2).sum(0)+1e-9)
    H,P=librosa.decompose.hpss(S)
    harm=(H**2).sum()/((H**2).sum()+(P**2).sum())
    rms=librosa.feature.rms(S=S)[0]
    # intro: time until rms reaches 60% of median of loud part
    thr=0.6*np.percentile(rms,70); idx=np.argmax(rms>thr); intro=idx*512/sr
    pulse=librosa.beat.plp(y=y,sr=sr).mean()
    rows.append(dict(name=n,dur=round(dur,1),bpm=round(float(np.atleast_1d(tempo)[0]),1),centroid=int(np.median(cent)),hf=round(float(np.median(hf))*100,1),flat=round(float(np.median(flat))*1000,1),harm=round(float(harm),2),intro=round(intro,1),dyn=round(float(np.percentile(rms,95)/(np.percentile(rms,20)+1e-6)),1)))
    an[n]=dict(tempo=float(np.atleast_1d(tempo)[0]),beats=[round(float(x),3) for x in bt],mean_rms=float(rms.mean()))
    print(rows[-1],flush=True)
json.dump(an,open('audio/analysis.json','w')); json.dump(rows,open('audio/audit.json','w'))
