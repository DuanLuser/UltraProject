import os
import time

def setvol(val):
    info_list = os.popen("amixer controls").read().split("\n")
    for numid_info in info_list:
        if "Speaker Playback Volume" in numid_info:
            output = os.popen("amixer cset "+ numid_info +" "+val).read()
            #print(output)

if __name__ =="__main__":

    setvol("90%")
