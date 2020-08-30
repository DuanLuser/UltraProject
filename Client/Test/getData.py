import os
import wave
import numpy as np
import matplotlib.pyplot as plt

from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate
from multiprocessing import Pool

from scipy import fftpack
import shutil
import datetime
import math

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import mpl_toolkits.mplot3d

from playRec import TdmaPlay


def FilterBandpass(wave, fs, low, high):
    ''' 应用带通滤波器 '''
    l = low/(fs/2)
    h = high/(fs/2)
    b, a = signal.butter(4, [l, h], 'bandpass')  # 配置滤波器 8 表示滤波器的阶数
    return signal.filtfilt(b, a, wave)  # data为要过滤的信号


def averageNormalization(micnum,corr):
    '''多个周期取平均'''
    global cSlice, rid
    distance=4851
    #peaks, _ = signal.find_peaks(corr, height=1000, distance=24480)  # 寻找整个序列的峰值
    peaks=[]
    peaks1=[]
    i=22500
    first=1
    while i+distance < corr.size:
        site=np.argmax(corr[i:i+distance])+i
        if corr[site] > 20000 :
            if first % 2 :
                peaks.append(site)
                print(i,"=",micnum,"-",site)
            else:
                peaks1.append(site)
                print(i,"-",micnum,"-",site)
        first+=1
        i+=distance
    
    cycles = []
    cycles1= []
    print(micnum,len(peaks))
    print(micnum, len(peaks1))
    for p in peaks:
        c = {}
        c["PeakIndex"] = p
        c["PeakHeight"] = corr[p]
        c["Corr"] = np.abs(corr[p+rid:p+cSlice])
        cycles.append(c)
        
    for p in peaks1:
        c = {}
        c["PeakIndex"] = p
        c["PeakHeight"] = corr[p]
        c["Corr"] = np.abs(corr[p+rid:p+cSlice])
        cycles1.append(c)

    count=0
    out = np.zeros(cSlice-rid)
    for i in range(len(cycles)):
        if len(cycles[i]['Corr'])!=(cSlice-rid):
            count+=1
        else:
            out += cycles[i]['Corr']
    length = len(cycles)-count
    out = out/length  # 平均
    
    count1=0
    out1 = np.zeros(cSlice-rid)
    for i in range(len(cycles1)):
        if len(cycles1[i]['Corr'])!=(cSlice-rid):
            count1+=1
        else:
            out1 += cycles1[i]['Corr']
    length1 = len(cycles1)-count1
    out1 = out1/length1  # 平均
    return out, out1

def afterAN(Ncorr,Ncorr1, micnum):
    
    global cSlice, rid, thdz, thdf, figureno
    rate = 44100
    
    aNcorr = Ncorr/300000            #经验值
    aNcorr1 = Ncorr1/300000

    #获取极值点    
    x=signal.argrelextrema(aNcorr, np.greater)[0]
    y=aNcorr[x]
    x1=signal.argrelextrema(aNcorr1, np.greater)[0]
    y1=aNcorr1[x1]

    #for safety
    if x.size <=0 or x1.size <= 0:
        return micnum,0,0
    
    #统一坐标轴，插值平滑
    x_min=max(x[0],x1[0])
    x_max=min(x[x.size-1],x1[x1.size-1])
    x_new = np.linspace(x_min,x_max,cSlice*2) #!!!cSlice的大小会影响每个区域点的个数
    func=interpolate.interp1d(x,y, kind="cubic")
    y_smooth=func(x_new)
    func1=interpolate.interp1d(x1,y1, kind="cubic")
    y_smooth1=func1(x_new)
    
    if True:

        figureno+=1
        plt.figure(figureno)
        label=['Empty','The other']
        #plt.plot(x,y,'o')
        plt.ylim(0,1)
        plt.plot((x_new+rid)/rate*340/2, y_smooth,linewidth=1)
        #plt.plot(x1,y1,'*')
        plt.plot((x_new+rid)/rate*340/2, y_smooth1,c='red',linewidth=1)
        plt.legend(label, loc =0) 
        plt.title(''.join(['mic',str(micnum)]))
        #plt.title('Comparison')
        #plt.title('Envelope Detection')
        plt.xlabel('Distance(m)')
        plt.ylabel('Correlation')
            
        plt.show()
    

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
            if i-2 > 0 and Y1[i-2] > Y1[i-1] and Y1[i] > Y1[i-1] :#断开每个峰值
                X[i-1]=-0.01
                Y[i-1]=Y1[i-1]=0
            if i-1 > 0 and (Y1[i]-Y[i])*(Y1[i-1]-Y[i-1])<0:#断开当前信号与背景信号交叉处
                X[i-1]=-0.01
                Y[i-1]=Y1[i-1]=0
            i+=1
        if i == cSlice*2 : break
        
        X[i]=-0.01
        Y[i]=Y1[i]=0
        i+=1

    site=cSlice*2  # site=i
    # 去除不对称的峰, 启发式;
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
        
        if addc >= 7*minusc or minusc >= 7*addc : # 7？ 有待测试确定
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
    snum=0
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
               maxsite[snum]=i
            val1[snum]+=Y1[i]
            val[snum]+=Y[i]
            count[snum]+=1
            i+=1
        snum+=1
        maxheight=-1

    mx=0
    mxs=-1
    mis=-1
    mi=2147483647
    zflag=False #前面没有正着超过阈值的情况，可取delta_v < 0 and abs(delta_v)>thdf的距离
    print('mic:%d'%micnum)
    for i in range(snum):
        #print(val[i])
        delta_v=val1[i]-val[i]
        maxD=(X[int(maxsite[i])]+rid)/rate*340/2
        miD=(X[int(maxsite[i])]+rid)/rate*340/2-0.
        delta_v=delta_v*math.e**(0.2*maxD)#maxD*maxD
        #else:
        #    delta_v=delta_v*math.e**(0.4*maxD)#maxD*maxD
        if delta_v > thdz:
            print('%.2fm %.4f %.4f'%(maxD,delta_v, delta_v/count[i]))
            zflag=True
        elif delta_v < 0 and abs(delta_v)>thdf and zflag == False:
            print('%.2fm %.4f %.4f'%(miD,delta_v, delta_v/count[i]))
        else:
            print('%.2fm %.4f %.4f'%(maxD,delta_v, delta_v/count[i]))
        if mx<delta_v:
            mx=delta_v
            mxs=i
        if delta_v<mi:
            mi=delta_v
            mis=i
    if mi >0:
        mi=0
    

    return micnum,mx,mi


def process(micInfo):
    '''处理音频，获得差异值(位于背景信号之上/之下)'''
    
    global figureno
    
    PATH1 = micInfo[0]
    PATH2 = micInfo[1]
    micnum = micInfo[2]
    
    low = 18000
    high = 22000
    time = 10/1000 # 10ms
    rate = 44100

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
    '''
    if True:
        figureno+=1
        plt.figure(figureno)
        plt.plot(fliter_y)
        plt.plot(fliter_y1)
        plt.title(str(micnum))
    '''
    # 互相关
    corr = np.abs(np.correlate(fliter_y, chirp, mode='full'))
    corr1 = np.abs(np.correlate(fliter_y1, chirp, mode='full'))
    
    if True:
        figureno+=1
        plt.figure(figureno)
        plt.plot(corr)
        plt.plot(corr1)
        plt.title(str(micnum))
    
    # 平均 and 归一化
    Ncorr, Ncorr_1= averageNormalization(micnum,corr)
    Ncorr1, Ncorr1_1 = averageNormalization(micnum,corr1)
    plt.show()
    micnum,mx,mi = afterAN(Ncorr,Ncorr1, micnum)
    
    micnum,mx,mi = afterAN(Ncorr_1,Ncorr1_1, micnum)
    
    return micnum,mx,mi
    


def forEveryMic(PATH1, PATH2, mics):
    '''对每个mic收集的数据进行process处理，并行'''
    global thdz, thdf, file
    count = 0
    micInfo=[]
    
    '''
    for micnum in mics:
        print('mic:%d'%micnum)
        mx,mi=process(PATH1,PATH2,micnum)
        if mx < thdz and (abs(mi) < thdf or mi==2147483647): # 阈值的设定？ empty    有待检验
            count+=1
    '''
    for micnum in mics:
        micInfo.append((PATH1, PATH2, micnum))
    with Pool(len(micInfo)) as p:
        result=p.map(process, micInfo)
    #result=process(micInfo[3])
    
    file.writelines('<<<<<<<<\n')
    for i in range(len(result)):
        file.writelines(str(result[i][0])+'---')
        file.writelines('mx:'+('%.2f'%result[i][1])+',mi:-'+('%.2f'%abs(result[i][2]))+'\n')
        if result[i][1] <= thdz and (abs(result[i][2]) <= thdf or result[i][2]==2147483647): # 阈值的设定？ empty    有待检验
            count+=1
    #print(count)
    #plt.show()
    return count


def RecordAudio(PATH, choice):
    '''采集音频数据'''
    global tplay
    
    if not os.path.exists(PATH): 
        os.makedirs(PATH)
    
    out = tplay.play_and_record(PATH,3)
    print(out)
    #recordFile.recordWAV(PATH)

def main():
    
    global figureno, thdz, thdf, cSlice, rid, file, tplay
    file=open('Data/Data.txt',mode='a+')
    file.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n')
    tplay=TdmaPlay()
    
    figureno=0

    thdz = 4           # 5.5 
    thdf = 5          # 6.5
    cSlice = 2117       # 2.5m; 847: 3 m; 988: 3.5m
    rid = 1           # no obstacles in 1m;//25 cm 
    mics=[1,3,4,5,6] #4

    PATH1='Empty'#input("empty:")
    PATH2='Barrier/barrier'#input("barrier:")
    RecordAudio(PATH2, 0)
    count = forEveryMic(PATH1, PATH2, mics)
    postfix = 1
    count1 = 0
    stability_count=0
    if count < 3: # 3
        time.sleep(4)
        # 判断环境是否稳定
        RecordAudio(PATH2, 0)
        while stability_count < 2:
            PATH3='Barrier/barrier'+str(postfix)
            RecordAudio(PATH3, 0)
            count = forEveryMic(PATH2, PATH3, mics)
            if (stability_count==0 and count < 3) or (stability_count==1 and count < 3): #5
                stability_count = 0
            PATH2=PATH3
            postfix+=1
            stability_count+=1
        count = forEveryMic(PATH1, PATH2, mics)
    
    outcome=''
    if count >= 3: # 3
        outcome='empty'
        #if count >=5 :
        #    for i in range(1,7):
        #        os.remove(''.join(['empty/mic',str(i),'.wav']))
        #        shutil.copyfile(''.join([PATH2,'/mic',str(i),'.wav']),''.join(['empty/mic',str(i),'.wav']))
    else:
        outcome='nonempty'
        #plt.show()
        path_images='images/'+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        empty_path=path_images+'-empty'
        barrier_path=path_images+'-barrier'
        if not os.path.exists(empty_path): 
            os.makedirs(empty_path)
        if not os.path.exists(barrier_path): 
            os.makedirs(barrier_path)
        
        for i in range(1,7):
            shutil.copyfile(''.join([PATH1,'/mic',str(i),'.wav']),''.join([empty_path, '/mic',str(i),'.wav']))
            shutil.copyfile(''.join([PATH2,'/mic',str(i),'.wav']),''.join([barrier_path, '/mic',str(i),'.wav']))
        #outcome='empty'
    file.writelines(outcome+'\n')
    file.close()
    print(outcome)
    #time.sleep(2)

        
    return outcome

if __name__ == "__main__":
    sys.exit(main())