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


def Debug_plot(Data, k):
    plt.figure()
    label=["Empty","The other"]
    plt.ylim(0,0.5)
    plt.plot(Data._x_y[k*2][0], Data._x_y[k*2][1], linewidth=1)
    plt.plot(Data._x_y[k*2+1][0], Data._x_y[k*2+1][1], c="red",linewidth=1)
    plt.legend(label, loc =0) 
    plt.title("".join(["mic",str(Data._micnum), "-", str(k)]))
    plt.xlabel("Distance(m)")
    plt.ylabel("Correlation")

def Debug_plot1(Data):
    plt.figure()
    plt.ylim(0,0.5)
    plt.ylim(0,0.5)
    for i in range(0,4):
        plt.subplot(4,1,i+1)
        plt.plot(Data[i]._x_y[0][0], Data[i]._x_y[0][1], linewidth=1)
        plt.plot(Data[i]._x_y[1][0], Data[i]._x_y[1][1], c="red",linewidth=1)
        plt.title("mic"+str(i+1))
        if i==0:
            label=["Empty","The other"]
            plt.legend(label, loc =0)
    plt.xlabel("Distance(m)")
    plt.ylabel("Correlation")


class URadar:
    """ 封装类 """
    _thdz: float             # 5.5 
    _thdf: float             # 6.5
    _outcome: str

    _mics = [1,2,3,4]
    _stability_count = 1
    _to_reset = False
    _micData = []
    
    _PATH1: str
    _PATH2: str
    
    file = None
    _plotFile = [[]for i in range(2)]
    _MAC: str
    
    def __init__(self, thdz=0.3, thdf=0.35, MAC="None") -> None:    # 阈值的设定？ empty    有待检验
        """
            初始化正向阈值，反向阈值，麦克风对象(MicData)
        """
        self._thdz=thdz
        self._thdf=thdf
        self._MAC=MAC
        self._PATH1 = "recordData/"+MAC+"/Empty"
        self._PATH2 = "recordData/"+MAC+"/Barrier/barrier"
        rid = -500
        cSlice = 2038                                               # 8m
        # 使用本地的扬声器进行检测（集中式模式）
        if MAC == "NoAddress":
            rid = 390                                               # 3m/2
            cSlice = 2117                                           # 16m/2 2117
        for i in self._mics:
            self._plotFile[0].append(None)                          # mics' data in one channel
            self._plotFile[1].append(None)                          # mics' data in the other channel
            self._micData.append(MicData(i, thdz, thdf, cSlice, rid))


    def reset(self):
        """
            重置背景信号
            return: "OK" or terminate
        """ 
        logger.info(self._MAC+" 正在重置...")
        if not os.path.exists(self._PATH1): os.makedirs(self._PATH1)
        
        out = os.popen("python3 playRec.py "+self._PATH1 +" 5 "+self._MAC).read().replace("\n", "")
        if out=="OK":
            logger.info(self._MAC+" 重置成功！")
        else:
            logger.info(self._MAC+" 重置失败！")
            sys.exit()
        return out


    def RecordAudio(self, PATH):
        """
            采集音频数据,中间会根据服务器的情况进行重置
            return: null
        """
        if not os.path.exists(PATH): os.makedirs(PATH)

        if self._to_reset == True:
            self.reset()
            self._to_reset = False
        
        out = os.popen("python3 playRec.py "+PATH +" 3 "+self._MAC).read()
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
        
        self.file.writelines("<<<<<<<<\n")
        for i in range(len(self._mics)):
            # 储存数据到 Data.txt
            print(i+1 ,self._micData[i]._process_result[1],self._micData[i]._process_result[2])
            self.file.writelines(str(self._micData[i]._process_result[0])+"---")
            self.file.writelines("mx:"+("%.2f"%self._micData[i]._process_result[1])+
                                 ",mi:-"+("%.2f"%abs(self._micData[i]._process_result[2]))+"\n")

            # 比较和阈值的关系; count 表示检测结果为"empty"的麦克风数量
            if (self._micData[i]._process_result[1] <= self._thdz 
                and abs(self._micData[i]._process_result[2]) <= self._thdf):
                count+=1
            self._micData[i]._process_result.clear()                                        # clear original data
            
            for k in range(2):      # two speakers
                if len(self._micData[i]._x_y) and k*2 < len(self._micData[i]._x_y) :        # 确保当前麦克风对应的声道已储存到有效数据
                    # 输出图像
                    #Debug_plot(self._micData[i], k)
                    
                    '''
                    for d in self._micData[i]._x_y[k*2+1][1]:
                        self._plotFile[k][self._micData[i]._micnum-1].write(("%.5f"%d)+",")
                    self._plotFile[k][self._micData[i]._micnum-1].write("\n")
                    '''
                    #print(self._micData[i]._micnum,self._micData[i]._x_y[k*2][0])
            #self._micData[i]._x_y.clear()
        
        Debug_plot1(self._micData)
        plt.show()
        for i in range(0,4):
            self._micData[i]._x_y.clear()
        sys.exit()
        #print(count)    
        return count
        

    def detect(self):
        """
            检测程序：调用录音等程序，判断环境是否发生波动
            return: the outcome of detecting
        """
        # 储存左右声道随时间的图像数据
        for k in range(2):
            f_index = 1
            part_path = "MIC/"+self._MAC+"/LMic"                # self._plotFile[0]对应 LMic 的数据
            if k == 1: part_path = "MIC/"+self._MAC+"/RMic"     # self._plotFile[1]对应 RMic 的数据
            if not os.path.exists(part_path): os.makedirs(part_path)
            for k1 in range(len(self._plotFile[k])):
                self._plotFile[k][k1] = open(part_path+"/data"+str(f_index)+".txt", mode="a+")      # 按照不同的麦克风进行存储，原则上 k1 对应 id=k1+1 的麦克风
                f_index += 1
        
        # 储存每个麦克风检测到的最大变化值（包含两个声道）
        self.file=open("MIC/Data-"+self._MAC+".txt",mode="a+")
        self.file.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\n")
        
        self.RecordAudio(self._PATH2)
        count = self.forEveryMic(self._PATH1, self._PATH2)
        # 
        if count < 3:       # 有至少2个麦克风检测到变化
            logger.info(self._MAC+" 检测到环境波动...")
            time.sleep(3)
            
            scount=0        # 稳定状态计数
            postfix = 1
            PATH2=self._PATH2
            self.RecordAudio(PATH2)
            while scount < self._stability_count:       # 判断环境是否稳定，稳定状态连续达到设定的次数
                logger.info(self._MAC+" 持续检测中...")
                PATH3=self._PATH2+str(postfix)
                self.RecordAudio(PATH3)
                count = self.forEveryMic(PATH2, PATH3)
                if count < 3:  scount = 0               # 再次出现波动时，稳定状态计数清零
                PATH2=PATH3
                postfix+=1
                scount+=1
            count = self.forEveryMic(self._PATH1, PATH2)
    
        if count >= 3: self._outcome="empty"    
        else: self._outcome="nonempty"
        logger.info(self._MAC+f" 检测结果：{self._outcome}")

        # 关闭文件
        self.file.writelines(self._outcome+"\n")
        self.file.close()
        for k in range(2):
            for f in self._plotFile[k]:
                f.close()
        time.sleep(2)

        return self._outcome
        

if __name__ == "__main__":
    """ for testing """
    
    Radar=URadar(MAC="4C:65:A8:56:A7:B3")#)   #0C:70:89:6E:18:E0")#"81:0D:F6:34:02:1B")#4C:65:A8:57:BE:4C
    reset_choice = input("reset_or_not:")
    if reset_choice == "1": Radar.reset()

    # 持续测试
    while True: Radar.detect()