
import os, sys
import time, wave
import datetime

import pyaudio
import threading
import numpy as np
import sounddevice as sd

from record import ignore_stderr
from setvolume import setvol


def play_with_Usb(audio):
    
    os.system("aplay -D plughw:0,0 "+audio)
    #os.system("aplay -D bluealsa:DEV=4C:65:A8:56:A7:B3,PROFILE=A2DP "+audio)


class TdmaPlay:
    
    expected_channel: list = []
    def __init__(self):
        self.expected_channels=[["seeed",1], #record
            #["USB Audio Device",0],
        ]
 
    def get_device_number(self, index_info):
 
        index, info = index_info
    
        for item in self.expected_channels:
            if item[0] in info["name"]:
                item[1]=index
                return index
        return False
    
    def good_filepath(self, path):
        return str(path).endswith(".wav") and (not str(path).startswith("."))
    
    def playrec(self, Path, Second):
        
        cwd = ""
        if Second=="5":
            cwd="audio/reset/"
        if Second=="3":
            cwd="audio/detect/"
        if Second=="2":
            cwd="audio/test/"   
        sound_file_paths = [
            os.path.join(cwd, path) for path in sorted(filter(lambda path: self.good_filepath(path), os.listdir(cwd)))]
        
        list(filter(lambda x: x is not False,map(self.get_device_number,[index_info for index_info in enumerate(sd.query_devices())])))
        
        # playing
        tp = threading.Thread(target=play_with_Usb, args=[sound_file_paths[0]])
        tp.start()
        
        # recording
        tr = threading.Thread(target=ignore_stderr, args=[Path, Second])
        tr.start()
        
        tp.join()
        tr.join()
        print("OK")
        return "OK"

def playprompt(wav):
    """
       播放提示音
       return: null
    """
    #setvol("70%")
    #os.system('aplay audio/prompt/'+ wav)  # the default port is USB audio card
    hour = datetime.datetime.now().hour
    #if hour >= 7 and hour <= 20:
    #    os.system('aplay -D sysdefault:CARD=Device audio/prompt/'+ wav)  # corresponding USD audio card
    '''
    if wav == "网络连接成功.wav":
        time.sleep(2)
    elif wav == "网络连接失败，正在重新连接.wav":
        time.sleep(3)
    elif wav == "障碍物已移除，谢谢配合.wav":
        time.sleep(3)
    elif wav == "请注意，消防通道禁止阻塞，请立即移除障碍物.wav":
        time.sleep(5)
    '''
    setvol("90%") 
            

if __name__ == "__main__":
    
    #playprompt("网络连接成功.wav")
    
    tplay=TdmaPlay()
    sys.exit(tplay.playrec(sys.argv[1], sys.argv[2]))
    
