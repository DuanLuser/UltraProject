
import os
from datetime import datetime
import base64

class Picture:
    
    # 当前时间作为文件名
    
    image_name: str = None
    path: str = "image/"
    
    def __init__(self):    
        self.image_name = datetime.now().strftime("%Y%m%d_%H%M%S.jpg")

    # 调用fswebcam拍照，树莓派上可以通过sudo apt install fswebcam安装。分辨率和照片质量可调

    def image2base64(self, filename: str) -> str:
        """将jpg文件编码为base64，方便传输"""
        with open(self.path+filename, "rb") as f:
            base64_bytes: str = base64.encodebytes(f.read())
            base64_str = "data:image/jpeg;base64," + base64_bytes.decode()
            return base64_str
        
    def takePhoto(self):
        os.system(f"fswebcam --no-banner -q -r 1280x960 --jpeg 95 {self.path+self.image_name}")
        # 调用函数将jpg文件编码成base64的字符串，上报障碍物的时候发送即可
        image_base64 = self.image2base64(self.image_name)
        return image_base64
    
if __name__ == "__main__":
    picture=Picture()
    picture.takePhoto()
