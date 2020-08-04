import os
import random
import time
import datetime
from socket import *
from multiprocessing import Pool

order=['connect','detect']

limit = datetime.timedelta(minutes = 30)

def subtime(time1,time2):
    time1=datetime.datetime.strptime(time1,"%Y-%m-%d %H:%M:%S")
    time2=datetime.datetime.strptime(time2,"%Y-%m-%d %H:%M:%S")
    return time2-time1

def connect():
    global reset_time
    while True:
        try:
            while True:
                choice=int(input('choice:'))
                data = order[choice]  
                if data=='connect':
                    #client.send('connectOK'.encode(encoding='utf-8'))
                    out_r = os.popen('python3 detect.py').read().replace('\n', '')
                    print(out_r)
                    if out_r == 'OK':
                        #client.send('resetOK'.encode(encoding='utf-8'))
                        reset_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                elif data=='detect':
                    #client.send('detectOK'.encode(encoding='utf-8'))
                    while True:
                        out_o = os.popen('python3 forObject.py').read().replace('\n', '')
                        out_o = out_o.replace('OK', '')
                        #if out2 != 'empty' and out2 != 'nonempty':
                        #    out2='default'
                        print(out_o)
                        #client.send(out_o.encode(encoding='utf-8'))
                        # reset regularly (30 minutes)
                        now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if out_o == 'empty' and subtime(reset_time,now_time) >= limit :
                            out_r1 = os.popen('python3 detect.py').read().replace('\n', '')
                            print(out_r1)
                            if out_r1 == 'OK':
                                reset_time = now_time
                if not data: break
        except:
            print('continue')
            continue


if __name__ == '__main__':
    reset_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connect()