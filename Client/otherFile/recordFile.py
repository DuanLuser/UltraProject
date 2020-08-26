import threading

import play
import record
import sys

def recordWAV(PATH):
    threads=[]
    threads.append(threading.Thread(target=play.playaudio, args=(0,)))
    threads.append(threading.Thread(target=record.recordaudio, args=(PATH,2,)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

if __name__=="__main__":
    sys.exit(recordWAV('empty'))
