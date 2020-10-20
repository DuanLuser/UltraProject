# -*- encoding: utf-8 -*-
'''
@File    :   record.py
@Time    :   2020/09/22 19:46:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import pyaudio
import sys
import wave
import numpy as np
import os
import time
import contextlib


@contextlib.contextmanager
def ignore_stderr(path, time):
    '''
        ignore warnings
        return: null
    '''
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        recordaudio(path, time)
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

def recordaudio(path, time):
   os.system(f"arecord -D sysdefault:CARD=seeed4micvoicec -d {time} -f dat -r 44100 -c 4 -t wav {path}/mic.wav")
   
if __name__=="__main__":
    
    ignore_stderr(sys.argv[1], sys.argv[2])#
