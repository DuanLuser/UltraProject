import os, wave, math
import shutil, datetime
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
from beamformMic import MicData
warnings.filterwarnings("ignore")

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import mpl_toolkits.mplot3d

logger = logzero.setup_logger("client", level=logging.INFO)

class URadar:
    """封装类"""
    
    _thdz: float             #7.5           # 5.5 
    _thdf: float             #8.5           # 6.5
    _micData: MicData
    _cta = [0, 30, 60, 90]   #
    _rfa = [0, 60, 120, 180, 240, 300] # 相对于mic4
    
    _mics = [1, 3, 4, 5, 6]
    _micd = 4.6/100                #  m
    
    _PATH1 = "Empty"
    _PATH2 = "Barrier/barrier"
    _stability_count = 2
    _reset_order = False
    _prompt: str = "None"
    _file = None
    
    def __init__(self, thdz=1.5, thdf=1.5) -> None:
        self._thdz = thdz
        self._thdf = thdf
        self._micData = MicData(thdz, thdf)
    
    def reset(self):
        logger.info("正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
            
        out = os.popen("python3 playRec.py "+self._PATH1 +" 5").read().replace("\n", "")
        if out=="OK":
            logger.info("重置成功！")
        else:
            logger.info("重置失败！")
        return out

    def beamform_detect(self, EPath, BPath):
        """ """
        rate = 44100
        low = 18000
        high = 22000
        dur_time = 10/1000          # 10ms
        vel = 340

        emic_fs_y = []
        bmic_fs_y = []
        for micnum in self._mics:
            filename=f"{EPath}/mic{micnum}.wav"
            filename1=f"{BPath}/mic{micnum}.wav"
            eFs, ey = wavfile.read(filename)
            bFs, by = wavfile.read(filename1)
            emic_fs_y.append([micnum, eFs, ey])
            bmic_fs_y.append([micnum, bFs, by])
        
        t = np.arange(0, dur_time, 1/rate)
        chirp = signal.chirp(t, low, dur_time, high, method = "linear")

        # 获得音频原始数据
        result = []
        Threads=[]
        for cta in self._cta:
            for rfa in self._rfa:
                delta_sample = []
                for micn in self._mics:
                    rfa1 = rfa + 60*(micn-1)
                    d = self._micd * math.sin(cta/180 * math.pi)* math.cos(rfa1/180*math.pi)
                    sample = d*rate/vel
                    #print(sample)
                    delta_sample.append(round(sample))
                #print(delta_sample)
               
                print("angle:", cta, rfa)
                mx, mi = self._micData.process(chirp, emic_fs_y, bmic_fs_y, delta_sample, cta, rfa)
                print("mx:",mx, "mi:",mi)
                self._file.writelines(str(cta)+"-"+str(rfa)+"->"+"mx:"+("%.2f"%mx)+",mi:-"+("%.2f"%abs(mi))+"\n")
                result.append([cta,rfa, mx,mi])
                if cta == 0: break
                #t = Thread(target=self._micData.process, args=(chirp, emic_fs_y, bmic_fs_y, delta_sample, cta, rfa,))
                #Threads.append(t)
                
        ''' 
        for t in Threads:
            t.start()
        for t in Threads:
            t.join()
        '''
        
        label = ["0", "60", "120", "180", "240", "300" ]
        for cta in self._cta:
            plt.figure()
            plt.ylim(0,1)
            cta_x_y = None
            if cta == 0:
                cta_x_y = self._micData._x_y_0      
            if cta == 30:
                cta_x_y = self._micData._x_y_30
            if cta == 60:
                cta_x_y = self._micData._x_y_60
            if cta == 90:
                cta_x_y = self._micData._x_y_90
                
            for x_y in cta_x_y:
                plt.plot(x_y[0], x_y[1], linewidth=1)

            plt.legend(label, loc =0) 
            plt.title("".join(["cta", "-", str(cta)]))
            plt.xlabel("Distance(m)")
            plt.ylabel("Correlation")
            
        #plt.show()
        
        plt.show()
        outcome = "empty"
        for res in self._micData._result:
            print(res[0], res[1], res[2], res[3])
            if res[2] > self._thdz or abs(res[3]) > self._thdf:
                outcome = "nonempty"
        
        print(outcome)
        return outcome
        
        

    def RecordAudio(self, PATH):
        """采集音频数据"""
        if not os.path.exists(PATH): 
            os.makedirs(PATH)
        
        if self._reset_order:
            self.reset()
            self._reset_order=False
        
        if self._prompt != "None":
            #playprompt(self._prompt)
            print("prompt",self._prompt)
            self._prompt="None"
        
        #out = os.popen("python3 playRec.py "+PATH +" 3").read().replace("\n", "")
        #print(out)
        
    def detect(self):
        
        self._file=open("MIC/Data.txt",mode="a+")
        self._file.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\n")
        
        self.RecordAudio(self._PATH2)
        outcome = self.beamform_detect(self._PATH1, self._PATH2)
        if outcome == "nonempty":
            logger.info("检测到环境波动...")
            time.sleep(3)
            # 判断环境是否稳定
            scount=0
            postfix = 1
            PATH2=self._PATH2
            self.RecordAudio(PATH2)
            while scount < self._stability_count:
                logger.info("持续检测中...")
                PATH3=self._PATH2+str(postfix)
                self.RecordAudio(PATH3)
                outcome = self.beamform_detect(PATH2, PATH3)
                if outcome == "nonempty":
                    scount = 0
                PATH2=PATH3
                postfix+=1
                scount+=1
            outcome = self.beamform_detect(self._PATH1, PATH2)
        logger.info(f"检测结果：{outcome}")
        
        self._file.writelines(outcome+"\n")
        self._file.close()
        return outcome

if __name__ == "__main__":
    
    bfObject = URadar()
    choice = int(input("reset_or_not:"))
    if choice == 1:
        bfObject.reset()
    while True:
        bfObject.detect()
    
