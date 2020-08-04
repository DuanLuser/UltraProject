import os

os.system('aplay -D "plughw:0,0" audio/20k-23k30ms.wav')

'''
import pyaudio
import wave

chunk=1024  #1024kb

def play():
    wf=wave.open("10ms.wav",'rb')
    p=pyaudio.PyAudio()
    stream=p.open(format=p.get_format_from_width(wf.getsampwidth()),
                  channels=wf.getnchannels(),
                  rate=wf.getframerate(),
                  output=True)
 
    data = wf.readframes(chunk)  # 读取数据
    print(data)
    while len(data)>0:  # 播放  
        stream.write(data)
        data = wf.readframes(chunk)
        print(data)
    stream.stop_stream()   # 停止数据流
    stream.close()
    p.terminate()
    
play()
'''