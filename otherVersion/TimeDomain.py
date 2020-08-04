import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

sampling_freq, audio = wavfile.read('20-23k50ms/0325empty1/mic4.wav')   # 读取文件

Nsamps=len(audio)
fft_signal = abs(np.fft.fft(audio))[0: int(Nsamps/2)-1]
f=sampling_freq*np.arange(0, Nsamps/2-1)/Nsamps


# 绘制语音信号的
plt.figure()
plt.plot(f, fft_signal, color='blue')
plt.xlabel('Freq (in Hz)')
plt.ylabel('Amplitude')
plt.show()