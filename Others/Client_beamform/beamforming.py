# -*- encoding: utf-8 -*-
'''
@File    :   beamforming.py
@Time    :   2020/09/22 19:32:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

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

    _cta = [0, 30, 60, 90]   #
    _rfa = [0, 45, 90, 135, 180, 225, 270, 315]      # 相对于mic1   
    _mics = [1, 2, 3, 4]
    _micd = 5.8*(2**0.5/2)/100              #  对角线的一半
    _micData = []
    
    _PATH1 = "Empty"
    _PATH2 = "Barrier/barrier"
    _stability_count = 1
    _reset_order = False
    _prompt: str = "None"
    
    _file = None
    _plotFile = []
    _plotFileR = []
    
    def __init__(self, thdz=1.5, thdf=1.5) -> None:
        """
            初始化正向阈值，反向阈值，麦克风对象(MicData)
        """
        self._thdz = thdz
        self._thdf = thdf
        for cta in self._cta:
            for rfa in self._rfa:
                file = None
                file_name = "MIC/LMic/data"+str(cta)+"-"+str(rfa)+".txt"
                self._plotFile.append([file,file_name])
                file1 = None
                file_name1 = "MIC/RMic/data"+str(cta)+"-"+str(rfa)+".txt"
                self._plotFileR.append([file1,file_name1])
                
                self._micData.append(MicData(thdz, thdf, cta, rfa))
                if cta == 0: break
            
    
    def reset(self):
        """
            重置背景信号
            return: "OK" or null
        """
        logger.info("正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
            
        #out = os.popen("python3 playRec.py "+self._PATH1 +" 5").read().replace("\n", "")
        out = os.popen("python3 playRec_ns.py "+self._PATH1 +" 5").read().replace("\n", "")
        out = "OK"
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
        index = 0
        Threads=[]
        for cta in self._cta:
            for rfa in self._rfa:
                delta_sample = []
                for micn in self._mics:
                    rfa1 = (180 + rfa + 90*(micn-1)) % 360  # need to modify when mics change
                    d = self._micd * math.sin(cta/180 * math.pi)* math.cos(rfa1/180*math.pi)
                    sample = d*rate/vel
                    #print(sample)
                    delta_sample.append(round(sample))
                #print(delta_sample)
                #print(cta, rfa, ";", self._micData[index]._cta, self._micData[index]._rfa)
                t = Thread(target=self._micData[index].process, args=(chirp, emic_fs_y, bmic_fs_y, delta_sample,))
                Threads.append(t)
                index += 1
                if cta == 0: break
                
        for t in Threads:
            t.start()
        for t in Threads:
            t.join()
        
        outcome = "empty"
        for micData in self._micData:
            print(micData._cta, micData._rfa, ("%.2f"%micData._result[0]), ("%.2f"%micData._result[1]))
            if len(micData._x_y):
                print(len(micData._x_y))
                plt.figure()
                label=["".join(["mic","empty"]),"".join(["mic","other"])]
                plt.plot(micData._x_y[0][0], micData._x_y[0][1])
                plt.plot(micData._x_y[1][0], micData._x_y[1][1])
                plt.legend(label, loc =0) 
                plt.title(str(micData._cta)+"-"+str(micData._rfa))
                
                f_index = 0
                if micData._cta != 0:
                    f_index = int((micData._cta/30-1)*8+micData._rfa/45 + 1) # need to modify when angles change
                for d in micData._x_y[1][1]:
                    self._plotFile[f_index][0].write(("%.5f"%d)+",")
                self._plotFile[f_index][0].write("\n")
                if len(micData._x_y) > 2:                             # the other mic
                    for d in micData._x_y[3][1]:
                        self._plotFileR[f_index][0].write(("%.5f"%d)+",")
                    self._plotFileR[f_index][0].write("\n")
                
            if micData._result[0] > self._thdz or abs(micData._result[1]) > self._thdf:
                outcome = "nonempty"
            
            # clear original data
            micData._result.clear()               
            micData._x_y.clear()
                
        print(outcome)
        plt.show()
        return outcome
        

    def RecordAudio(self, PATH):
        """
            采集音频数据,中间会根据服务器的情况进行重置，输出提示音等
            return: null
        """
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
        out = os.popen("python3 playRec_ns.py "+PATH +" 3").read().replace("\n", "")
        #print(out)
        
    def detect(self):
        """
            检测程序：调用录音等程序，判断环境是否发生波动
            return: the outcome of detecting
        """
        for f in self._plotFile:
            f[0] = open(f[1], mode="a+")
        for f in self._plotFileR:
            f[0] = open(f[1], mode="a+")
            
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
        for f in self._plotFile:
            f[0].close()
        for f in self._plotFileR:
            f[0].close()    
        
        return outcome

if __name__ == "__main__":
    """ for testing """
    
    bfObject = URadar()
    choice = int(input("reset_or_not:"))
    if choice == 1:
        bfObject.reset()
    while True:
        bfObject.detect()
    
