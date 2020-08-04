import os
import wave
import shutil
import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate
from multiprocessing import Pool
from scipy import fftpack
from threading import Thread, Event

import logging
import logzero

import warnings
warnings.filterwarnings("ignore")

logger = logzero.setup_logger("client", level=logging.INFO)


class URadar:
    '''封装类'''
    thdz: int               #7.5           # 5.5 
    thdf: int               #8.5           # 6.5
    cSlice: int             #988       # 3.5 m
    rid: int                #70           # no obstacles in 25 cm 
    outcome: str

    figureno=0
    mics=[1,3,4,5,6]
    stability_count=2
    process_result=[]
    nor_val=200000           #经验值
    reset_order=False
    
    _PATH1='Empty'
    _PATH2='Barrier/barrier'


    def __init__(self, thdz=7.5, thdf=8.5, cSlice=988, rid=70) -> None:
        self.thdz=thdz
        self.thdf=thdf
        self.cSlice=cSlice
        self.rid=rid

    def reset(self):
        logger.info("正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
        out = os.popen('sh runforDetect.sh '+self._PATH1 +' 0 0').read().replace('\n', '')# 0 0
        if out=="OK":
            logger.info("重置成功！")
        else:
            logger.info("重置失败！")
        return out
    
    def FilterBandpass(self, wave, fs, low, high):
        ''' 应用带通滤波器 '''
        l = low/(fs/2)
        h = high/(fs/2)
        b, a = signal.butter(8, [l, h], 'bandpass')  # 配置滤波器 8 表示滤波器的阶数
        return signal.filtfilt(b, a, wave)  # data为要过滤的信号

    def averageNormalization(self, corr):
        '''多个周期取平均'''
        distance=24480              # t=051s;  rate=48000
        #peaks, _ = signal.find_peaks(corr, height=1000, distance=24480)  # 寻找整个序列的峰值
        peaks=[]
        i=1000
        first=1
        while i+distance < corr.size:
            site=np.argmax(corr[i:i+distance])+i
            if corr[site] > 100 :
                if first >= 2:
                    peaks.append(site)
                else: first+=1
            i+=distance
    
        cycles = []
        #print(len(peaks))
        for p in peaks:
            c = {}
            c[("PeakIndex")] = p
            c[("PeakHeight")] = corr[p]
            c[("Corr")] = np.abs(corr[p+self.rid:p+self.cSlice])
            cycles.append(c)

        count=0
        out = np.zeros(self.cSlice-self.rid)
        for i in range(len(cycles)):
            if len(cycles[i][('Corr')])!=(self.cSlice-self.rid):
                count+=1
            else:
                out += cycles[i][('Corr')]
        length = len(cycles)-count
        out = out/length  # 平均
        return out, np.max(out)

    def process(self, PATH1, PATH2, micnum):
        '''处理音频，获得差异值(位于背景信号之上/之下)'''
        
        low = 18000
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
        fliter_y = self.FilterBandpass(y, Fs, low, high)
        fliter_y1 = self.FilterBandpass(y1, Fs1, low, high)

        # 互相关
        corr = np.correlate(fliter_y, chirp, mode='full')
        corr1 = np.correlate(fliter_y1, chirp, mode='full')
    
        # 平均 and 归一化
        Ncorr, maxv = self.averageNormalization(corr)
        Ncorr1, maxv1 = self.averageNormalization(corr1)
        aNcorr = Ncorr/self.nor_val            
        aNcorr1 = Ncorr1/self.nor_val

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
        x_new = np.linspace(x_min,x_max,self.cSlice*2) #!!!cSlice的大小会影响每个区域点的个数
        func=interpolate.interp1d(x,y, kind="cubic")
        y_smooth=func(x_new)
        func1=interpolate.interp1d(x1,y1, kind="cubic")
        y_smooth1=func1(x_new)


        #提取图2(The Other)中高于/低于图1(Empty)的所有点
        X=np.zeros(self.cSlice*2)
        Y=np.zeros(self.cSlice*2)
        Y1=np.zeros(self.cSlice*2)
        i=0
        while i < self.cSlice*2:
            while i < self.cSlice*2 and y_smooth1[i] != y_smooth[i] :
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
            if i == self.cSlice*2 : break
        
            X[i]=-0.01
            Y[i]=Y1[i]=0
            i+=1

        site=self.cSlice*2  # site=i
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
        
            if addc >= 10*minusc or minusc >= 10*addc : # 7？ 有待测试确定
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
        #print('mic:%d'%micnum)
        for i in range(snum):
            delta_v=val1[i]-val[i]
            if delta_v > self.thdz:
                #print('%d: %f %f %fm'%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self.rid)/rate*340/2))
                zflag=True
            #elif delta_v < 0 and abs(delta_v)>self.thdf and zflag == False:
                #print('%d: %f %f %fm'%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self.rid)/rate*340/2-0.2))
            #else:
                #print('%d: %f %f %fm'%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self.rid)/rate*340/2)) 
            if mx<delta_v:
                mx=delta_v
                mxs=i
            if delta_v<mi:
                mi=delta_v
                mis=i
        if mi >0:
            mi=0
        
        self.process_result.append((micnum,mx,mi))
        return micnum,mx,mi


    def forEveryMic(self, PATH1, PATH2, mics):
        '''对每个mic收集的数据进行process处理，并行'''
        count = 0
        Threads=[]
        for micnum in mics:
            t = Thread(target=self.process, args=(PATH1, PATH2, micnum,))
            t.start()
            Threads.append(t)
        for t in Threads:
            t.join()
        result=self.process_result
        for i in range(len(result)):
            if result[i][1] <= self.thdz and (abs(result[i][2]) <= self.thdf or result[i][2]==2147483647): # 阈值的设定？ empty    有待检验
                count+=1
        self.process_result.clear()
        return count


    def RecordAudio(self, PATH, choice):
        '''采集音频数据'''
        if not os.path.exists(PATH): 
            os.makedirs(PATH)
        out=''
        if self.reset_order == True:
            self.reset()
            self.reset_order=False
            
        if choice==0:
            out = os.popen('sh runforDetect.sh '+PATH+' '+'0 0').read().replace('\n', '')#0,0
        else:
            out = os.popen('sh runforDetect.sh '+PATH+' '+'2 1').read().replace('\n', '')
        print(out)
        #recordFile.recordWAV(PATH)

    def detect(self):
    
        self.RecordAudio(self._PATH2, 0)
        count = self.forEveryMic(self._PATH1, self._PATH2, self.mics)
        if count < 5: # 3
            time.sleep(4)
            # 判断环境是否稳定
            scount=0
            postfix = 1
            PATH2=self._PATH2
            self.RecordAudio(PATH2, 0)
            while scount < self.stability_count:
                PATH3=self._PATH2+str(postfix)
                self.RecordAudio(PATH3, 0)
                count = self.forEveryMic(PATH2, PATH3, self.mics)
                if (scount==0 and count < 4) or (scount==1 and count < 4): #5
                    scount = 0
                PATH2=PATH3
                postfix+=1
                scount+=1
            count = self.forEveryMic(self._PATH1, PATH2, self.mics)
    
        if count >= 5: # 3
            self.outcome='empty'
            #if count >=5 :
            #    for i in range(1,7):
            #        os.remove(''.join(['empty/mic',str(i),'.wav']))
            #        shutil.copyfile(''.join([PATH2,'/mic',str(i),'.wav']),''.join(['empty/mic',str(i),'.wav']))
        else:
            self.outcome='nonempty'
            #self.outcome='empty'
        print(self.outcome)
        logger.info(f"检测结果：{self.outcome}")
        time.sleep(1)
        return self.outcome
    

if __name__ == "__main__":
    # 启动通讯客户端
    # ws = WebsocketClient()
    # ws.server_url = "ws://localhost:2714"
    # ws.device_id = "2"
    # ws.Start()

    Radar=URadar(None)
    reset_choice=input('reset_or_not:')
    if reset_choice=='1':
        Radar.reset()
    while True:
        Radar.detect()