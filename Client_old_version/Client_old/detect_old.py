import os
import wave
import numpy as np
import matplotlib.pyplot as plt

from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate

from scipy import fftpack
import shutil



def FilterBandpass(wave, fs, low, high):
    ''' 应用带通滤波器 '''
    l = low/(fs/2)
    h = high/(fs/2)
    b, a = signal.butter(8, [l, h], 'bandpass')  # 配置滤波器 8 表示滤波器的阶数
    return signal.filtfilt(b, a, wave)  # data为要过滤的信号


def averageNormalization(corr):
    global cSlice, rid
    distance=24480
    #peaks, _ = signal.find_peaks(corr, height=1000, distance=22491)  # 寻找整个序列的峰值
    peaks=[]
    i=10000
    first=1
    while i+distance < corr.size:
        site=np.argmax(corr[i:i+distance])+i
        if corr[site] > 10000 :
            if first >= 2:
                peaks.append(site)
            else: first+=1
        i+=distance
    cycles = []
    #print(len(peaks))
    for p in peaks:
        c = {}
        c["PeakIndex"] = p
        c["PeakHeight"] = corr[p]
        c["Corr"] = np.abs(corr[p+rid:p+cSlice])
        cycles.append(c)

    count=0
    out = np.zeros(cSlice-rid)
    for i in range(len(cycles)):
        if len(cycles[i]['Corr'])!=(cSlice-rid):
            count+=1
        else:
            out += cycles[i]['Corr']
    length = len(cycles)-count
    out = out/length  # 平均
    return out, np.max(out)


def process(PATH1, PATH2, micnum):
    global cSlice, rid, thdz, thdf, CDcount
    global CandidateD
    global figureno

    low = 20000
    high = 22000
    time = 10/1000 # 10ms
    rate = 48000

    filename1 = f'{PATH1}/mic{micnum}.wav'
    filename2 = f'{PATH2}/mic{micnum}.wav'
    t = np.arange(0, time, 1/rate)
    chirp = signal.chirp(t, low,time, high, method = 'linear')

    # 获得音频原始数据
    Fs, y = wavfile.read(filename1) # 空
    Fs1, y1 = wavfile.read(filename2) # 空

    # 滤波
    fliter_y = FilterBandpass(y, Fs, low, high)
    fliter_y1 = FilterBandpass(y1, Fs1, low, high)

    # 互相关
    corr = np.correlate(fliter_y, chirp, mode='full')
    corr1 = np.correlate(fliter_y1, chirp, mode='full')

    # 平均 and 归一化
    Ncorr, maxv = averageNormalization(corr)
    Ncorr1, maxv1 = averageNormalization(corr1)
    aNcorr = Ncorr/100000
    aNcorr1 = Ncorr1/100000

    #获取极值点    
    x=signal.argrelextrema(aNcorr, np.greater)[0]
    y=aNcorr[x]
    x1=signal.argrelextrema(aNcorr1, np.greater)[0]
    y1=aNcorr1[x1]

    if x.size <=0 or x1.size <= 0:
        return 0,0,0,0,0,x
    x_min=max(x[0],x1[0])
    x_max=min(x[x.size-1],x1[x1.size-1])
    
    #统一坐标轴，插值平滑
    x_new = np.linspace(x_min,x_max,cSlice*2) #!!!cSlice的大小会影响每个区域点的个数
    func=interpolate.interp1d(x,y, kind="cubic")
    y_smooth=func(x_new)
    func1=interpolate.interp1d(x1,y1, kind="cubic")
    y_smooth1=func1(x_new)
    
    if 1 == 1:
        figureno+=1
        plt.figure(figureno)
        label=['Empty','The other']
        #plt.plot(x,y,'o')
        plt.ylim(0,1)
        plt.plot((x_new+rid)/48000*340/2, y_smooth,linewidth=1)
        #plt.plot(x1,y1,'*')
        plt.plot((x_new+rid)/48000*340/2, y_smooth1,c='red',linewidth=1)
        plt.legend(label, loc =0) 
        #plt.title(''.join(['mic',str(micnum)]))
        plt.title('Comparison')
        #plt.title('Envelope Detection')
        plt.xlabel('Distance(m)')
        plt.ylabel('Correlation')
        #plt.show()


    #提取图2(The Other)中高于/低于图1(Empty)的所有点
    X=np.zeros(cSlice*2)
    Y=np.zeros(cSlice*2)
    Y1=np.zeros(cSlice*2)
    i=0
    while i < cSlice*2:
        while i < cSlice*2 and y_smooth1[i] != y_smooth[i] :
            X[i]=x_new[i]
            Y[i]=y_smooth[i]
            Y1[i]=y_smooth1[i]
            if i-2 > 0 and Y1[i-2] > Y1[i-1] and Y1[i] > Y1[i-1] :
                X[i-1]=-0.01
                Y[i-1]=Y1[i-1]=0
            if i-1 > 0 and (Y1[i]-Y[i])*(Y1[i-1]-Y[i-1])<0:
                X[i-1]=-0.01
                Y[i-1]=Y1[i-1]=0
            i+=1
        if i == cSlice*2 : break
        
        X[i]=-0.01
        Y[i]=Y1[i]=0
        i+=1

    site=i
    # 去除不对称的峰
    i=0
    addc=0
    minusc=0
    mark=site

    while i < site :
        while i < site and X[i] < 0 :
           i+=1
        if i >= site :
           break
        mark=i
        while i < site and X[i] >= 0 :
           if i+1 < site and X[i+1] >= 0 :
               if Y1[i+1] > Y1[i] :
                   addc+=1
               if Y1[i+1] < Y1[i] :
                   minusc+=1
           i+=1
        
        if addc >= 7*minusc or minusc >= 7*addc : # 2.5 ？ 有待测试确定
            while mark < site and X[mark] >= 0 :
                X[mark]=-0.01
                Y[mark]=Y1[mark]=0
                mark+=1
        
        addc=0 #重新赋值
        minusc=0
        mark=site
        

    #找出值最大部分的最大差值对应的位置
    val=np.zeros(site)
    val1=np.zeros(site)
    count=np.zeros(site)
    maxsite=np.zeros(site)
    i=0
    site1=0
    maxheight=-1
    while i < site :
        while i < site and X[i] < 0 :
            i+=1
        if i >= site :
            break
        while i < site and X[i] >= 0 :
            delta_h=Y1[i]#-Y[i]
            if maxheight < delta_h :
               maxheight=delta_h
               maxsite[site1]=i
            val1[site1]+=Y1[i]
            val[site1]+=Y[i]
            count[site1]+=1
            i+=1
        site1+=1
        maxheight=-1

    mx=0
    ms=-1
    mis=-1
    mi=2147483647
    zflag=False #前面没有正着超过阈值的情况，可取delta_v < 0 and abs(delta_v)>thdf的距离
    for i in range(site1):
        delta_v=val1[i]-val[i]
        if delta_v > thdz:
            CandidateD[CDcount]=(X[int(maxsite[i])]+rid)/48000*340/2 #作为候选
            CDcount+=1
            zflag=True
        elif delta_v < 0 and abs(delta_v)>thdf and zflag == False:
            CandidateD[CDcount]=(X[int(maxsite[i])]+rid)/48000*340/2-0.2
            CDcount+=1
        if mx<delta_v:
            mx=delta_v
            ms=i
        if delta_v<mi:
            mi=delta_v
            mis=i
            
    CandidateD[CDcount]=-1
    CDcount+=1
    return ms,mis,mx,mi,maxsite,X


def forEveryMic(PATH1, PATH2, mics):
    global MicD, CandidateD
    global CDcount,thdz, thdf
    
    MicD=np.zeros(6)
    CDcount=0
    CandidateD=np.zeros(600)#只取最后一次比较的数据

    count = 0
    for micnum in mics:
        ms,mis,mx,mi, maxsite,X=process(PATH1,PATH2,micnum)
        if mx < thdz and (abs(mi) < thdf or mi==2147483647): # 阈值的设定？ empty    有待检验
            count+=1
        else:
            if mx >= thdz:
                MicD[micnum-1]=(X[int(maxsite[ms])]+rid)/48000*340/2
            elif abs(mi) >= thdf and mi!=2147483647:
                MicD[micnum-1]=(X[int(maxsite[mis])]+rid)/48000*340/2-0.2 #厚度至少为20cm
    #plt.show()
    return count

def record(PATH, choice):
    if not os.path.exists(PATH): 
        os.makedirs(PATH)
    if choice==0:
        os.system('sh runforDetect.sh '+PATH+' '+'0 0')
    else:
        os.system('sh runforDetect.sh '+PATH+' '+'2 1')
    time.sleep(7)

def calculateD():
    global MicD
    MicD1=MicD.copy()
    MicD1.sort()
    i=0
    while MicD1[i]==0:
        i+=1
    i+=1
    sumD=0
    numD=0
    while i < MicD1.size-1:
        sumD+=MicD1[i]
        numD+=1
        i+=1
    distance=sumD/numD
    return distance


figureno=0

# Main
thdz = 15
thdf = 20
cSlice = 705      # 2.5 m
rid = 70           # no obstacles in 25 cm 
mics=[1,3,4,5,6]

MicD=np.zeros(6)
CDcount=0
CandidateD=np.zeros(600)# temporary

PATH1='empty'#input("empty:")
PATH2='barrier'#input("barrier:")
record(PATH2, 0)

count = forEveryMic(PATH1, PATH2, mics)
postfix = 1
count1 = 0
if count < 3:
    #print(PATH2)
    time.sleep(5)
    while count < 4 and count1 < 3:
        record(PATH2, 0)
        PATH3='barrier'+str(postfix)
        record(PATH3, 0)
        count = forEveryMic(PATH2, PATH3, mics)
        count1 = forEveryMic(PATH1, PATH3, mics)
        PATH2=PATH3
        postfix+=1
    
if postfix > 1:
    count = count1
#print(count)
if count >= 3:
    print('empty')
    if count >=4 :
        for i in range(1,7):
            os.remove(''.join(['empty/mic',str(i),'.wav']))
            shutil.copyfile(''.join([PATH2,'/mic',str(i),'.wav']),''.join(['empty/mic',str(i),'.wav']))
else:
    angle=1
    distance_p=calculateD()
    
    CDcount=0
    MicD=np.zeros(6)
    for micnum in mics:
        delta_d=2147483647
        while CandidateD[CDcount]>0:
            v=abs(CandidateD[CDcount]-distance_p)
            if v < delta_d:
                delta_d=v
                MicD[micnum-1]=CandidateD[CDcount]
            CDcount+=1
        CDcount+=1
        
    distance=calculateD()
    while abs(distance-distance_p)>0.1:
        CDcount=0
        MicD=np.zeros(6)
        for micnum in mics:
            delta_d=2147483647
            while CandidateD[CDcount]>0:
                v=abs(CandidateD[CDcount]-distance)
                if v < delta_d:
                    delta_d=v
                    MicD[micnum-1]=CandidateD[CDcount]
                CDcount+=1
            CDcount+=1
        distance_p=distance
        distance=calculateD()
    ''' 
    delta_v=float("%.2f" % (MicD[0]-MicD[4]))
    if delta_v > 0.07:
        angle=0
    elif -delta_v > 0.07:
        angle=2
    '''
    delta_v=float("%.2f" % (MicD[3]-MicD[4]))
    if MicD[3]==0 or (delta_v >=0.2 and MicD[4]!=0) :
        angle=2
        if MicD[4]==0 or MicD[5]==0:
            distance=max(MicD[4],MicD[5])
        else:
            distance=min(MicD[4],MicD[5])
    if MicD[4]==0 or (-delta_v >=0.2 and MicD[3]!=0):
        angle=0
        if MicD[2]==0 or MicD[3]==0:
            distance=max(MicD[2],MicD[3])
        else:
            distance=min(MicD[2],MicD[3])
    if abs(delta_v)<0.2:
        angle=1
    
    distance= ("%.2f" % distance)
    outcome='nonempty,'+str(angle)+','+distance+'m'
    #print('distance2:', distance)
    print(outcome)
#plt.show()
