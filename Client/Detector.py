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

import warnings
warnings.filterwarnings("ignore")

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import mpl_toolkits.mplot3d

logger = logzero.setup_logger("client", level=logging.INFO)

class URadar:
    '''封装类'''
    _thdz: float             #7.5           # 5.5 
    _thdf: float             #8.5           # 6.5
   
    _outcome: str
    _prompt: str = 'None'

    _mics=[1,3,4,5,6]
    _stability_count=2
    _reset_order=False
    _micData = []
    
    _PATH1='Empty'
    _PATH2='Barrier/barrier'
    
    file=None
    
    def __init__(self, thdz=5, thdf=6) -> None:
        self._thdz=thdz
        self._thdf=thdf
        for i in self._mics:
            self._micData.append(MicData(i, thdz, thdf))

    def reset(self):
        logger.info("正在重置...")
        if not os.path.exists(self._PATH1):
            os.makedirs(self._PATH1)
            
        #out = self.tplay.play_and_record(self._PATH1,5)
        #out = play_and_record(self._PATH1,5)
        out = os.popen('python3 playRec.py '+self._PATH1 +' 5').read().replace('\n', '')
        if out=="OK":
            logger.info("重置成功！")
        else:
            logger.info("重置失败！")
        return out
    

    def forEveryMic(self, PATH1, PATH2):
        '''对每个mic收集的数据进行process处理，并行'''
        count = 0
        
        Threads=[]
        for i in range(len(self._mics)):
            t = Thread(target=self._micData[i].process, args=(PATH1, PATH2, self._mics[i],))
            t.start()
            Threads.append(t)
        for t in Threads:
            t.join()
        
        sEmpty=np.zeros(self._micData[0]._cSlice*2)
        sOther=np.zeros(self._micData[0]._cSlice*2)
        self.file.writelines('<<<<<<<<\n')
        for i in range(len(self._mics)):
            self.file.writelines(str(self._micData[i]._process_result[0])+'---')
            self.file.writelines('mx:'+('%.2f'%self._micData[i]._process_result[1])+',mi:-'+('%.2f'%abs(self._micData[i]._process_result[2]))+'\n')
            if self._micData[i]._process_result[1] <= self._thdz and abs(self._micData[i]._process_result[0]) <= self._thdf: # 阈值的设定？ empty    有待检验
                count+=1
            self._micData[i]._process_result.clear()
            
            for k in range(1):
                plt.figure()
                label=['Empty','The other']
                #plt.plot(x,y,'o')
                plt.ylim(0,1)
                plt.plot(self._micData[i]._x_y[k*2][0],self._micData[i]._x_y[k*2][1], linewidth=1)
                #plt.plot(x1,y1,'*')
                plt.plot(self._micData[i]._x_y[k*2+1][0],self._micData[i]._x_y[k*2+1][1], c='red',linewidth=1)
                plt.legend(label, loc =0) 
                plt.title(''.join(['mic',str(self._micData[i]._micnum)]))
                #plt.title('Comparison')
                #plt.title('Envelope Detection')
                plt.xlabel('Distance(m)')
                plt.ylabel('Correlation')
                if k==0 :
                    sEmpty+=self._micData[i]._x_y[0][1]
                    sOther+=self._micData[i]._x_y[1][1]
                #print(self._micData[i]._micnum,self._micData[i]._x_y[k*2][0])
            self._micData[i]._x_y.clear()

        plt.figure()
        label=['Empty','The other']
        #plt.plot(x,y,'o')
        plt.ylim(0,1)
        plt.plot(sEmpty/len(self._mics), linewidth=1)
        #plt.plot(x1,y1,'*')
        plt.plot(sOther/len(self._mics), c='red',linewidth=1)
        plt.legend(label, loc =0) 
        plt.title("allmic")
        #plt.title('Comparison')
        #plt.title('Envelope Detection')
        plt.xlabel('Distance(m)')
        plt.ylabel('Correlation')
            
        plt.show()
            
        #print(count)    
        return count

    def RecordAudio(self, PATH):
        '''采集音频数据'''
        if not os.path.exists(PATH): 
            os.makedirs(PATH)
        out=''
        if self._reset_order:
            self.reset()
            self._reset_order=False
            
        #存在提示音要占据音频端口的情况，先播放提示音
        if self._prompt != 'None':
            #playprompt(self._prompt)
            print('prompt',self._prompt)
            self._prompt='None'
        
        #out = self.tplay.play_and_record(PATH,3)
        #out = play_and_record(PATH,3)
        #out = os.popen('python3 playRec.py '+PATH +' 3').read().replace('\n', '')
        #print(out)
        

    def detect(self):
        
        # 记录数据
        self.file=open('MIC/Data.txt',mode='a+')
        self.file.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n')
      
        
        self.RecordAudio(self._PATH2)
        count = self.forEveryMic(self._PATH1, self._PATH2)
        # 
        if count < 3: # 3
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
                count = self.forEveryMic(PATH2, PATH3)
                if (scount==0 and count < 3) or (scount==1 and count < 3): #5
                    scount = 0
                PATH2=PATH3
                postfix+=1
                scount+=1
            count = self.forEveryMic(self._PATH1, PATH2)
    
        if count >= 3: # 4
            self._outcome='empty'
            #if count >=5 :
            #    for i in range(1,7):
            #        os.remove(''.join(['empty/mic',str(i),'.wav']))
            #        shutil.copyfile(''.join([PATH2,'/mic',str(i),'.wav']),''.join(['empty/mic',str(i),'.wav']))
        else:
            self._outcome='nonempty'
            #self._outcome='empty'
        logger.info(f"检测结果：{self._outcome}")
        self.file.writelines(self._outcome+'\n')
        self.file.close()
        time.sleep(2)
        
        return self._outcome
    
def continuelly(Radar):
    while True:
        Radar.detect()
        

if __name__ == "__main__":
    # 启动通讯客户端
    # ws = WebsocketClient()
    # ws.server_url = "ws://localhost:2714"
    # ws.device_id = "2"
    # ws.Start()
    Radar=URadar()
    reset_choice='0'#input('reset_or_not:')
    if reset_choice=='1':
        Radar.reset()
    while True:
        Radar.detect()