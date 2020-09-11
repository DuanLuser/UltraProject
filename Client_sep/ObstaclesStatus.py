from datetime import datetime,timedelta

class ObstacleStatus:
    
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