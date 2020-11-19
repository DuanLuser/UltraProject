#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   Server.py
@Time    :   2020/07/28 16:34:50
@Author  :   Runze Tang 
@Version :   1.0
@Contact :   libcat1997@outlook.com
@License :   (C)Copyright 2020, LIBCAT
@Desc    :   None
'''

import os
import base64
import logzero
import logging
import json
import time
from datetime import datetime,timedelta
from websocket import WebSocketApp
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread, Event, Lock

from beamforming import URadar
from ObstaclesStatus import ObstacleStatus
from camera import Picture
from playRec import playprompt

logger = logzero.setup_logger("Comm")


class ICommClient:
    """通信客户端抽象类，封装了主要的发送、接收、重连逻辑。具体通信方式应当继承该类并实现
    """

    ###########Public成员#############
    server_url: str # 服务器地址
    device_id: str  # 设备id
    server_connect_timeout: int = 5     # 尝试连接服务器的超时时间(秒)
    server_connect_interval: int = 10   # 尝试连接服务器的时间间隔(秒)
    server_ping_timeout: int = 5        # ping服务器的超时时间(秒)
    server_ping_maxfailure: int = 3     # ping服务器最大失败次数
    server_ping_interval: int = 10      # ping服务器的时间间隔(秒)
    
    radar: URadar = URadar()
    picture: Picture = Picture()
    Obstacles: list = []
    firstConnect: bool = False

    ###########Protected成员#############
    _server_replied_event: Event = Event()  # 用于检测服务器在线
    _server_timeout_count: int = 0   # 服务器超时次数
    _is_connected: bool = False  # 是否连接到服务器
    _scheduler: BackgroundScheduler = BackgroundScheduler()
    
    
    ###########公共函数###############
    def Start(self) -> None:
        """启动客户端，开始连接服务器
        """
        # 启动连接定时器，并立即执行一次
        if not self._scheduler.running:
            self._scheduler.start()
        
        self._scheduler.remove_all_jobs()
        self._scheduler.add_job(
            self.Connect,
            'interval', 
            seconds=self.server_connect_interval, 
            id="Connect", 
            next_run_time=datetime.now())
        
    def Shutdown(self) -> None:
        """停止客户端，断开连接，不再重连
        """
        try:
            self.Close()
        except:
            pass
        self._scheduler.shutdown()

    def Connect(self) -> None:
        """连接服务器
        """
        raise NotImplementedError

    def Send(self, data: str) -> None:
        """发送消息
        Parameters
        ----------
        data : str
            消息内容
        """
        raise NotImplementedError

    def Close(self) -> None:
        """关闭客户端
        """
        raise NotImplementedError
    
    def SendJson(self, data) -> None:
        """发送Json消息

        Parameters
        ----------
        data : Any
            任意可转换为Json的结构
        """
        self.Send(json.dumps(data))


    ############事件处理#############
    def OnConnected(self):
        """连接上服务器时
        """
        self._is_connected = True
        logger.info(f"连接到服务器成功: {self.server_url}")
        if not self.firstConnect:
            #playprompt("网络连接成功.wav")
            print("网络连接成功.wav")
            self.firstConnect=True
            Thread(target=self.DetectReport).start() # 连接成功后，启动检测
        else:
            print('网络连接成功.wav')
            self.radar.prompt="网络连接成功.wav"

        # 移除连接定时器
        self._scheduler.remove_job("Connect")
        
        # 启动ping定时器
        self._scheduler.add_job(
            self.CheckAlive, 
            'interval', 
            seconds=self.server_ping_interval, 
            id="CheckAlive")

        # 注册设备
        self.RegisterDevice()
            

    def OnDisconnected(self, reason: str = ""):
        """与服务器断开时
        Parameters
        ----------
        reason : str, optional
            原因描述, by default ""
        """
        self._is_connected = False
        logger.info(f"与服务器连接断开({reason})，{self.server_connect_interval}秒后重试")
        # 连接成功后断开
        if self.firstConnect:
            print('网络连接失败，正在重新连接.wav')
            self.radar.prompt="网络连接失败，正在重新连接.wav"
        
        # 移除ping定时器
        self._scheduler.remove_job("CheckAlive")
        # 添加连接定时器
        self._scheduler.add_job(
            self.Connect, 
            'interval', 
            seconds=self.server_connect_interval, 
            id="Connect")

    def OnConnectFailed(self, reason: str = ""):
        """与服务器连接失败时
        Parameters
        ----------
        reason : str, optional
            原因描述, by default ""
        """
        logger.info(f"无法连接到服务器({reason})，{self.server_connect_interval}s后重试")
        if not self.firstConnect:
            #playprompt("网络连接失败，正在重新连接.wav")
            print("网络连接失败，正在重新连接.wav")

    def OnMessage(self, message: str):
        """接收到服务器消息时
        Parameters
        ----------
        message : str
            消息内容
        """
        logger.info(f"收到服务器消息：{message}")

        if message == "ping":
            self.Send("pong")

        if message == "pong":
            self._server_replied_event.set()
            
        if message == "reset":
            self.radar.reset_order=True
            self.Obstacles.clear()
            self.Send("resetOk")
                      

    ############逻辑处理############
    def RegisterDevice(self):
        """注册设备id
        """
        self.Send(json.dumps({"cmd": "register", "deviceid": self.device_id}))

    def CheckAlive(self):
        """检查服务器是否在线
        """
        self._server_replied_event.clear()
        logger.info(f"Pinging server...")
        self.Send("ping")
        #self._server_replied_event.set()
        replied = self._server_replied_event.wait(self.server_ping_timeout) # 等待回复 5秒超时
        if not replied:
            # 超时了
            self._server_timeout_count += 1 # 超时计数器+1
            logger.warning(f"Ping server timeout ({self._server_timeout_count}/{self.server_ping_maxfailure})")
            if self._server_timeout_count == self.server_ping_maxfailure:
                logger.warning(f"server 已掉线")
                self.Close()
                
        else:
            self.TimeoutCount = 0 # 超时计数器清零

    #############雷达检测############
    def DetectReport(self):
        reset_limit = timedelta(minutes = 15)
        empty_count = 0
        prompt_count = 0
        Reported=False
        
        if self.radar.reset()=="OK":
            reset_time = datetime.now()
            while True:
                outcome = self.radar.detect()
                if outcome=="nonempty":
                    empty_count = 0
                    if len(self.Obstacles)==0:
                        obstacle=ObstacleStatus()
                        self.Obstacles.append(obstacle)
                        prompt_count = 0
                        Reported=False
                    #else: 后续判断障碍物是否改变
                    if prompt_count < 3: # 连续提示次数
                        #playprompt("请注意，消防通道禁止阻塞，请立即移除障碍物.wav")
                        print("请注意，消防通道禁止阻塞，请立即移除障碍物.wav")
                        prompt_count+=1  
                if outcome=="empty" and len(self.Obstacles)!=0:
                    self.Obstacles.clear()
                    #playprompt("障碍物已移除，谢谢配合.wav")
                    print("障碍物已移除，谢谢配合.wav")
                    if Reported==True:
                        self.Send(json.dumps({"cmd": "log", "level": "REMOVED","message":"障碍物已移除"}))
                        logger.info("障碍物移除已上报！")
                    
                now_time=datetime.now()
                for ob in self.Obstacles:    
                    if ob.IsReport==False:#now_time-ob.FirstAppear > ob.ReportLimit and ob.IsReport==False:
                        # 拍照上传
                        image_base64=self.picture.takePhoto()
                        self.Send(json.dumps({"cmd": "log", "level": "DETECTED","message":"检测到障碍物！","image": image_base64}))
                        ob.IsReport=True
                        logger.info("存在障碍物已上报！")
                        Reported=True
                # 一段时间后自行reset
                '''
                now_time=datetime.now()
                if outcome == 'empty' and  now_time-reset_time >= reset_limit :
                    empty_count+=1
                    if empty_count==2 and self.radar.reset()=="OK":
                        reset_time = now_time
                        empty_count = 0
                        logger.info("重置成功！")
                '''
                        

class WebsocketClient(ICommClient):
    """基于Websocket的通讯客户端
    """

    __ws_client: WebSocketApp

    def on_message(self, ws, message):
        self.OnMessage(message)

    def on_error(self, ws, error):
        logger.debug(error)

    def on_close(self, ws):
        if not self._is_connected:
            self.OnConnectFailed("time out")
        else:
            self.OnDisconnected("disconnected")

    def on_open(self, ws):
        self.OnConnected()


    def Connect(self):
        # 初始化客户端
        self.__ws_client = WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close)
        logger.info("正在尝试连接到服务器...")
        # 启动客户端，开始连接
        Thread(target=self.__ws_client.run_forever, daemon=True).start()
        # 设置连接服务器的超时时间
        self.__ws_client.sock.settimeout(self.server_connect_timeout)

    def Send(self, data: str):
        self.__ws_client.send(data)

    def Close(self):
        if self.__ws_client:
            self.__ws_client.close()

class UdpClient(ICommClient):
    """基于UDP的通信客户端
    """
    pass


# 测试用
if __name__ == "__main__":
    
    time.sleep(5)
    ws = WebsocketClient()
    ws.server_url = "ws://47.100.88.177:2714"
    ws.device_id = "2"
    ws.Start()
    while True: continue