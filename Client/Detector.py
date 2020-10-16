# -*- encoding: utf-8 -*-
'''
@File    :   Detector.py
@Time    :   2020/09/22 19:21:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import os, wave, shutil
import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate
from threading import Thread, Event
import logging, logzero
from playRec import playprompt
from processMic import MicData
from forDebug import Debug

import warnings
warnings.filterwarnings("ignore")

logger = logzero.setup_logger("client", level=logging.INFO)

 
class URadar:
    """ 封装类 """
    _thdz: float             # 5.5 
    _thdf: float             # 6.5
    _outcome: str
    _prompt: str = "None"

    _mics=[1, 2, 3, 4]
    _stability_count = 1
    _reset_order = False
    _micData = []
    _debug: Debug = None
    
    _PATH1="Empty"
    _PATH2="Barrier/barrier"
    
    def __init__(self, thdz=0.4, thdf=0.45) -> None:      # 0.45   0.45
        """
            初始化正向阈值，反向阈值，麦克风对象(MicData)
        """
        self._thdz=thdz
        self._thdf=thdf
        for i in self._mics:
            self._micData.append(MicData(i, thdz, thdf, 2000, 390))
        self._debug=Debug()
        

    def reset(self):
        """
            重置背景信号
            return: "OK" or null
        """
        logger.info("正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
            
        out = os.popen("python3 playRec.py "+self._PATH1 +" 5").read().replace("\n", "")
        #out = "OK"
        if out=="OK":
            logger.info("重置成功！")
        else:
            logger.info("重置失败！")
        return out


    def RecordAudio(self, PATH):
        """
            采集音频数据,中间会根据服务器的情况进行重置，输出提示音等
            return: null
        """
        if not os.path.exists(PATH): os.makedirs(PATH)
            
        if self._reset_order:
            self.reset()
            self._reset_order=False
            
        #存在提示音要占据音频端口的情况，先播放提示音
        if self._prompt != "None":
            #playprompt(self._prompt)
            print("prompt",self._prompt)
            self._prompt="None"

        out = os.popen("python3 playRec.py "+PATH +" 3").read()
        #print(out)
    

    def forEveryMic(self, PATH1, PATH2):
        """
            对每个mic收集的数据进行process处理，并行
            中间可以输出图像
            return: the number of microphones whose result is "empty"
        """
        count = 0
        Threads=[]
        for i in range(len(self._mics)):
            t = Thread(target=self._micData[i].process, args=(PATH1, PATH2, self._mics[i],))
            t.start()
            Threads.append(t)
        for t in Threads:
            t.join()
            
        self._debug.saveSep2threshdFile()
        for i in range(len(self._mics)):
            print(i+1 ,self._micData[i]._process_result[1],self._micData[i]._process_result[2])
            self._debug.save2threshdFile(self._micData[i]._process_result[0],\
                                         self._micData[i]._process_result[1],self._micData[i]._process_result[2])
            if self._micData[i]._process_result[1] <= self._thdz and \
               abs(self._micData[i]._process_result[2]) <= self._thdf: # 阈值的设定？ empty    有待检验
                count+=1
            elif self._micData[i]._process_result[1] > 0.6 or \
                 abs(self._micData[i]._process_result[2]) > 0.65:
                self._debug.save_valued_data(PATH1, PATH2)
            self._micData[i]._process_result.clear()    # clear original data
            
            for k in range(2):   # two speakers
                if len(self._micData[i]._x_y) and k*2 < len(self._micData[i]._x_y) :
                    self._debug.save2plotStream(self._micData[i]._x_y[k*2+1][1],self._micData[i]._micnum,k)
            #self._micData[i]._x_y.clear()
        
        self._debug.plotData(self._micData)
        for i in range(0,4):
            self._micData[i]._x_y.clear()
   
        return count
      

    def detect(self):
        """
            检测程序：调用录音等程序，判断环境是否发生波动
            return: the outcome of detecting
        """
        # 记录数据
        self._debug.openFile()
        
        self.RecordAudio(self._PATH2)
        count = self.forEveryMic(self._PATH1, self._PATH2)
        # 
        if count < 4: # 3
            logger.info("检测到环境波动...")
            time.sleep(1)
            # 判断环境是否稳定
            scount=0
            postfix = 1
            PATH2=self._PATH2
            self.RecordAudio(PATH2)
            while scount < self._stability_count:
                logger.info("持续检测中...")
                PATH3=self._PATH2+str(postfix)
                self.RecordAudio(PATH3)
                count = self.forEveryMic(PATH2, PATH3)
                PATH2=PATH3
                postfix+=1
                scount+=1
                if count < 4: scount = 0
            count = self.forEveryMic(self._PATH1, PATH2)
    
        if count >= 4: self._outcome="empty"
        else: self._outcome="nonempty"

        logger.info(f"检测结果：{self._outcome}")

        self._debug.saveOut2threshdFile(self._outcome)
        self._debug.closeFile()
        
        time.sleep(10)
        return self._outcome
        

if __name__ == "__main__":
    """ for testing """
    
    Radar=URadar()
    reset_choice = input("reset_or_not:")
    if reset_choice == "1":
        Radar.reset()
    while True:
        Radar.detect()
