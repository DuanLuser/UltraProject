import logging
from comm import WebsocketClient
from lidarsdk import Rslidar, PolarPoint
from typing import List, Dict, NoReturn, Set, Union, Tuple
import multiprocessing
from multiprocessing import Manager, Lock
from multiprocessing.connection import Connection
import time
import logzero
import numpy as np
import math

logger = logzero.setup_logger("lidar client", level=logging.INFO)


def StartLidar(pipe: Connection, serial_port, return_dict: Dict):
    lidar = Rslidar(serial_port, 230400)

    def received(points: List[PolarPoint]):
        pipe.send(points)

    lidar.round_received = received

    isopen = lidar.Open()
    if isopen:
        lidar.ReadData()
        return_dict["code"] = 0
        return_dict["msg"] = "OK"
    else:
        return_dict["code"] = -1
        return_dict["msg"] = "无法连接到激光雷达"


class Settings:
    serial_port: str = "COM3"
    server_address: str = "ws://localhost:2714"
    device_id: str = "0"
    reset_rounds: int = 12
    scan_rounds: int = 12
    min_dist_error: float = 0.1
    angle_end: int = 180
    continue_obj_dist_threshold: float = 0.1
    obstacle_stable_time: float = 30
    stable_rounds_before_detect: int = 3
    stable_dist_diff_threshold: float = 0.1
    stable_points_max_rate: float = 0.1


class Detector:
    settings: Settings = Settings()
    basic_points: List[float] = None

    __pipe: Connection = None
    __lock: multiprocessing.synchronize.Lock = Lock()
    __last_round:  List[float] = None

    def __init__(self, pipe: Connection, settings: Settings = None):
        self.__pipe = pipe

        # 使用默认配置
        if settings == None:
            self.settings = Settings()
        else:
            self.settings = settings

    def PrintPoints(self, points: List[float]) -> None:
        for i in range(self.settings.angle_end):
            print(f"{i}°：{points[i]}")

    def GetRound(self) -> List[PolarPoint]:
        return self.__pipe.recv()

    def GetRounds(self, n: int) -> Tuple[List[float], bool]:
        self.__lock.acquire()
        try:
            count = 0
            rounds: List[float] = np.zeros(self.settings.angle_end)
            rounds_count: List[int] = np.zeros(self.settings.angle_end)
            while count < n:
                # 从激光雷达获得一圈点
                points = self.GetRound()
                for p in points:
                    # 角度值向下取整得到数组下标
                    index = int(math.floor(p.Angle))
                    # 只处理指定范围内的数据
                    if index < self.settings.angle_end:
                        rounds[index] += p.Dist
                        rounds_count[index] += 1
                count += 1
                logger.debug(f'获取一圈：{len(points)}')
            for i in range(0, self.settings.angle_end):
                if rounds_count[i] != 0:
                    rounds[i] /= rounds_count[i]
            self.__lock.release()
            return (rounds, True)
        except Exception as ex:
            logger.exception(ex)
            self.__lock.release()
            return (None, False)

    def Reset(self) -> None:
        logger.info("正在重置...")
        points, ok = self.GetRounds(self.settings.reset_rounds)
        # self.TrackedObjs.clear()
        if ok:
            logger.info("重置成功！")
            self.basic_points = points
            self.PrintPoints(self.basic_points)
        else:
            logger.error("重置失败")

        # self.is_resetted=True

    def IsStable(self, round1: List[float], round2: List[float]) -> bool:
        assert len(round1) == len(round2)
        unstable_count = 0
        points_count = 0
        for i in range(self.settings.angle_end):
            if round1[i] > 0 and round2[i] > 0:
                points_count += 1
                if math.fabs(round1[i]-round2[i]) > self.settings.stable_dist_diff_threshold:
                    unstable_count += 1
        max_unstable_count = points_count * self.settings.stable_points_max_rate
        if unstable_count > max_unstable_count:
            logger.info(f"不稳定 上轮点数={len(round1)} 本轮点数={len(round2)} 不稳定{unstable_count}/阈值{max_unstable_count}")
            return False
        else:
            logger.info(f"稳定 上轮点数={len(round1)} 本轮点数={len(round2)} 不稳定{unstable_count}/阈值{max_unstable_count}")
            return True


if __name__ == "__main__":
    # 启动通讯客户端
    # ws = WebsocketClient()
    # ws.server_url = "ws://localhost:2714"
    # ws.device_id = "2"
    # ws.Start()

    # 启动激光雷达
    manager = Manager()
    return_dict = manager.dict()
    # 用管道传输数据
    pipe = multiprocessing.Pipe()
    # 将激光雷达驱动放在单独的进程中，避免Python的GIL引起性能问题
    p1 = multiprocessing.Process(target=StartLidar, args=(pipe[0], "COM3", return_dict))
    p1.daemon = True
    p1.start()
    time.sleep(1)
    # 如果激光雷达发生错误，通过return_dict获取返回值
    if "code" in return_dict and return_dict["code"] == -1:
        logger.error("错误，无法连接到激光雷达！")
        exit(0)

    # 启动检测  暂时没有完工，先测试一下部分功能
    try:
        detector = Detector(pipe[1])
        detector.Reset()
        last_round = None
        for i in range(10):
            points, ok = detector.GetRounds(10)
            if not ok:
                break
            if last_round is None:
                last_round = points
                continue
            is_stable = detector.IsStable(last_round, points)
            last_round = points
    except KeyboardInterrupt:
        pass
    p1.terminate()
