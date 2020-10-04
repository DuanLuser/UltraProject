# -*- encoding: utf-8 -*-
'''
@File    :   Manager.py
@Time    :   2020/10/3 19:12:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import os, sys
import time, wave
import logging, logzero
from Detector import URadar
from playRec import playprompt

import warnings
warnings.filterwarnings("ignore")


class manager:
    """ 封装类 
    管理各个区域的蓝牙输出与检测
    """
    _Radars = []
    _MACs = ["FC:58:FA:F7:D5:EF","81:0D:F6:34:02:1B"]
    _prompt = "None"

    def __init__(self) -> None:
        thdz=[0.3, 0.3]
        thdf=[0.35, 0.35]
        for i in range(len(self._MACs)):
            self._Radars.append(URadar(thdz[i], thdf[i], self._MACs[i]))
            # 为不同的蓝牙设备创建文件夹
            if not os.path.exists("recordData/"+self._MACs[i]): 
                os.makedirs("recordData/"+self._MACs[i])

    def reset_all(self):
        """
            重置背景信号
            return: "OK" or null
        """
        for radar in self._Radars:
            out = radar.reset()
            print(out)

        return "OK"     #

    def detect_by_turns(self):

        #存在提示音要占据音频端口的情况，先播放提示音
        if self._prompt != "None":
            playprompt(self._prompt)
            print("prompt",self._prompt)
            self._prompt="None"

        final_outcome = "empty"
        for radar in self._Radars:
            outcome = radar.detect()
            if outcome =="nonempty":
                final_outcome = "nonempty"
                break
        return final_outcome

if __name__ == "__main__":
    """ for testing """

    all_radar = manager()
    reset_choice = input("reset_or_not:")
    if reset_choice == "1":
        all_radar.reset_all()
    while True:
        out = all_radar.detect_by_turns()
        print(out)
    
    



