'''
import os

out = os.popen('python3 detect.py empty 0 0' ).read().replace('\n', '')
out_1 = os.popen('python3 forObject.py empty barrier 0 0' ).read().replace('\n', '')
print(out_1)
 
out1 = os.popen('python3 detect.py empty1 2 1' ).read().replace('\n', '')
out1_1 = os.popen('python3 forObject.py empty1 barrier1 2 1' ).read().replace('\n', '')
print(out1_1)

import datetime
import time

def subtime(time1,time2):
    time1=datetime.datetime.strptime(time1,"%Y-%m-%d %H:%M:%S")
    time2=datetime.datetime.strptime(time2,"%Y-%m-%d %H:%M:%S")
    return time2-time1

datetime.timedelta(minutes = 30) 


time1=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
time2=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(time1)
while True:
    time2=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if subtime(time1,time2) >= datetime.timedelta(minutes =1) :
        print(time2)
        time1=time2

import os
import shutil
for i in range(1,7):
    os.remove(''.join(['empty2/','mic',str(i),'.wav']))
    shutil.copyfile(''.join(['empty/','mic',str(i),'.wav']),''.join(['empty2/','mic',str(i),'.wav']))
'''
import os
import wave
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from pylab import *
from scipy import interpolate
'''
Fs, y = wavfile.read('audio/20k-22k10ms.wav')
plt.plot(y)
plt.show()

low = 20000
high = 22000
time = 10/1000 # 10ms
rate = 48000
t = np.arange(0, 0*rate+time, 1/rate)
c= np.arange(low, high, 2000/480)

plt.plot(t,c)
plt.xlim(0,0.51)
plt.xlabel('Time/s')
plt.ylabel('Frequency/Hz')
plt.title('Time-Frequency of single period ')
plt.show()
'''
MicD=np.zeros(6)
MicD1=MicD.copy()
print(MicD1.size)
if MicD1[0]==0:
    print(1)



