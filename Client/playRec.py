import os, sys
import time
import wave

import pyaudio
import soundfile
import threading
import sounddevice as sd
import numpy as np

from record import ignore_stderr

def play_wav_on_index(audio_data, index):
    """
    Play an audio file given as the result of `load_sound_file_into_memory`
    :param audio_data: A two-dimensional NumPy array
    :param index:
    :return: None, returns when the data has all been consumed
    """
    sd.default.device[1] = index
    sd.play(audio_data, samplerate=44100, blocking=True)
    #sd.wait()

class TdmaPlay:
    
    Fs: int = 44100
    DATA_TYPE:str = "float32"
    
    expected_channel: list = []
    sound_card_indices: list = []
    
    def __init__(self):
        self.expected_channels=[["seeed-8mic-voicecard",1], #record
            ["USB Audio Device",0],
            #["upmix",2]#play
            ]

    def load_sound_file_into_memory(self, path):
        """
        Get the in-memory version of a given path to a wav file
        :param path: wav file to be loaded
        :return: audio_data, a 2D numpy array
        """
 
        audio_data, self.Fs = soundfile.read(path, dtype=self.DATA_TYPE)
        return audio_data
 
 
    def get_device_number(self, index_info):
        """
        Given a device dict, return True if the device is one of our USB sound cards and False if otherwise
        :param index_info: a device info dict from PyAudio.
        :return: True if expected card, False if otherwise
        """
 
        index, info = index_info
    
        for item in self.expected_channels:
            if item[0] in info["name"]:
                item[1]=index
                if "seeed-8mic" not in item[0]:
                    self.sound_card_indices.append(index)
                return index
        return False
        
    def good_filepath(self, path):
        """
        Macro for returning false if the file is not a non-hidden wav file
        :param path: path to the file
        :return: true if a non-hidden wav, false if not a wav or hidden
        """
        return str(path).endswith(".wav") and (not str(path).startswith("."))
    
    def playrec(self, Path, Second):
        cwd = ""
        
        if Second=="5":
            cwd="audio/reset/"
        if Second=="3":
            cwd="audio/detect/"
        self.sound_card_indices.clear()
        
        sound_file_paths = [
            os.path.join(cwd, path) for path in sorted(filter(lambda path: self.good_filepath(path), os.listdir(cwd)))]
        
        #print("Discovered the following .wav files:", sound_file_paths)
 
        files = [self.load_sound_file_into_memory(path) for path in sound_file_paths]
 
        #print("Files loaded into memory, Looking for devices.")
        #print(sd.query_devices())
 
        list(filter(lambda x: x is not False,map(self.get_device_number,[index_info for index_info in enumerate(sd.query_devices())])))
 
        #print("Discovered the following sound devices", self.sound_card_indices)
        #print(self.expected_channels)
        running = True
 
        if not len(self.sound_card_indices) > 0:
            running = False
            #print("No audio devices found, stopping")
 
        if not len(files) > 0:
            running = False
            #print("No sound files found, stopping")
        
        if running:
            #print("Playing files")
            threads = [threading.Thread(target=play_wav_on_index, args=[file_path, index])
                   for file_path, index  in zip(files, self.sound_card_indices)]
            
            # playing
            for thread in threads:
                thread.start()
            # recording
            t=threading.Thread(target=ignore_stderr, args=[Path, self.expected_channels[0][1], Second])
            t.start()
            
            for thread, device_index in zip(threads, self.sound_card_indices):
                #print("Waiting for device", device_index, "to finish")
                thread.join()
            t.join()
            
            return "OK"

# 播放提示音
def playprompt(wav):
    #os.popen('aplay -D "plughw:2,0" audio/prompt/'+ wav)
    if wav == "网络连接成功.wav":
        time.sleep(2)
    elif wav == "网络连接失败，正在重新连接.wav":
        time.sleep(3)
    elif wav == "障碍物已移除，谢谢配合.wav":
        time.sleep(3)
    elif wav == "请注意，消防通道禁止阻塞，请立即移除障碍物.wav":
        time.sleep(5)
            
'''
def play_and_record(path, second): # 线程报错
    tplay=TdmaPlay()
    out = tplay.playrec(path, second)
    return out
'''

if __name__ == "__main__":
    tplay=TdmaPlay()
    sys.exit(tplay.playrec(sys.argv[1], sys.argv[2]))
    
