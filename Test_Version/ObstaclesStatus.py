from datetime import datetime,timedelta

class ObstacleStatus:
    
    IsExist: bool
    IsReport: bool
    FirstAppear: datetime
    
    ReportLimit=timedelta(minutes = 1)
    DetectedInfo={"cmd": "detected",
                  "data": [{"begin_angle":0, "end_angle":0,
                            "width": 0, "dist": 0,
                            "points": [ [0, 0],],
                            "uid":"0" }]}
    
    def __init__(self):
        self.IsExist=True
        self.IsReport=False
        self.FirstAppear=datetime.now()