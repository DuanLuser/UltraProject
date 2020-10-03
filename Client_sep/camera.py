# -*- encoding: utf-8 -*-
'''
@File    :   camera.py
@Time    :   2020/09/22 19:23:00
@Author  :   Dil Duan
@Version :   1.0
@Contact :   1522740702@qq.com
@License :   (C)Copyright 2020
'''

import os
import time
import base64
from datetime import datetime


# 调用fswebcam拍照，树莓派上可以通过sudo apt install fswebcam安装。分辨率和照片质量可调
class Picture:
    
    image_name: str = None  # 当前时间作为文件名
    path: str = "image/"
    image_num: int = 0

    def image2base64(self, filename: str) -> str:
        """
            将jpg文件编码为base64，方便传输
            return: encoded data
        """
        with open(self.path+filename, "rb") as f:
            base64_bytes: str = base64.encodebytes(f.read())
            base64_str = "data:image/jpeg;base64," + base64_bytes.decode()
            return base64_str
        
    def takePhoto(self):
        """
            拍照，并调用 image2base64()
            return: encoded data
        """
        self.image_num += 1
        if self.image_num == 5:
            self.clearPhotos()
            self.image_num = 0
        self.image_name = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
        os.system(f"fswebcam --no-banner -q -r 1280x960 --jpeg 95 {self.path+self.image_name}")
        # 调用函数将jpg文件编码成base64的字符串，上报障碍物的时候发送即可
        image_base64 = self.image2base64(self.image_name)
        return image_base64

    def clearPhotos(self):
        """
            清理照片（避免堆积占用内存）
            return: null
        """
        for photo in os.listdir(self.path):
            path_photo = os.path.join(self.path, photo)
            if os.path.isfile(path_photo):
                os.remove(path_photo)
    
    
    
if __name__ == "__main__":
    """ for testing """
    picture=Picture()
    while True:
        picture.takePhoto()
        time.sleep(2)
