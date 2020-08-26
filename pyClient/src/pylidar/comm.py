#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   comm.py
@Time    :   2020/07/28 16:34:50
@Author  :   Runze Tang 
@Version :   1.0
@Contact :   libcat1997@outlook.com
@License :   (C)Copyright 2020, LIBCAT
@Desc    :   None
'''


from threading import Thread, Event
import logzero
import logging
import json
from datetime import datetime
from websocket import WebSocketApp
from apscheduler.schedulers.background import BackgroundScheduler

logger = logzero.setup_logger("Comm")


class ICommClient:
    """通信客户端抽象类，封装了主要的发送、接收、重连逻辑。具体通信方式应当继承该类并实现
    """

    ###########Public成员#############
    server_url: str # 服务器地址
    device_id: str  # 设备id
    server_connect_timeout: int = 5     # 尝试连接服务器的超时时间(秒)
    server_connect_interval: int = 10 # 尝试连接服务器的时间间隔(秒)
    server_ping_timeout: int = 5        # ping服务器的超时时间(秒)
    server_ping_maxfailure: int = 3     # ping服务器最大失败次数
    server_ping_interval: int = 10      # ping服务器的时间间隔(秒)

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

        self._scheduler.add_job(
            self.Connect,
            'interval', 
            seconds=self.server_connect_interval, 
            id="Connect", 
            next_run_time=datetime.now())

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

    ############事件处理#############
    def OnConnected(self):
        """连接上服务器时
        """
        self._is_connected = True
        logger.info(f"连接到服务器成功: {self.server_url}")

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
        logger.info(f"与服务器连接断开({reason})，{self.server_ping_interval}秒后重试")
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
        self.__ws_client.sock.settimeout(5)

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
    ws = WebsocketClient()
    ws.server_url = "ws://localhost:2714"
    ws.device_id = "2"
    ws.Start()
    input()
