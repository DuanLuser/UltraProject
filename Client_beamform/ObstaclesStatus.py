# -*- encoding: utf-8 -*-
'''
@File    :   ObstaclesStatus.py
@Time    :   2020/09/22 19:31:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

from datetime import datetime, timedelta

class ObstacleStatus:
    """ 储存出现的障碍的状态 """
    IsExist: bool
    IsReport: bool
    FirstAppear: datetime
    
    ReportLimit=timedelta(minutes = 1)
    
    def __init__(self):
        self.IsExist=True
        self.IsReport=False
        self.FirstAppear=datetime.now()


    '''
    # 上报障碍物和图片 发送以下格式json
    {
        "cmd": "log",
        "level": "DETECTED",
        "message": "检测到障碍物！",
        "image": image_base64
    }

    # 上报障碍物移除
    {
        "cmd": "log",
        "level": "REMOVED",
        "message": "障碍物已移除"
    }
    '''
