import pyaudio
import sys
import wave
import numpy as np
import os
import time
import contextlib


@contextlib.contextmanager
def ignore_stderr(path,index,time):
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
    PATH = path

    RESPEAKER_RATE = 44100
    RESPEAKER_CHANNELS = 8
    RESPEAKER_WIDTH = 2
    # run getDeviceInfo.py to get index
    RESPEAKER_INDEX = int(index)  #0,0; 2 refer to input device id
    CHUNK = 1024
    RECORD_SECONDS = int(time) # reset:5; detect:3
    WAVE_OUTPUT_FILENAME = []

    for i in range(6):
        WAVE_OUTPUT_FILENAME.append([])

    for i in range(6):
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
    for i in range(6):
        frames.append([])

    for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        # extract channel 0 data from 8 channels, if you want to extract channel 1, please change to [1::8]
        for j in range(6):
            x=np.frombuffer(data,dtype=np.int16)[j::8]
            frames[j].append(x.tostring())
    
    #print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    for i in range(6):
        wf = wave.open(WAVE_OUTPUT_FILENAME[i], 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
        wf.setframerate(RESPEAKER_RATE)
        wf.writeframes(b''.join(frames[i]))
        wf.close()
    print('OK')
    return 'OK'

if __name__=="__main__":
    #ignore_stderr('Empty',2, 5)#sys.argv[1], sys.argv[2])
    #if sys.argv[1]=='None':
    #    time.sleep(int(sys.argv[3]))
    #else:
    ignore_stderr(sys.argv[1], sys.argv[2], sys.argv[3])#'Barrier/barrier',2,3)#
    #sys.exit(recordaudio('Empty',2))
