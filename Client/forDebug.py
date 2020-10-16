import os, time, shutil
import datetime
import matplotlib.pyplot as plt

class Debug:
    """
        储存数据，输出图像，调试用
    """
    _plotLprefix = "MIC/LMic/data"
    _plotRprefix = "MIC/RMic/data"
    _threshdFile = "MIC/Data.txt"
    _plotStream = [[]for i in range(2)]

    _targetEprefix = "MIC/Wanted/empty"
    _targetBprefix = "MIC/Wanted/barrier"

    def __init__(self)->None:
        """
            初始化plot数据输出流，分左右声道
        """
        if not os.path.exists("MIC/LMic"): os.makedirs("MIC/LMic")
        if not os.path.exists("MIC/RMic"): os.makedirs("MIC/RMic")
        for i in range(0,4):
            self._plotStream[0].append(None)
            self._plotStream[1].append(None)
        
        plt.figure(figsize=(12, 12))

    def openFile(self):
        """
            打开要储存的文件
        """
        for k in range(0,4):
            self._plotStream[0][k] = open(self._plotLprefix+str(k+1)+".txt", mode="a+")
            self._plotStream[1][k] = open(self._plotRprefix+str(k+1)+".txt", mode="a+")

        self._threshdFile=open("MIC/Data.txt",mode="a+")
        self._threshdFile.writelines(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\n")

    def closeFile(self):
        """
            关闭要储存的文件
        """
        self._threshdFile.close()
        for k in range(2):
            for file in self._plotStream[k]:
                file.close()

    def save2threshdFile(self, mic, mx, mi):
        """
            储存每个麦克风的最大与最小阈值
        """
        self._threshdFile.writelines(str(mic)+"---")
        self._threshdFile.writelines("mx:"+("%.2f"%mx)+",mi:-"+("%.2f"%abs(mi))+"\n")
        
    def saveSep2threshdFile(self):
        """
            输出分隔符
        """
        self._threshdFile.writelines("<<<<<<<<<<\n")

    def saveOut2threshdFile(self, outcome):
        """
            储存检测结果
        """
        self._threshdFile.writelines(outcome+"\n")

    def save2plotStream(self, data, mic, channel):
        """
            一行数据（data）代表某时刻的检测结果
        """
        for d in data:
            self._plotStream[channel][mic-1].write(("%.5f"%d)+",")
        self._plotStream[channel][mic-1].write("\n")

    def save_valued_data(self, empty_data, barrier_data):
        """
            储存大于一定阈值的完整数据（empty与barrier）
        """
        t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_efile = self._targetEprefix+t
        target_bfile = self._targetBprefix+t
    
        if not os.path.exists(target_efile): 
            os.makedirs(target_efile)
        if not os.path.exists(target_bfile): 
            os.makedirs(target_bfile)
        for i in range(1,5):
            shutil.copyfile(''.join([empty_data,'/mic',str(i),'.wav']),\
                ''.join([target_efile+'/mic',str(i),'.wav']))
            shutil.copyfile(''.join([barrier_data,'/mic',str(i),'.wav']),\
                ''.join([target_bfile+'/mic',str(i),'.wav']))

    def plotData(self, Data):
        plt.clf()               # clear previous data
        plt.ion()
        plt.show()
        for i in range(0,4):
            plt.subplot(4,1,i+1)
            plt.ylim(0,0.2)
            plt.plot(Data[i]._x_y[0][0], Data[i]._x_y[0][1], linewidth=1)
            plt.plot(Data[i]._x_y[1][0], Data[i]._x_y[1][1], c="red",linewidth=1)
            plt.title("mic"+str(Data[i]._micnum))
            label=["Empty","The other"]
            plt.legend(label, loc =0)
        plt.xlabel("Distance(m)")
        plt.ylabel("Correlation")
        plt.pause(0.001)

