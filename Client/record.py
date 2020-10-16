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
def ignore_stderr(path,index,time):
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
        recordaudio(path, index, time)
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

def recordaudio(path, index, time):
    '''
        record the sound
        return: "OK" or null
    '''
    
    PATH = path
    RESPEAKER_RATE = 44100
    RESPEAKER_CHANNELS = 4
    RESPEAKER_WIDTH = 2
    # run getDeviceInfo.py to get index
    RESPEAKER_INDEX = int(index)  # refer to input device id
    CHUNK = 1024
    RECORD_SECONDS = int(time)    # reset:5; detect:3
    WAVE_OUTPUT_FILENAME = []

    for i in range(4):
        WAVE_OUTPUT_FILENAME.append([])

    for i in range(4):
        WAVE_OUTPUT_FILENAME[i]=''.join([PATH,"/mic",str(i+1),".wav"])

    p = pyaudio.PyAudio()

    stream = p.open(
            rate=RESPEAKER_RATE,
            format=p.get_format_from_width(RESPEAKER_WIDTH),
            channels=RESPEAKER_CHANNELS,
            input=True,
            input_device_index=RESPEAKER_INDEX,)

    #print("* recording")

    frames = []
    for i in range(4):
        frames.append([])

    for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        # extract channel 0 data from 8 channels, if you want to extract channel 1, please change to [1::8]
        for j in range(4):
            x=np.frombuffer(data,dtype=np.int16)[j::4]
            frames[j].append(x.tostring())
    
    #print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    for i in range(4):
        wf = wave.open(WAVE_OUTPUT_FILENAME[i], 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
        #print('here', p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
        wf.setframerate(RESPEAKER_RATE)
        wf.writeframes(b''.join(frames[i]))
        wf.close()
    print('OK')
    return 'OK'

if __name__=="__main__":
    
    ignore_stderr(sys.argv[1], sys.argv[2], sys.argv[3]) #'Barrier/barrier',2,3)#
