"""串口工具模块。

功能：
1. 循环读取：后台线程持续读取串口数据，处理半行缓冲、ANSI 颜色码清洗、解码容错，
   并将带时间戳的完整行写入日志文件（绝对路径，文件只在循环外打开一次）
2. 写入：发送命令，可选自动补换行
3. 检测关键字：在读取流中阻塞等待指定关键字出现，支持超时控制
4. 复制关键信息：通过正则表达式从串口数据中提取关键信息并返回
5. 异常处理：自定义异常体系，统一异常捕获与日志记录，重连带指数退避
6. 多串口连接：SerialManager 统一管理多个串口连接的建立、获取与释放
"""

import os
import re
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue

import serial
import serial.tools.list_ports
from serial import SerialException

from utils.log_utils import get_logger

logger = get_logger()

# 串口日志存储目录（基于项目根目录的绝对路径）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERIAL_LOG_DIR = os.path.join(PROJECT_ROOT, "serial_logs")
os.makedirs(SERIAL_LOG_DIR, exist_ok=True)

# ANSI 颜色码（如 \x1b[32m、\x1b[0m）
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

# 读取循环的休眠间隔（秒）
READ_BUSY_INTERVAL = 0.01
READ_IDLE_INTERVAL = 0.05


class SerialError(Exception):
    """串口异常基类。"""


class SerialConnectError(SerialError):
    """串口连接失败。"""


class SerialTimeoutError(SerialError):
    """串口操作超时（等待关键字/提取信息未在时限内命中）。"""


class SerialReadError(SerialError):
    """串口读取异常。"""


class SerialSendError(SerialError):
    """串口写入异常。"""


class SerialPort:
    """单串口连接封装。

    :param port: 串口设备路径，如 "/dev/cu.usbserial-1140"
    :param baudrate: 波特率，默认 115200
    :param timeout: 串口读写超时时间（秒）
    """

    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

        # 读取线程相关状态
        self._stop_event = threading.Event()
        self._read_thread = None
        self._line_queue = Queue()
        self._history_lock = threading.Lock()
        self._history = deque(maxlen=2000)  # 近期完整行缓存，供信息提取回溯

        self._open()

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------
    def _open(self):
        """打开串口，失败时抛出对应的自定义异常。"""
        try:
            self.ser = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=self.timeout
            )
            logger.info(
                f"串口连接成功：{self.port} @ {self.baudrate}"
            )
        except FileNotFoundError as exc:
            raise SerialConnectError(f"端口不存在，请检查端口连接：{exc}") from exc
        except PermissionError as exc:
            raise SerialConnectError(f"权限不足，端口被占用：{exc}") from exc
        except ValueError as exc:
            raise SerialConnectError(f"串口参数错误：{exc}") from exc
        except SerialException as exc:
            raise SerialConnectError(f"串口打开失败：{exc}") from exc
        except Exception as exc:
            raise SerialConnectError(f"串口连接出现其他错误：{exc}") from exc

    @property
    def is_open(self):
        """串口是否处于打开状态。"""
        return self.ser is not None and self.ser.is_open

    def ser_is_open(self):
        """检查串口连接情况并记录日志。

        :return: True 表示已连接，False 表示已断开
        """
        if self.is_open:
            logger.info(f"串口{self.port}已打开")
            return True
        logger.error(f"串口{self.port}连接断开")
        return False

    def reconnect(self, max_retries=5, base_delay=1, max_delay=30):
        """重连串口，采用指数退避策略。

        :param max_retries: 最大重试次数
        :param base_delay: 首次重试延迟（秒）
        :param max_delay: 单次重试延迟上限（秒）
        :return: True 表示重连成功
        :raises SerialConnectError: 重试耗尽仍未成功
        """
        delay = base_delay
        for attempt in range(1, max_retries + 1):
            try:
                self.close()
                self._open()
                logger.info(f"串口{self.port}第{attempt}次重连成功")
                return True
            except SerialConnectError as exc:
                logger.error(
                    f"串口{self.port}第{attempt}次重连失败：{exc}，"
                    f"{delay}秒后重试"
                )
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
        raise SerialConnectError(
            f"串口{self.port}重连失败，已重试{max_retries}次"
        )

    def close(self):
        """关闭串口并停止读取线程，可重复调用（幂等）。"""
        self.stop()
        if self.ser is not None and self.ser.is_open:
            try:
                self.ser.close()
                logger.info(f"串口{self.port}已关闭")
            except SerialException as exc:
                logger.error(f"串口{self.port}关闭异常：{exc}")

    # ------------------------------------------------------------------
    # 上下文管理器支持
    # ------------------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # ------------------------------------------------------------------
    # 串口枚举
    # ------------------------------------------------------------------
    @staticmethod
    def list_ports():
        """列出当前系统可用的串口设备列表。"""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        logger.info(f"串口列表：{ports}")
        return ports

    # 兼容旧接口
    port_list_show = list_ports

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------
    def send(self, data, newline=True):
        """向串口写入数据。

        :param data: 待发送的字符串
        :param newline: 是否自动追加换行符
        :raises SerialSendError: 写入失败且重连后仍失败
        """
        if not self.is_open:
            self.reconnect()
        payload = (data + "\n") if newline else data
        try:
            self.ser.write(payload.encode("utf-8"))
            self.ser.flush()
            logger.info(f"串口{self.port}发送：{data!r}")
        except (SerialException, OSError) as exc:
            logger.error(f"串口{self.port}写入异常：{exc}")
            try:
                self.reconnect()
                self.ser.write(payload.encode("utf-8"))
                self.ser.flush()
            except (SerialError, SerialException, OSError) as retry_exc:
                raise SerialSendError(
                    f"串口{self.port}写入失败：{retry_exc}"
                ) from retry_exc

    # 兼容旧接口
    ser_send_words = send

    # ------------------------------------------------------------------
    # 循环读取
    # ------------------------------------------------------------------
    def start(self):
        """启动后台读取线程（若未启动）。"""
        if self._read_thread is not None and self._read_thread.is_alive():
            logger.warning(f"串口{self.port}读取线程已在运行")
            return
        self._stop_event.clear()
        self._read_thread = threading.Thread(
            target=self.read_loop, name=f"serial-read-{self.port}", daemon=True
        )
        self._read_thread.start()
        logger.info(f"串口{self.port}读取线程已启动")

    def stop(self, join_timeout=5):
        """停止后台读取线程。"""
        self._stop_event.set()
        if self._read_thread is not None and self._read_thread.is_alive():
            self._read_thread.join(timeout=join_timeout)
        self._read_thread = None

    def read_loop(self, log_name=None):
        """循环读取串口数据。

        持续读取串口数据，按行切分（保留半行缓冲），清洗 ANSI 颜色码，
        带时间戳写入日志文件，并推入队列供关键字检测/信息提取使用。

        :param log_name: 日志文件名，默认按 "串口名-日期.log" 命名
        """
        log_name = log_name or (
            f"{self.port.replace('/', '_')}-"
            f"{datetime.now().strftime('%Y-%m-%d')}.log"
        )
        log_path = os.path.join(SERIAL_LOG_DIR, log_name)
        pending = ""  # 半行缓冲

        logger.info(f"等待串口{self.port}获取数据")
        with open(log_path, "a", encoding="utf-8") as log_file:
            while not self._stop_event.is_set():
                try:
                    if not self.is_open:
                        self._handle_read_failure()
                        continue

                    if self.ser.in_waiting > 0:
                        raw = self.ser.read(self.ser.in_waiting)
                        text = pending + raw.decode("utf-8", errors="ignore")
                        pending = ""
                        # 未出现行结束符则整段作为半行缓冲，等待下一轮
                        if not text.endswith(("\r\n", "\n", "\x1b[0m")):
                            pending = text
                            continue
                        for line in text.split("\r\n"):
                            line = ANSI_ESCAPE_RE.sub("", line).strip()
                            if not line:
                                continue
                            timestamp = datetime.now().strftime(
                                "[%Y-%m-%d_%H:%M:%S]:"
                            )
                            log_file.write(f"{timestamp}{line}\n")
                            log_file.flush()
                            with self._history_lock:
                                self._history.append(line)
                            self._line_queue.put(line)
                        time.sleep(READ_BUSY_INTERVAL)
                    else:
                        time.sleep(READ_IDLE_INTERVAL)
                except (OSError, SerialException) as exc:
                    logger.error(f"串口{self.port}读取异常：{exc}")
                    self._handle_read_failure()
                except Exception as exc:
                    logger.error(f"串口{self.port}读取出现未知异常：{exc}")
                    time.sleep(READ_IDLE_INTERVAL)

    def _handle_read_failure(self):
        """读取失败后的统一处理：尝试重连，失败则停止线程。"""
        try:
            self.reconnect()
        except SerialConnectError as exc:
            logger.error(f"串口{self.port}重连失败，停止读取线程：{exc}")
            self._stop_event.set()

    # ------------------------------------------------------------------
    # 关键字检测
    # ------------------------------------------------------------------
    def wait_for_keyword(self, keyword, timeout=10):
        """阻塞等待读取流中出现指定关键字。

        :param keyword: 待检测的关键字
        :param timeout: 最长等待时间（秒）
        :return: 命中关键字的完整行
        :raises SerialTimeoutError: 超时未命中
        """
        logger.info(f"串口{self.port}等待关键字：{keyword!r}（超时{timeout}秒）")
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SerialTimeoutError(
                    f"串口{self.port}等待关键字{keyword!r}超时（{timeout}秒）"
                )
            try:
                line = self._line_queue.get(timeout=remaining)
            except Empty:
                continue
            if keyword in line:
                logger.info(f"串口{self.port}命中关键字：{line}")
                return line

    # ------------------------------------------------------------------
    # 关键信息提取（复制关键信息）
    # ------------------------------------------------------------------
    def extract_info(self, pattern, timeout=10, group=1):
        """通过正则表达式从读取流中提取关键信息。

        :param pattern: 正则表达式字符串
        :param timeout: 最长等待时间（秒）
        :param group: 返回的捕获组编号，0 表示整个匹配
        :return: 匹配到的关键信息字符串
        :raises SerialTimeoutError: 超时未匹配到
        """
        logger.info(f"串口{self.port}提取信息，正则：{pattern!r}")
        regex = re.compile(pattern)
        deadline = time.monotonic() + timeout

        # 先回溯历史行，命中直接返回
        with self._history_lock:
            for line in list(self._history):
                match = regex.search(line)
                if match:
                    result = match.group(group)
                    logger.info(f"串口{self.port}从历史数据提取到：{result!r}")
                    return result

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SerialTimeoutError(
                    f"串口{self.port}提取信息{pattern!r}超时（{timeout}秒）"
                )
            try:
                line = self._line_queue.get(timeout=remaining)
            except Empty:
                continue
            match = regex.search(line)
            if match:
                result = match.group(group)
                logger.info(f"串口{self.port}提取到关键信息：{result!r}")
                return result


class SerialManager:
    """多串口连接管理器。

    以端口为键统一管理多个 SerialPort 实例，支持批量连接、
    按端口获取、统一关闭，并支持上下文管理器协议。
    """

    def __init__(self):
        self._ports = {}

    def connect(self, port, baudrate=115200, timeout=1):
        """建立（或复用）一个串口连接。

        :param port: 串口设备路径
        :param baudrate: 波特率
        :param timeout: 读写超时时间（秒）
        :return: SerialPort 实例
        :raises SerialConnectError: 连接失败
        """
        if port in self._ports:
            existing = self._ports[port]
            if existing.is_open:
                logger.info(f"串口{port}已连接，直接复用")
                return existing
        serial_port = SerialPort(port=port, baudrate=baudrate, timeout=timeout)
        self._ports[port] = serial_port
        return serial_port

    def connect_many(self, port_configs):
        """批量建立多个串口连接。

        :param port_configs: 列表，每项为 {"port": ..., "baudrate": ..., "timeout": ...}
        :return: dict[str, SerialPort]，键为端口路径
        """
        for config in port_configs:
            self.connect(
                port=config["port"],
                baudrate=config.get("baudrate", 115200),
                timeout=config.get("timeout", 1),
            )
        return dict(self._ports)

    def get(self, port):
        """按端口路径获取已连接的串口实例。

        :param port: 串口设备路径
        :return: SerialPort 实例
        :raises SerialConnectError: 该端口尚未连接
        """
        serial_port = self._ports.get(port)
        if serial_port is None:
            raise SerialConnectError(f"串口{port}尚未连接，请先调用 connect()")
        return serial_port

    def close_all(self):
        """关闭所有串口连接并释放资源。"""
        for port, serial_port in self._ports.items():
            try:
                serial_port.close()
            except Exception as exc:
                logger.error(f"串口{port}关闭异常：{exc}")
        self._ports.clear()
        logger.info("所有串口连接已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()
        return False


# 兼容旧接口：原有代码中的 SerialConnect 名称继续可用
SerialConnect = SerialPort
