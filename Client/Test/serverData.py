import os
import random
import time
from socket import *
from multiprocessing import Pool

import logzero
import logging
import json
from datetime import datetime,timedelta
from websocket import WebSocketApp
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread, Event, Lock

from ObstaclesStatus import ObstacleStatus

logger = logzero.setup_logger("Comm")

import reset
import getData

HOST = '192.168.0.108'
POST = [21567]


def playprompt(wav):
    os.system('aplay -D "plughw:0,0" audio/'+ wav)

def subtime(time1,time2):
    time1=datetime.datetime.strptime(time1,"%Y-%m-%d %H:%M:%S")
    time2=datetime.datetime.strptime(time2,"%Y-%m-%d %H:%M:%S")
    return time2-time1

if __name__ == '__main__':

    addr=(HOST,POST[0])
    #connect(addr)
    Obstacles=[]
    reset_limit = timedelta(minutes = 30)
    empty_count = 0
    prompt_count = 0
    Reported=False
        
    if True:#reset.main()=="OK":
        logger.info("reset successfully！")
        reset_time = datetime.now()
        while True:
            outcome = getData.main()
            if outcome=="nonempty":
                empty_count = 0
                if len(Obstacles)==0:
                    obstacle=ObstacleStatus()
                    Obstacles.append(obstacle)
                #else: 后续判断障碍物是否改变
                if prompt_count < 3: # 连续提示次数
                    #playprompt("请注意，消防通道禁止阻塞，请立即移除障碍物.wav")
                    #time.sleep(5)
                    prompt_count+=1  
            if outcome=="empty" and len(Obstacles)!=0:
                Obstacles.clear()
                prompt_count = 0 
                #playprompt("障碍物已移除，谢谢配合.wav")
                #time.sleep(3)
                if Reported==True:
                    #self.Send(json.dumps({"cmd": "removed", "data": ["0"]}))
                    logger.info("障碍物移除已上报！")
                    
            now_time=datetime.now()
            for ob in Obstacles:    
                if now_time-ob.FirstAppear > ob.ReportLimit and ob.IsReport==False:
                    #self.Send(json.dumps(ob.DetectedInfo))
                    ob.IsReport=True
                    logger.info("存在障碍物已上报！")
                    Reported=True
            # 一段时间后自行reset
            
            now_time=datetime.now()
            if outcome == 'empty' and  now_time-reset_time >= reset_limit :
                empty_count+=1
                if empty_count==2 and reset.main()=="OK":
                    reset_time = now_time
                    empty_count = 0
                    logger.info("重置成功！")
            






