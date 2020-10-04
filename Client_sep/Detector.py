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
from threading import Thread, Event
import logging, logzero

from processMic import MicData

import warnings
warnings.filterwarnings("ignore")

logger = logzero.setup_logger("client", level=logging.INFO)

class URadar:
    """ 封装类 """
    _thdz: float             # 5.5 
    _thdf: float             # 6.5
    _outcome: str

    _mics = [1, 2, 3, 4]
    _stability_count = 1
    _to_reset = False
    _micData = []
    
    _PATH1: str
    _PATH2: str
    
    file = None
    _plotFile = [[]for i in range(2)]
    _MAC: str
    
    def __init__(self, thdz=0.3, thdf=0.35, MAC="None") -> None:
        """
            初始化正向阈值，反向阈值，麦克风对象(MicData)
        """
        self._thdz=thdz
        self._thdf=thdf
        self._MAC=MAC
        self._PATH1 = "recordData/"+MAC+"/Empty"
        self._PATH2 = "recordData/"+MAC+"/Barrier/barrier"
        for i in self._mics:
            self._plotFile[0].append(None)
            self._plotFile[1].append(None)
            self._micData.append(MicData(i, thdz, thdf))

    def reset(self):
        """
            重置背景信号
            return: "OK" or null
        """ 
        logger.info(self._MAC+" 正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
            
        out = os.popen("python3 playRec.py "+self._PATH1 +" 5 "+self._MAC).read().replace("\n", "")
        #out = "OK"
        if out=="OK":
            logger.info(self._MAC+" 重置成功！")
        else:
            logger.info(self._MAC+" 重置失败！")
            sys.exit()
        return out
    

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
        
        self.file.writelines("<<<<<<<<\n")
        for i in range(len(self._mics)):
            print(i+1 ,self._micData[i]._process_result[1],self._micData[i]._process_result[2])
            self.file.writelines(str(self._micData[i]._process_result[0])+"---")
            self.file.writelines("mx:"+("%.2f"%self._micData[i]._process_result[1])+",mi:-"+("%.2f"%abs(self._micData[i]._process_result[2]))+"\n")
            if self._micData[i]._process_result[1] <= self._thdz and abs(self._micData[i]._process_result[2]) <= self._thdf: # 阈值的设定？ empty    有待检验
                count+=1
            self._micData[i]._process_result.clear()    # clear original data
            
            for k in range(2):   # two speakers
                if len(self._micData[i]._x_y) and k*2 < len(self._micData[i]._x_y) :
                    
                    plt.figure()
                    label=["Empty","The other"]
                    plt.ylim(0,0.8)
                    plt.plot(self._micData[i]._x_y[k*2][0],self._micData[i]._x_y[k*2][1], linewidth=1)
                    plt.plot(self._micData[i]._x_y[k*2+1][0],self._micData[i]._x_y[k*2+1][1], c="red",linewidth=1)
                    plt.legend(label, loc =0) 
                    plt.title("".join(["mic",str(self._micData[i]._micnum), "-", str(k)]))
                    plt.xlabel("Distance(m)")
                    plt.ylabel("Correlation")
                    
                    for d in self._micData[i]._x_y[k*2+1][1]:
                        self._plotFile[k][self._micData[i]._micnum-1].write(("%.5f"%d)+",")
                    self._plotFile[k][self._micData[i]._micnum-1].write("\n")
                    #print(self._micData[i]._micnum,self._micData[i]._x_y[k*2][0])
            self._micData[i]._x_y.clear()

        plt.show() 
        #print(count)    
        return count

    def RecordAudio(self, PATH):
        """
            采集音频数据,中间会根据服务器的情况进行重置，输出提示音等
            return: null
        """
        if not os.path.exists(PATH): 
            os.makedirs(PATH)

        if self._to_reset == True:
            self.reset()
            self._to_reset = False

        out = os.popen("python3 playRec.py "+PATH +" 3 "+self._MAC).read()
        #print(out)
        

    def detect(self):
        """
            检测程序：调用录音等程序，判断环境是否发生波动
            return: the outcome of detecting
        """
        # 记录数据
        for k in range(2):
            f_index = 1
            part_path = "MIC/"+self._MAC+"/LMic"
            if k == 1:
                part_path = "MIC/"+self._MAC+"/RMic"
            if not os.path.exists(part_path): 
                os.makedirs(part_path)
            for k1 in range(len(self._plotFile[k])):
                self._plotFile[k][k1] = open(part_path+"/data"+str(f_index)+".txt", mode="a+")
                f_index += 1
        
        self.file=open("MIC/Data-"+self._MAC+".txt",mode="a+")
        self.file.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\n")
      
        
        self.RecordAudio(self._PATH2)
        count = self.forEveryMic(self._PATH1, self._PATH2)
        # 
        if count < 3: # 3
            logger.info(self._MAC+" 检测到环境波动...")
            time.sleep(3)
            # 判断环境是否稳定
            scount=0
            postfix = 1
            PATH2=self._PATH2
            self.RecordAudio(PATH2)
            while scount < self._stability_count:
                logger.info(self._MAC+" 持续检测中...")
                PATH3=self._PATH2+str(postfix)
                self.RecordAudio(PATH3)
                count = self.forEveryMic(PATH2, PATH3)
                if count < 3:
                    scount = 0
                PATH2=PATH3
                postfix+=1
                scount+=1
            count = self.forEveryMic(self._PATH1, PATH2)
    
        if count >= 3: 
            self._outcome="empty"
            
        else:
            self._outcome="nonempty"

        logger.info(self._MAC+f" 检测结果：{self._outcome}")
        self.file.writelines(self._outcome+"\n")
        self.file.close()
        for k in range(2):
            for f in self._plotFile[k]:
                f.close()
        
        time.sleep(2)
        return self._outcome
        

if __name__ == "__main__":
    """ for testing """
    
    Radar=URadar(MAC="FC:58:FA:F7:D5:EF")
    reset_choice = input("reset_or_not:")
    if reset_choice == "1":
        Radar.reset()
    while True:
        Radar.detect()