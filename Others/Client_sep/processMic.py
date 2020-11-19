# -*- encoding: utf-8 -*-
'''
@File    :   processMic.py
@Time    :   2020/09/22 19:32:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import os
import wave
import shutil
import datetime
import numpy as np
from scipy import signal
from pylab import *
from scipy.io import wavfile
from scipy import interpolate, fftpack
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore")

def debug_print(info):
    assert(0==0)
    #print(info)

def debug_plot(data, data1, title):
    plt.figure()
    plt.title(title)
    plt.plot(data)
    plt.plot(data1)
    plt.show()

class MicData:
    """ 存储每个麦克风的数据信息 """
    _micnum: int
    _cSlice: int             # 覆盖的范围
    _rid: int                # no obstacles in "_rid" distance 
    _thdz: int
    _thdf: int
    _nor_val: int            # 经验值
    _x_y: list               # for plot figure
    _process_result: list
    
    _rate = 44100
    _low = 18000
    _high = 22000
    _dur_time = 10/1000       # 10ms
    _distance = 4851          # t=0.11s;  rate=44100
    _target_brid = -500       # for bluetooth
    
    def __init__(self, micnum: int, thdz: int, thdf: int, cSlice: int, rid: int) -> None:
        """
            初始化各值
            _nor_val 和 _thdz、_thdf 有密切关系，一句经验
        """
        self._micnum = micnum
        self._x_y=[]
        self._process_result=[]

        self._rid = rid
        self._cSlice = cSlice
        self._thdz = thdz
        self._thdf = thdf
        self._nor_val = 500000
        if rid != self._target_brid:
            self._nor_val = 1000000
        
    def FilterBandpass(self, wave, fs):
        """
            带通滤波
            return: filtered data
        """
        l = self._low/(fs/2)
        h = self._high/(fs/2)
        b, a = signal.butter(5, [l, h], "bandpass")     # 配置滤波器 5/8 表示滤波器的阶数
        return signal.filtfilt(b, a, wave)              # data为要过滤的信号

    def averageNormalization(self, corr):
        """
            按照周期分别提取出左右声道的音频(找到最高峰进行划分), 多个周期取平均
            return: the average data(L, R)
        """
        #peaks, _ = signal.find_peaks(corr, height=1000, distance=24480)  # 寻找整个序列的峰值
        peaks_lists = [[]for i in range(2)]
        cycles_lists = [[]for i in range(2)]

        i = 63000                                       # 0; 针对蓝牙播放不完整的情况，从x轴一定的位置开始切分
        h_thd = 10000                                   # 最高峰的判断阈值
        if self._rid != self._target_brid:
            i = 0            #63000 # 
            h_thd = 1000000   #20000#
        first = 1
        first_detect = False
        while i+self._distance < corr.size:             # 提取最高峰并提取片段，按声道分别进行存储
            site=np.argmax(corr[i:i+self._distance])+i
            if corr[site] > h_thd :
                c = {}
                c["PeakIndex"] = site
                c["PeakHeight"] = corr[site]
                c["Corr"] = np.abs(corr[site+self._rid:site+self._cSlice])
                channel_flag = first 
                if self._rid != self._target_brid:
                    channel_flag =first % 2
                if channel_flag: # % 2 :
                    peaks_lists[0].append(site)
                    cycles_lists[0].append(c)
                    debug_print("micnum:%d - site:%d"%(self._micnum, site))
                else:
                    peaks_lists[1].append(site)
                    cycles_lists[1].append(c)
                    debug_print("micnum:%d = site:%d"%(self._micnum, site))
                if first == 1 :
                    first_detect = True
            if first_detect :
                first += 1
            i += self._distance
    
        debug_print("micnum:%d, len(peaks_lists)[%d]:%d"%(self._micnum,0,len(peaks_lists[0])))
        debug_print("micnum:%d, len(peaks_lists)[%d]:%d"%(self._micnum,1,len(peaks_lists[1])))

        out = np.zeros(self._cSlice-self._rid)
        out1 = np.zeros(self._cSlice-self._rid)
        for i in range(2):
            count = 0
            for i1 in range(len(cycles_lists[i])):
                if i == 0:
                    if len(cycles_lists[i][i1][("Corr")])!=(self._cSlice-self._rid):
                        count += 1
                    else:  out += cycles_lists[i][i1][("Corr")]
                else:
                    if len(cycles_lists[i][i1][("Corr")])!=(self._cSlice-self._rid):
                        count += 1
                    else: out1 += cycles_lists[i][i1][("Corr")]
            if i == 0:
                length = len(cycles_lists[i])-count
                out = out/length  # 平均
            else:
                length = len(cycles_lists[i])-count
                out1 = out1/length  # 平均
        return out, out1

    def afterAN(self, Ncorr, Ncorr1, micnum):
        """
            多周期平均后的处理：
            1. 包络检波部分，共两步
            2. 提取图2(The Other)中高于/低于图1(Empty)的所有点
            3. 去除不对称的峰, 启发式
            4. 找出值最大部分的最大差值对应的位置
            5. 计算各个区间当前信号与背景信号的差异（类比于求方差的思想）
            return: the number of microphone, Maximum difference, Minimum difference
        """
        # 归一化——将值统一到(0,1)
        aNcorr = Ncorr/self._nor_val            
        aNcorr1 = Ncorr1/self._nor_val


        """1. 包络检波部分，共两步"""
        # 1.1 提取极值点
        x=signal.argrelextrema(aNcorr, np.greater)[0]
        y=aNcorr[x]
        x1=signal.argrelextrema(aNcorr1, np.greater)[0]
        y1=aNcorr1[x1]
        if x.size <=0 or x1.size <= 0: # 若没有极值点，立即返回
            return micnum,0,0
    
        # 1.2 统一坐标轴，插值平滑
        x_min = max(x[0],x1[0])
        x_max = min(x[x.size-1],x1[x1.size-1])
        x_new = np.linspace(x_min,x_max,self._cSlice*2)     # _cSlice的大小会影响每个区域点的个数
        func=interpolate.interp1d(x,y, kind="cubic")
        y_smooth=func(x_new)
        func1=interpolate.interp1d(x1,y1, kind="cubic")
        y_smooth1=func1(x_new)
        debug_print("Type:%s"%(type(y_smooth1)))
        
        # 储存数据，供 Detector.py 打印浏览
        if self._rid != self._target_brid:
            self._x_y.append([(x_new+self._rid)/self._rate*340/2,y_smooth])
            self._x_y.append([(x_new+self._rid)/self._rate*340/2,y_smooth1])
        else:
            self._x_y.append([(x_new+self._rid)/self._rate*340,y_smooth])
            self._x_y.append([(x_new+self._rid)/self._rate*340,y_smooth1])
        

        """ 2. 提取图2(The Other)中高于/低于图1(Empty)的所有点"""
        X=np.zeros(self._cSlice*2)      # 记录目标区间的x轴值，非目标区间统一设置为 -0.01
        Y=np.zeros(self._cSlice*2)      # 记录背景信号的y轴值
        Y1=np.zeros(self._cSlice*2)     # 记录当前信号的y轴值

        i = 0
        while i < self._cSlice*2:
            while i < self._cSlice*2 and y_smooth1[i] != y_smooth[i] :
                X[i]=x_new[i]
                Y[i]=y_smooth[i]
                Y1[i]=y_smooth1[i]
                if i-2 > 0 and Y1[i-2] > Y1[i-1] and Y1[i] > Y1[i-1] :      # 断开每个峰值
                    X[i-1]=-0.01
                    Y[i-1]=Y1[i-1]=0
                if i-1 > 0 and (Y1[i]-Y[i])*(Y1[i-1]-Y[i-1])<0:             # 断开当前信号与背景信号交叉处
                    X[i-1]=-0.01
                    Y[i-1]=Y1[i-1]=0
                i+=1
            if i == self._cSlice*2 : break
        
            X[i]=-0.01
            Y[i]=Y1[i]=0
            i+=1


        """3. 去除不对称的峰, 启发式"""
        site=self._cSlice*2  # site=i
        addc=0
        minusc=0
        mark=site

        i = 0
        while i < site :
            # 跳过 X 值为 -0.01 的区间
            while i < site and X[i] < 0 : i+=1
            if i >= site : break

            # 当前区间 X 值>=0
            mark = i
            while i < site and X[i] >= 0 :
                if i+1 < site and X[i+1] >= 0 :
                    if Y1[i+1] > Y1[i] : addc+=1
                    if Y1[i+1] < Y1[i] : minusc+=1
                i+=1
        
            if addc >= 7*minusc or minusc >= 7*addc : # 7？ 有待测试确定
                while mark < site and X[mark] >= 0 :
                    X[mark]=-0.01
                    Y[mark]=Y1[mark]=0
                    mark+=1
        
            addc=0 #重新赋值
            minusc=0
            mark=site
        

        """4. 找出值最大部分的最大差值对应的位置"""
        val=np.zeros(site)                  # 背景信号各区间纵轴（Y）值的累计值
        val1=np.zeros(site)                 # 当前信号各区间纵轴（Y1）值的累计值
        count=np.zeros(site)                # 各区间的点数（背景信号与当前信号对应区间该值相同）
        maxsite=np.zeros(site)              # 各区间最高峰的值对应的横轴值（X）

        i = 0
        snum = 0
        maxheight = -1
        while i < site :
            while i < site and X[i] < 0 : i+=1
            if i >= site : break

            while i < site and X[i] >= 0 :
                delta_h=Y1[i]#-Y[i]         # 以当前信号的最高值代表该区间的位置
                if maxheight < delta_h :
                    maxheight=delta_h
                    maxsite[snum]=i
                val1[snum]+=Y1[i]
                val[snum]+=Y[i]
                count[snum]+=1
                i+=1
            snum+=1
            maxheight=-1
        

        """5. 计算各个区间当前信号与背景信号的差异（类比于求方差的思想）"""
        # 5.1 类比于求方差，不除以各区间的总点数
        i = 0
        snumi = 0
        cgma=np.zeros(site)
        cgma1=np.zeros(site)
        while i < site :
            while i < site and X[i] < 0 : i+=1
            if i >= site : break

            aver = val[snumi]/count[snumi]
            while i < site and X[i] >= 0 :
                cgma[snumi] += (Y[i] - aver) * (Y[i] - aver)
                cgma1[snumi] += (Y1[i] - aver) * (Y1[i] - aver)
                i+=1
            snumi+=1

        # 5.2 基于4.1计算差异值
        mx = 0                              # 正向最大差异值
        mi = 2147483647                     # 反向最大差异值（绝对值最大）
        mxs = -1                            # 正向最大差异值对应的区间下标
        mis = -1                            # 反向最大差异值对应的区间下标
        zflag = False                       # 前面没有正着超过阈值的情况，可取delta_v < 0 and abs(delta_v)>thdf的距离

        debug_print("mic:%d"%micnum)
        for i in range(snum):
            delta_v=(cgma1[i]-cgma[i])*15   #val1[i]-val[i]#
            maxD=(X[int(maxsite[i])]+self._rid)/self._rate*340
            if self._rid != self._target_brid: maxD /= 2

            delta_v=delta_v*math.e**(0.1*maxD) # maxD*maxD           # 与距离有关联，具体待探究
            if delta_v > self._thdz:
                debug_print("%.2fm %f %f"%(maxD, delta_v, delta_v/count[i]))
                zflag=True
            elif delta_v < 0 and abs(delta_v)>self._thdf and zflag == False:
                debug_print("%.2fm %f %f"%(maxD, delta_v, delta_v/count[i]))
            else:
                debug_print("%.2fm %f %f"%(maxD, delta_v, delta_v/count[i])) 
            if mx<delta_v:
                mx=delta_v
                mxs=i
            if delta_v<mi:
                mi=delta_v
                mis=i
        if mi >0 : mi=0                     # mi 的值理论上应该<0

        return micnum,mx,mi
    
    
    def process(self, PATH1, PATH2, micnum):
        """
            处理音频：
            1. 获得音频原始数据
            2. 滤波
            3. 互相关
            4. 平均与归一化
            5. 多周期平均后的处理（详见afterAN()函数）
            return: null
        """

        filename1 = f"{PATH1}/mic{micnum}.wav"
        filename2 = f"{PATH2}/mic{micnum}.wav"
        t = np.arange(0, self._dur_time, 1/self._rate)
        chirp = signal.chirp(t, self._low,self._dur_time, self._high, method = "linear")

        """1. 获得音频原始数据"""
        Fs, y = wavfile.read(filename1) # 空
        Fs1, y1 = wavfile.read(filename2) # 空
        
        """2. 滤波"""
        fliter_y = self.FilterBandpass(y, Fs)
        fliter_y1 = self.FilterBandpass(y1, Fs1)

        """3. 互相关"""
        corr = np.abs(np.correlate(fliter_y, chirp, mode="full"))
        corr1 = np.abs(np.correlate(fliter_y1, chirp, mode="full"))
        
        #debug_plot(y,y1,"original")
        #debug_plot(fliter_y,fliter_y1, "filtered")
        #debug_plot(corr,corr1, "corr")
        
        """4. 平均与归一化"""
        Ncorr, Ncorr_1= self.averageNormalization(corr)
        Ncorr1, Ncorr1_1 = self.averageNormalization(corr1)

        """5. 多周期平均后的处理"""
        micnum,mx,mi = self.afterAN(Ncorr,Ncorr1, micnum)
        micnum,mx1,mi1 = self.afterAN(Ncorr_1,Ncorr1_1, micnum)
        
        # 储存数据，会在每一次比较之后进行清空（因为要重复使用）
        self._process_result.append(micnum)
        self._process_result.append(max(mx,mx1))
        self._process_result.append(min(mi,mi1))
        
        