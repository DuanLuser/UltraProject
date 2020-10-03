
import os, sys
import time, wave

import pyaudio
import threading
import numpy as np
import sounddevice as sd

from record import ignore_stderr
from setvolume import setvol

def play_with_buletooth(MAC, audio):
    out = os.popen("aplay -D bluealsa:DEV="+MAC+",PROFILE=A2DP "+audio).readlines()
    
class TdmaPlay:
    
    expected_channel: list = []
    def __init__(self):
        self.expected_channels=[["seeed",1], #record
            #["USB Audio Device",0],
            #["upmix",2]#play
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
    
    def playrec(self, Path, Second, MAC):
        
        cwd = ""
        if Second=="5":
            cwd="audio/reset/"
        if Second=="3":
            cwd="audio/detect/"
        sound_file_paths = [
            os.path.join(cwd, path) for path in sorted(filter(lambda path: self.good_filepath(path), os.listdir(cwd)))]
        
        list(filter(lambda x: x is not False,map(self.get_device_number,[index_info for index_info in enumerate(sd.query_devices())])))
        
        # playing
        tp = threading.Thread(target=play_with_buletooth, args=[MAC, sound_file_paths[0]])
        tp.start()
        
        # recording
        tr = threading.Thread(target=ignore_stderr, args=[Path, self.expected_channels[0][1], Second])
        tr.start()
        
        tp.join()
        tr.join()

        return "OK"

def playprompt(wav):
    """
       播放提示音
       return: null
    """
    #setvol("70%")
    #os.system('aplay audio/prompt/'+ wav)  # the default port is USB audio card
    #os.system('aplay -D plughw:0,0 audio/prompt/'+ wav)  # corresponding USD audio card
    if wav == "网络连接成功.wav":
        time.sleep(2)
    elif wav == "网络连接失败，正在重新连接.wav":
        time.sleep(3)
    elif wav == "障碍物已移除，谢谢配合.wav":
        time.sleep(3)
    elif wav == "请注意，消防通道禁止阻塞，请立即移除障碍物.wav":
        time.sleep(5)
    #setvol("100%") 
            

if __name__ == "__main__":
    tplay=TdmaPlay()
    sys.exit(tplay.playrec(sys.argv[1], sys.argv[2], sys.argv[3]))#"Empty","5","FC:58:FA:F7:D5:EF"))#
    
