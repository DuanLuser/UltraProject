import os
import time
time.sleep(3)

def setvol(val):
    info_list = os.popen("amixer controls").read().split("\n")
    for numid_info in info_list:
        if "Speaker Playback Volume" in numid_info:
            #print(numid_info)
            output = os.popen("amixer cset "+ numid_info +" "+val).read()
            #print(output)
