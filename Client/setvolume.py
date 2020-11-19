import os
import time
time.sleep(3)

"""设置音量"""
def setvol(val):
    info_list = os.popen("amixer controls").read().split("\n")
    for numid_info in info_list:
        if "Playback Volume" in numid_info:
            #print(numid_info)
            ouput = os.popen("amixer cset "+ numid_info +" "+val).read()

if __name__=="__main__":
    setvol("98%")