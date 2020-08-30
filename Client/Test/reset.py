import os, sys, time
from playRec import TdmaPlay

#from play import playprompt

def main():
    
    file='Empty' #sys.argv[1] #input("FileName:")
    if not os.path.exists(file):
        os.makedirs(file)
    #playprompt("网络连接成功.wav")
    #time.sleep(2)
    tplay=TdmaPlay()
    out = tplay.play_and_record(file,5)
     
    print(out)
    
    return out

if __name__=="__main__":
    sys.exit(main())