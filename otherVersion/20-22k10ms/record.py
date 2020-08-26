import pyaudio
import sys
import wave
import numpy as np

PATH = sys.argv[1]

RESPEAKER_RATE = 48000
RESPEAKER_CHANNELS = 8
RESPEAKER_WIDTH = 2
# run getDeviceInfo.py to get index
RESPEAKER_INDEX = int(sys.argv[2])  #1,0; 2 refer to input device id
CHUNK = 1024
RECORD_SECONDS = 5
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

