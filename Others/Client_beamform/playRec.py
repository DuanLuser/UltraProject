# -*- encoding: utf-8 -*-
'''
@File    :   playRec.py
@Time    :   2020/09/22 19:57:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import os, sys
import time, wave
import sounddevice as sd
from record import ignore_stderr


class TdmaPlay:
    
    Fs: int = 44100
    DATA_TYPE:str = "float32"
    
    expected_channel: list = []
    
    def __init__(self):
        self.expected_channels=[["seeed-8mic-voicecard",1], #record
            #["USB Audio Device",0],
            #["upmix",2]#play
            ]
 
 
    def get_device_number(self, index_info):
        """
        Given a device dict, return True if the device is one of our USB sound cards and False if otherwise
        param index_info: a device info dict from PyAudio.
        return: True if expected card, False if otherwise
        """
 
        index, info = index_info
    
        for item in self.expected_channels:
            if item[0] in info["name"]:
                item[1]=index
                return index
        return False
        
    
    def playrec(self, Path, Second):

        list(filter(lambda x: x is not False,map(self.get_device_number,[index_info for index_info in enumerate(sd.query_devices())])))
        #print(self.expected_channels)
        # recording
        ignore_stderr(Path, self.expected_channels[0][1], Second) 
        #return out


def playprompt(wav):
    """
        播放提示音
        return: null
    """
    #os.popen('aplay audio/prompt/'+ wav)  # the default port is USB audio card
    if wav == "网络连接成功.wav":
        time.sleep(2)
    elif wav == "网络连接失败，正在重新连接.wav":
        time.sleep(3)
    elif wav == "障碍物已移除，谢谢配合.wav":
        time.sleep(3)
    elif wav == "请注意，消防通道禁止阻塞，请立即移除障碍物.wav":
        time.sleep(5)

if __name__ == "__main__":
    
    tplay=TdmaPlay()
    sys.exit(tplay.playrec(sys.argv[1], sys.argv[2]))
    
