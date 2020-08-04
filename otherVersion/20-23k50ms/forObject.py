import os
import sys
import wave
import time
import numpy as np

from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate

from scipy import fftpack


def FilterBandpass(wave, fs, low, high):
    ''' 应用带通滤波器 '''
    l = low/(fs/2)
    h = high/(fs/2)
    b, a = signal.butter(8, [l, h], 'bandpass')  # 配置滤波器 8 表示滤波器的阶数
    return signal.filtfilt(b, a, wave)  # data为要过滤的信号


def averageNormalization(corr):
    global cSlice
    
    distance=22491
    #peaks, _ = signal.find_peaks(corr, height=1000, distance=22491)  # 寻找整个序列的峰值
    peaks=[]
    i=10000
    while i+distance < corr.size:
        site=np.argmax(corr[i:i+distance])+i
        if corr[site] > 1000:
            peaks.append(site)
        i+=distance
    
    cycles = []
    for p in peaks:
        c = {}
        c["PeakIndex"] = p
        c["PeakHeight"] = corr[p]
        c["Corr"] = np.abs(corr[p:p+cSlice])
        #c["NormalizedCorr"] =((c["Corr"]-np.min(c["Corr"]))/np.max(c["Corr"]))
        cycles.append(c)

    count=0
    out = np.zeros(cSlice)
    for i in range(len(cycles)):
        if len(cycles[i]['Corr'])!=cSlice:
            count+=1
        else:
            out += cycles[i]['Corr']
    length = len(cycles)-count
    out = out/length  # 平均
    #print('min=%f, max=%f'%(np.min(out),np.max(out)))
    out = (out-np.min(out))/np.max(out) # 归一化
    return out


def process(PATH1, PATH2, micnum):
    global cSlice

    low = 18000
    high = 20000
    time = 10/1000 # 10ms
    rate = 44100

    filename1 = f'{PATH1}/mic{micnum}.wav'
    filename2 = f'{PATH2}/mic{micnum}.wav'

    t = np.arange(0, time,1/rate)
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
    aNcorr = averageNormalization(corr)
    aNcorr1 = averageNormalization(corr1)
    
    #获取极值点    
    x=signal.argrelextrema(aNcorr, np.greater)[0]
    y=aNcorr[x]
    x1=signal.argrelextrema(aNcorr1, np.greater)[0]
    y1=aNcorr1[x1]

    if x.size<=0 or x1.size<=0: sys.exit(0)  #error
    x_min=max(x[0],x1[0])
    x_max=min(x[x.size-1],x1[x1.size-1])
    
    #统一坐标轴，插值平滑
    x_new = np.linspace(x_min,x_max,cSlice*2) #!!!cSlice的大小会影响每个区域点的个数
    func=interpolate.interp1d(x,y, kind="cubic")
    y_smooth=func(x_new)
    func1=interpolate.interp1d(x1,y1, kind="cubic")
    y_smooth1=func1(x_new)

    #提取图2(The Other)中高于图1(Empty)的所有点
    X=np.zeros(cSlice*2)
    Y=np.zeros(cSlice*2)
    Y1=np.zeros(cSlice*2)
    i=0
    site=0
    while i < cSlice*2:
        while i<cSlice*2 and y_smooth1[i]>y_smooth[i] :
            X[site]=x_new[i]
            Y[site]=y_smooth[i]
            Y1[site]=y_smooth1[i]
            site+=1
            i+=1
        if i==cSlice*2: break
        X[site]=-0.01
        Y[site]=Y1[site]=0
        site+=1
        i+=1
   
    
    # 去除不对称的峰
    i=0
    addc=0
    minusc=0
    mark=site
    while i < site:
        while i < site and X[i] < 0:
           i+=1
        if i >= site:
           break

        mark=i
        while i < site and X[i] >= 0:
           if i+1<site and X[i+1]>=0:
               if Y1[i+1]>Y1[i]:
                   addc+=1
               if Y1[i+1]<Y1[i]:
                   minusc+=1
           i+=1

        t1=mark
        t2=i-1
        if (addc>=3.5*minusc or minusc>=3.5*addc): # 2.5 ？ 有待测试确定
            while mark<site and X[mark]>=0:
                X[mark]=-0.01
                Y[mark]=Y1[mark]=0
                mark+=1
        
        '''
        #去除两端,如何优化
        t_1=t1
        t_2=t2
        while (t1<site and X[t1]>=0) and (t1+1<site and X[t1+1]>=0) and (Y1[t1+1]<=Y1[t1]):#情况1，左侧一开始就下降
            X[t1]=-0.01
            Y[t1]=Y1[t1]=0;
            t1+=1

        mark1=t_1#情况2，上升部分没有下降部分多，只看一上一下两端
        addc1=0
        minusc1=0
        while (t_1<site and X[t_1]>=0) and (t_1+1<site and X[t_1+1]>=0) and (Y1[t_1+1]>=Y1[t_1]):
            addc1+=1
            t_1+=1
        while (t_1<site and X[t_1]>=0) and (t_1+1<site and X[t_1+1]>=0) and (Y1[t_1+1]<=Y1[t_1]):
            minusc1+=1
            t_1+=1
        if  minusc1>=2.5*addc1: # 2.5 ？ 有待测试确定
            while mark1<=t_1 and X[mark1]>=0:
                X[mark1]=-0.01
                Y[mark1]=Y1[mark1]=0
                mark1+=1

        while (t2>0 and X[t2]>=0) and (t2-1>0 and X[t2-1]>=0) and (Y1[t2-1]<=Y1[t2]):#情况3，从右到左，右侧一开始就下降
            X[t2]=-0.01
            Y[t2]=Y1[t2]=0
            t2-=1
        if X[t2-1]<0:
            X[t2]=-0.01
            Y[t2]=Y1[t2]=0
            t2-=1

        mark1=t_2#情况4，从右到左，上升部分没有下降部分多，只看一上一下两端
        addc1=0
        minusc1=0
        while (t_2>0 and X[t_2]>=0) and (t_2-1>0 and X[t_2-1]>=0) and (Y1[t_2-1]>=Y1[t_2]):
            addc1+=1
            t_2-=1
        while (t_2>0 and X[t_2]>=0) and (t_2-1>0 and X[t_2-1]>=0) and (Y1[t_2-1]<=Y1[t_2]):
            minusc1+=1
            t_2-=1
        if  minusc1>=2.5*addc1: # 2.5 ？ 有待测试确定
            while mark1>=t_2 and X[mark1]>=0:
                X[mark1]=-0.01
                Y[mark1]=Y1[mark1]=0
                mark1-=1
        '''

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
    while i < site:
        while i < site and X[i] < 0:
            i+=1
        if i >= site:
            break
        while i < site and X[i] >= 0:
            delta_h=Y1[i]-Y[i]
            if maxheight<delta_h:
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
    for i in range(site1):
        print('%d: %f  %f'%(i,(val1[i]-val[i]),(val1[i]-val[i])/count[i]))
        delta_v=val1[i]-val[i]
        if mx<delta_v:
            mx=delta_v
            ms=i

    return ms,mx,maxsite,X


PATH1='empty'
PATH2='barrier'

os.system('sh runforDetect.sh '+PATH2)
time.sleep(7)

cSlice=1000#int(sys.argv[1])

mics=[1]
for micnum in mics:
    
    ms,mx,maxsite,X=process(PATH1,PATH2,micnum)
    ms1,mx1,maxsite1,X1=process(PATH2,PATH1,micnum)

    if mx < 3 and mx1 < 4: # 阈值的设定？     有待检验
        print('None!')
    else:
        print('Distance: %fm '%(X[int(maxsite[ms])]/44100*340/2))

