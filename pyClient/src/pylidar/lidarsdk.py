#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   lidarsdk.py
@Time    :   2020/07/27 20:38:33
@Author  :   Runze Tang 
@Version :   1.0
@Contact :   libcat1997@outlook.com
@License :   (C)Copyright 2020, LIBCAT
@Desc    :   None
'''


import logzero
import serial
from serial import Serial
import struct
import logging
from typing import List, Callable, NoReturn

LIDAR_PACEKT_HEADER1 = 0xAA
FRAME_HEAD_LENGTH = 8
MOTOR_SPEED_RES = 0.05
DISTANCE_RES = 0.00025
ANGLE_RES = 0.01

logger = logzero.setup_logger(name="Lidar", level=logging.INFO)


class PolarPoint:
    """极坐标点
    """

    Angle: float
    Dist: float

    def __init__(self, angle=0, dist=0):
        """极坐标点

        Parameters
        ----------
        angle : float
            极角
        dist : float
            极径
        """
        self.Angle = angle
        self.Dist = dist


class Rslidar:
    """Lidar封装类
    """

    _serial: Serial = None
    port_name: str  # 串口名称
    bit_rate: int   # 串口波特率
    timeout: int    # 串口打开超时时间
    sigval_threshold = 100 # 信号强度最低阈值
    round_received: Callable[[List[PolarPoint]], None]

    def __init__(self, port_name, bit_rate=230400) -> None:
        """初始化串口

        Parameters
        ----------
        port_name : str
            端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
        bit_rate : int
            波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
        """
        self.port_name = port_name
        self.bit_rate = bit_rate

    def Open(self, timeout=None) -> bool:
        """打开串口

        Parameters
        ----------
        timeout : int, optional
            超时设置, None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）, by default 0
        """
        ret = False
        try:
            # 打开串口，并得到串口对象
            self._serial = serial.Serial(self.port_name, self.bit_rate, timeout=timeout)
            # 判断是否打开成功
            if self._serial.is_open:
                return True
        except Exception as e:
            logger.exception(e)
            return False

    def Close(self) -> None:
        """关闭串口
        """
        if self._serial and self._serial.is_open:
            self._serial.flushInput()
            self._serial.flushOutput()
            self._serial.close()
            self._serial = None

    def ReadData(self) -> NoReturn:
        """持续读取串口数据
        """

        points = []
        while True:
            # 找到分隔符0xAA
            self._serial.read_until(bytes([0xAA]))
            # 读取并解析帧头
            frame_header = self._serial.read(7)
            if len(frame_header) != 7:
                logger.warning(f'frame header len!=7:'+frame_header.hex())
                continue
            frame_len = struct.unpack(">H", frame_header[0:2])[0]
            frame_prot_ver = frame_header[2]
            frame_type = frame_header[3]
            frame_cmd = frame_header[4]
            frame_param_len = struct.unpack(">H", frame_header[5:7])[0]
            if frame_len > 200:
                logger.warning(f"Unexcepted frameheader: {frame_header.hex()}")
                continue
            logger.debug(f"frame_len={frame_len} frame_prot_ver={hex(frame_prot_ver)} frame_type={hex(frame_type)} frame_cmd={hex(frame_cmd)} frame_param_len={frame_param_len}")

            # 读取并解析数据
            frame_body = self._serial.read(frame_param_len + 2)

            # logger.info(frame_body.hex())
            n = int((frame_param_len - 5) / 3)  # 本帧点数量
            mspeed = frame_body[0]*MOTOR_SPEED_RES  # 电机转速
            angle_offset = struct.unpack(">H", frame_body[3:5])[0] * ANGLE_RES  # 本帧角度偏移

            # 如果是新的一圈
            if angle_offset <= 0.1:
                if len(points) > 0:
                    if self.round_received:
                        self.round_received(points)
                    else:
                        self.ReceivedOneRound(points)
                    points.clear()

            # 解析点数据
            for i in range(n):
                offset = 5+i*3
                signal_val = frame_body[offset]  # 信号强度
                dist = struct.unpack(">H", frame_body[offset+1:offset+3])[0] * DISTANCE_RES  # 距离
                angle = angle_offset + 22.5 * i / n  # 角度

                if dist > 0 and signal_val > self.sigval_threshold:
                    point = PolarPoint(angle, dist)
                    points.append(point)

            logger.debug(f"帧: angle={angle_offset}-{angle_offset+22.5}° count={n}")

    def ReceivedOneRound(self, points: List[PolarPoint]):
        """默认的接收到一圈的处理函数
        """
        logger.info(f"收到一圈数据({len(points)})")
        for p in points:
            print(f"a={p.Angle:0.2f} r={p.Dist:0.2f}")
        pass


# 测试用
if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    lidar = Rslidar("COM3", 230400)
    isopen = lidar.Open()
    if isopen:
        lidar.ReadData()
        lidar.Close()
