import os
import wave
import shutil
import datetime
import numpy as np
from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate
from scipy import fftpack

import warnings
warnings.filterwarnings("ignore")


class MicData:

    _cSlice: int             # 988       # 3.5 m
    _rid: int                # 70           # no obstacles in 25 cm 
    _thdz: int
    _thdf: int
    
    _rate = 44100
    _low = 18000
    _high = 22000
    _distance = 4851         # t=0.11s;  rate=44100
    _nor_val = 2000000        # 经验值
    
    # record data for plotting figure
    _x_y_0: list
    _x_y_30: list
    _x_y_60: list
    _x_y_90: list

    def __init__(self, thdz: int, thdf: int) -> None:
        self._cSlice = 100
        self._rid = -100
        self._thdz = thdz
        self._thdf = thdf
        self._x_y_0 = []
        self._x_y_30 = []
        self._x_y_60 = []
        self._x_y_90 = []
        

    def FilterBandpass(self, wave, fs):
        """ 应用带通滤波器 """
        l = self._low/(fs/2)
        h = self._high/(fs/2)
        b, a = signal.butter(5, [l, h], "bandpass")  # 配置滤波器 5/8 表示滤波器的阶数
        return signal.filtfilt(b, a, wave)  # data为要过滤的信号

    def averageNormalization(self, corr):
        """多个周期取平均"""
        #peaks, _ = signal.find_peaks(corr, height=1000, distance=24480)  # 寻找整个序列的峰值
        peaks_lists = [[]for i in range(2)]
        cycles_lists = [[]for i in range(2)]

        i=22050             # 44100     0.5s
        first=1
        first_detect = False
        while i+self._distance < corr.size:
            site=np.argmax(corr[i:i+self._distance])+i
            if corr[site] > 100000 :
                c = {}
                c["PeakIndex"] = site
                c["PeakHeight"] = corr[site]
                c["Corr"] = np.abs(corr[site+self._rid:site+self._cSlice])
                if first % 2 :
                    peaks_lists[0].append(site)
                    cycles_lists[0].append(c)
                else:
                    peaks_lists[1].append(site)
                    cycles_lists[1].append(c)
                if first == 1 :
                    first_detect = True
            if first_detect:
                first += 1
            i+=self._distance
    
        out = np.zeros(self._cSlice-self._rid)
        out1 = np.zeros(self._cSlice-self._rid)
        for i in range(2):
            count=0
            for i1 in range(len(cycles_lists[i])):
                if i == 0:
                    if len(cycles_lists[i][i1][("Corr")])!=(self._cSlice-self._rid):
                        count+=1
                    else:
                        out += cycles_lists[i][i1][("Corr")]
                else:
                    if len(cycles_lists[i][i1][("Corr")])!=(self._cSlice-self._rid):
                        count+=1
                    else:
                        out1 += cycles_lists[i][i1][("Corr")]
            if i == 0:
                length = len(cycles_lists[i])-count
                out = out/length  # 平均
            else:
                length = len(cycles_lists[i])-count
                out1 = out1/length  # 平均
        return out, out1

    def afterAN(self, Ncorr, Ncorr1, cta, rfa):

        aNcorr = Ncorr/self._nor_val            
        aNcorr1 = Ncorr1/self._nor_val

        #获取极值点    
        x=signal.argrelextrema(aNcorr, np.greater)[0]
        y=aNcorr[x]
        x1=signal.argrelextrema(aNcorr1, np.greater)[0]
        y1=aNcorr1[x1]
        
        #for safety
        if x.size <=0 or x1.size <= 0:
            return 0,0
    
        #统一坐标轴，插值平滑
        x_min=max(x[0],x1[0])
        x_max=min(x[x.size-1],x1[x1.size-1])
        x_new = np.linspace(x_min,x_max,self._cSlice*2) #!!!_cSlice的大小会影响每个区域点的个数
        func=interpolate.interp1d(x,y, kind="cubic")
        y_smooth=func(x_new)
        func1=interpolate.interp1d(x1,y1, kind="cubic")
        y_smooth1=func1(x_new)
        #print("Type",type(y_smooth1))
        
        #self._x_y.append([(x_new+self._rid)/self._rate*340/2,y_smooth])
        if cta == 0:
            self._x_y_0.append([(x_new+self._rid)/self._rate*340/2,y_smooth1])
        if cta == 30:
            self._x_y_30.append([(x_new+self._rid)/self._rate*340/2,y_smooth1])
        if cta == 60:
            self._x_y_60.append([(x_new+self._rid)/self._rate*340/2,y_smooth1])
        if cta == 90:
            self._x_y_90.append([(x_new+self._rid)/self._rate*340/2,y_smooth1])
        """
        plt.figure()
        label=["Empty","The other"]
        #plt.plot(x,y,"o")
        plt.ylim(0,1)
        plt.plot((x_new+self._rid)/self._rate*340/2, y_smooth,linewidth=1)
        #plt.plot(x1,y1,"*")
        plt.plot((x_new+self._rid)/self._rate*340/2, y_smooth1,c="red",linewidth=1)
        plt.legend(label, loc =0) 
        plt.title("".join([str(cta),"-", str(rfa)]))
        #plt.title("Comparison")
        #plt.title("Envelope Detection")
        plt.xlabel("Distance(m)")
        plt.ylabel("Correlation")
            
        #plt.show()
        """
        
        #提取图2(The Other)中高于/低于图1(Empty)的所有点
        X=np.zeros(self._cSlice*2)
        Y=np.zeros(self._cSlice*2)
        Y1=np.zeros(self._cSlice*2)
        i=0
        while i < self._cSlice*2:
            while i < self._cSlice*2 and y_smooth1[i] != y_smooth[i] :
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
            if i == self._cSlice*2 : break
        
            X[i]=-0.01
            Y[i]=Y1[i]=0
            i+=1

        # 去除不对称的峰, 启发式;
        site=self._cSlice*2  # site=i
        addc=0
        minusc=0
        mark=site
        i=0
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
        for i in range(snum):
            delta_v=val1[i]-val[i]
            maxD=(X[int(maxsite[i])]+self._rid)/self._rate*340/2
            #if val[i]>10:
            delta_v=delta_v*math.e**(0.2*maxD)#maxD*maxD
            #else:
            #    delta_v=delta_v*math.e**(0.4*maxD)#maxD*maxD
            if delta_v > self._thdz:
                #print("%d: %f %f %fm"%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self._rid)/self._rate*340/2))
                zflag=True
            #elif delta_v < 0 and abs(delta_v)>self._thdf and zflag == False:
                #print("%d: %f %f %fm"%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self._rid)/self._rate*340/2-0.2))
            #else:
                #print("%d: %f %f %fm"%(i, delta_v, delta_v/count[i],(X[int(maxsite[i])]+self._rid)/self._rate*340/2)) 
            if mx<delta_v:
                mx=delta_v
                mxs=i
            if delta_v<mi:
                mi=delta_v
                mis=i
        if mi >0 :
            mi=0

        return mx,mi

    def process(self, chirp, emic_fs_y, bmic_fs_y, delta_sample, cta, rfa):
        """处理音频"""

        min_delta = min(delta_sample)
        #print(delta_sample, min_delta)
        
        fliter_ey = []
        fliter_by = []
        for i in range(len(emic_fs_y)):
            edata = emic_fs_y[i]
            bdata = bmic_fs_y[i]
            eres = self.FilterBandpass(edata[2], edata[1])
            bres = self.FilterBandpass(bdata[2], bdata[1])
            fliter_ey.append(eres)
            fliter_by.append(bres)
            
        length_ey = len(fliter_ey[0])-15       # max(delta_sample[i])-min_delta =12
        length_by = len(fliter_by[0])-15
        
        aligned_efy = []
        aligned_bfy = []
        for i in range(len(delta_sample)):
            start = delta_sample[i] - min_delta
            end1 = length_ey + start
            end2 = length_by + start
            aligned_efy.append(fliter_ey[i][start:end1])
            aligned_bfy.append(fliter_by[i][start:end2])
            #print("aligned", len(aligned_efy[i]))
        
        sum_efy = aligned_efy[0]
        sum_bfy = aligned_bfy[0]
        for i in range(1, len(aligned_efy)):
            sum_efy += aligned_efy[i]
            sum_bfy += aligned_bfy[i]
      
        # 互相关
        sum_ecorr = np.abs(np.correlate(sum_efy, chirp, mode="full"))
        sum_bcorr = np.abs(np.correlate(sum_bfy, chirp, mode="full"))
        
        """
        plt.figure()
        label=["".join(["mic","empty"]),"".join(["mic","other"])]
        plt.plot(sum_ecorr)
        plt.plot(sum_bcorr)
        #plt.plot(sum_corr)
        plt.legend(label, loc =0) 
        plt.title("comparsion")
        plt.show()
        """
        # 平均 and 归一化
        eNcorr, eNcorr1 = self.averageNormalization(sum_ecorr)
        bNcorr, bNcorr1 = self.averageNormalization(sum_bcorr)
        
        mx,mi = self.afterAN(eNcorr,bNcorr, cta, rfa)
        mx1,mi1 = self.afterAN(eNcorr1,bNcorr1, cta, rfa)
        
        return max(mx,mx1), min(mi,mi1)

        
        
        