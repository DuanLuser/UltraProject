import os
import sys
import threading

import play
import record

def main():
    file='Empty' #sys.argv[1] #input("FileName:")
    if not os.path.exists(file):
        os.makedirs(file)
    out = os.popen('sh runforDetect.sh '+file +' 0 0').read().replace('\n', '')# 0 0
    '''
    threads=[]
    threads.append(threading.Thread(target=play.playaudio, args=(0,)))
    threads.append(threading.Thread(target=record.recordaudio, args=('empty',2,)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    '''
    print(out)
    return out

if __name__=="__main__":
    sys.exit(main())