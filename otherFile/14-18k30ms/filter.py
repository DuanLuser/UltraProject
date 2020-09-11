import os
import wave
import numpy as np
import matplotlib.pyplot as plt

from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate

from tkinter import *
from tkinter import messagebox

from scipy import fftpack


def FilterBandpass(wave, fs, low, high):
    ''' 应用带通滤波器 '''
    l = low/(fs/2)
    h = high/(fs/2)
    b, a = signal.butter(5, [l, h], 'bandpass')  # 配置滤波器 8 表示滤波器的阶数
    return signal.filtfilt(b, a, wave)  # data为要过滤的信号


def averageNormalization(corr):
    global cSlice
    distance=25440     #0.53s   48kHz
    peaks=[]
    i=10000
    first=1
    while i+distance < corr.size:
        site=np.argmax(corr[i:i+distance])+i
        if corr[site] > 50000 :
            if first >= 2:
                peaks.append(site)
            else: first+=1
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


def process(PATH1, PATH2, micnum, figureno, order):
    global cSlice

    low = 14000
    high = 18000
    time = 30/1000 # 30ms
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
    aNcorr = averageNormalization(corr)
    aNcorr1 = averageNormalization(corr1)

    #获取极值点    
    x=signal.argrelextrema(aNcorr, np.greater)[0]
    y=aNcorr[x]
    x1=signal.argrelextrema(aNcorr1, np.greater)[0]
    y1=aNcorr1[x1]
    
    if x.size <=0 or x1.size <= 0:
        return 0,0,0,x

    x_min=max(x[0],x1[0])
    x_max=min(x[x.size-1],x1[x1.size-1])
    
    #统一坐标轴，插值平滑
    x_new = np.linspace(x_min,x_max,cSlice*2) #!!!cSlice的大小会影响每个区域点的个数
    func=interpolate.interp1d(x,y, kind="cubic")
    y_smooth=func(x_new)
    func1=interpolate.interp1d(x1,y1, kind="cubic")
    y_smooth1=func1(x_new)


    if order == 0:
        plt.figure(figureno+1)
        label=['Empty','The other']
        #plt.plot(x,y,'o')
        plt.plot(x_new, y_smooth,linewidth=1)
        #plt.plot(x1,y1,'*')
        plt.plot(x_new, y_smooth1,c='red',linewidth=1)
        plt.legend(label, loc =0) 
        plt.title(''.join(['mic',str(micnum)]))
        plt.xlabel('Sampling point')
        plt.ylabel('Correlation')
    

    #提取图2(The Other)中高于图1(Empty)的所有点
    X=np.zeros(cSlice*2)
    Y=np.zeros(cSlice*2)
    Y1=np.zeros(cSlice*2)
    i=0
    while i < cSlice*2:
        while i < cSlice*2 and y_smooth1[i] > y_smooth[i] :
            X[i]=x_new[i]
            Y[i]=y_smooth[i]
            Y1[i]=y_smooth1[i]
            if i-2 > 0 and Y1[i-2] > Y1[i-1] and Y1[i] > Y1[i-1] :
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
        
    
    # 去除了不对成的峰--重点
    if order == 0 :
        plt.figure(figureno+2)
        label=['Empty','The other']
        plt.plot(X,Y,'.')
        plt.plot(X,Y1,'.',c='red')
        plt.legend(label, loc =0) 
        plt.title(''.join(['Minus',str(micnum)]))
        plt.xlim(0, cSlice)
        plt.ylim(0, 1)
        plt.xlabel('Sampling point')
        plt.ylabel('Correlation')


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
            delta_h=Y1[i]-Y[i]
            if maxheight < delta_h :
               maxheight=delta_h
               maxsite[site1]=i
            val1[site1]+=Y1[i]
            val[site1]+=Y[i]
            count[site1]+=1
            i+=1
        site1+=1
        maxheight=-1

    #判断相似
    msite=np.zeros(site1)
    misite=np.zeros((site1,10))
    msite1=np.zeros(site1)
    similar=np.zeros(site1)
    i=0
    site1=0
    while i < site :
        while i < site and X[i] < 0 :
            i+=1
        if i >= site :
            break
        num=0
        num1=0
        isite=i
        while i < site and X[i] >= 0 :
            if i-2 > 0 and X[i-2] > 0 and X[i-1] > 0:
                if Y1[i-2] < Y1[i-1] and Y1[i] < Y1[i-1] :
                    msite1[site1]=X[i-1]
                if Y[i-2] < Y[i-1] and Y[i] < Y[i-1] :
                    msite[site1]=X[i-1]
                    num+=1
                if Y[i-2] > Y[i-1] and Y[i] > Y[i-1] :
                    misite[site1][num1]=X[i-1]
                    num1+=1
            if num >= 2 :
                while i+1 < site and X[i+1] >= 0 : i+=1
                
            i+=1
        if num < 2 and np.abs(msite1[site1]-msite[site1]) <= 8:
            similar[site1]=1
            
        if num == 1 :
            if misite[site1][0]!=0 and misite[site1][1]!=0:
                if misite[site1][0]-X[isite] >8 or X[i-1]-misite[site1][1] >8 :
                    similar[site1]=0
            elif misite[site1][0]!=0 :
                if misite[site1][0]-X[isite] >8 and X[i-1]-misite[site1][0] >8 :
                    similar[site1]=0
        site1+=1


    mx=0
    ms=-1
    for i in range(site1):
        delta_v=val1[i]-val[i]
        if similar[i] == 1:
            print('%d: %f %f %f'%(i, delta_v, delta_v*0.65, delta_v/count[i]))
            delta_v*=0.65
        else :
            print('%d: %f %f'%(i, delta_v, delta_v/count[i]))
        if mx<delta_v:
            mx=delta_v
            ms=i

    return ms,mx,maxsite,X


PATH1=input("empty:")
PATH2=input("barrier:")
if not os.path.exists(PATH2):
    os.makedirs(PATH2)

os.system('sh runforDetect.sh '+PATH2)
time.sleep(7)


cSlice=1300
mics=[1,2,3,4,5,6]
fugureno = 1
for micnum in mics:
    print('mic:%d'%micnum)
    ms,mx,maxsite,X=process(PATH1,PATH2,micnum,fugureno,0)
    fugureno += 4
    ms1,mx1,maxsite1,X1=process(PATH2,PATH1,micnum,fugureno,1)

    root=Tk()
    root.withdraw()
    if mx < 4 and mx1 < 6: # 阈值的设定？     有待检验
        print('None!')
        messagebox.showinfo('提示信息','目标范围内没有新增障碍物！')
    else:
        print('Distance: %fm '%(X[int(maxsite[ms])]/48000*340/2))
        messagebox.showinfo('提示信息','目标范围内有新增障碍物，在前方 %.2fm 以内'%(X[int(maxsite[ms])]/48000*340/2))
plt.show()
