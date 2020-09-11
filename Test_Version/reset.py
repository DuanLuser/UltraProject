import os, sys, time

#from play import playprompt

def main():
    
    file='Empty' #sys.argv[1] #input("FileName:")
    if not os.path.exists(file):
        os.makedirs(file)
    #playprompt("网络连接成功.wav")
    #time.sleep(2)
    out = os.popen('python3 playRec.py '+file +' 5').read().replace('\n', '')  
    print(out)
    
    return out

if __name__=="__main__":
    sys.exit(main())