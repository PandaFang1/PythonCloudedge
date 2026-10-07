"""手机连接管理模块。

功能：
1. Android 设备通过 adb 命令连接与管理
2. iOS 设备通过 Xcode（xcrun devicectl / xctrace）连接与管理
3. 支持多台手机同时连接
4. 支持多平台（Android / iOS）连接
5. 可与 config.yaml 中配置的设备列表进行比对校验

设计说明：
- BasePhoneConnector 为平台连接器抽象基类，各平台分别实现子类
- PhoneManager 为统一管理入口，负责读取配置、分发连接器、批量连接与比对
"""

import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from utils.log_utils import get_logger

logger = get_logger()

# 支持的平台名称（统一按小写比较）
SUPPORTED_PLATFORMS = ("android", "ios")

# iOS UDID 正则：新机型带连字符（00008110-000130AA1A05401E），旧机型为 40 位十六进制
_IOS_UDID_PATTERN = re.compile(
    r"\b(?:[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16}|[0-9A-Fa-f]{40})\b"
)

# CoreDevice UUID 正则（devicectl list 输出中的 identifier，8-4-4-4-12 格式）
_COREDEVICE_UUID_PATTERN = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
)


class PhoneError(Exception):
    """手机连接模块异常基类。"""

    pass


class PhoneConnectError(PhoneError):
    """手机连接失败异常。"""

    pass


class PhoneCommandError(PhoneError):
    """手机管理命令执行失败异常。"""

    pass


class PhoneNotFoundError(PhoneError):
    """设备未找到 / 未在线异常。"""

    pass


class PlatformNotSupportedError(PhoneError):
    """不支持的平台异常。"""

    pass


class DeviceConfigMismatchError(PhoneError):
    """设备配置与 config.yaml 不匹配异常。"""

    pass


@dataclass
class DeviceInfo:
    """设备信息（与 config.yaml 中 devices 条目一一对应）。"""

    user_name: str
    platform: str
    udid: str
    phone_model: str = ""
    app_package: str = ""
    wda_port: Optional[int] = None
    # 连接成功后回填的附加信息
    online: bool = False

    def to_dict(self) -> Dict:
        """转换为字典，便于日志打印。"""
        return {
            "user_name": self.user_name,
            "platform": self.platform,
            "udid": self.udid,
            "phone_model": self.phone_model,
            "online": self.online,
        }


class BasePhoneConnector(ABC):
    """平台连接器抽象基类，子类需实现具体平台的连接逻辑。"""

    # 子类需覆写：命令行工具名，如 "adb" / "xcrun"
    TOOL_NAME: str = ""

    def __init__(self, timeout: float = 10.0):
        """
        :param timeout: 单条命令执行超时时间（秒）
        """
        self.timeout = timeout
        self._tool_path: Optional[str] = None

    # ---------------- 通用能力 ----------------

    def check_tool_available(self) -> bool:
        """检查平台命令行工具是否安装可用。

        :return: 工具可用返回 True，否则 False
        """
        self._tool_path = shutil.which(self.TOOL_NAME)
        return self._tool_path is not None

    def run_command(self, args: List[str]) -> str:
        """执行平台命令并返回标准输出。

        :param args: 命令参数列表，如 ["adb", "devices"]
        :return: 命令标准输出内容
        :raises PhoneCommandError: 命令不存在、超时或返回非 0 退出码时抛出
        """
        if not self._tool_path:
            if not self.check_tool_available():
                msg = f"命令行工具 [{self.TOOL_NAME}] 未安装或不在 PATH 中"
                logger.error(msg)
                raise PhoneCommandError(msg)

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"命令执行超时（>{self.timeout}s）：{' '.join(args)}"
            logger.error(msg)
            raise PhoneCommandError(msg) from exc
        except OSError as exc:
            msg = f"命令执行失败：{' '.join(args)}，错误：{exc}"
            logger.error(msg)
            raise PhoneCommandError(msg) from exc

        if result.returncode != 0:
            msg = (f"命令返回非 0 退出码 [{result.returncode}]：{' '.join(args)}，"
                   f"stderr：{result.stderr.strip()}")
            logger.error(msg)
            raise PhoneCommandError(msg)

        return result.stdout

    # ---------------- 抽象方法：由子类实现 ----------------

    @abstractmethod
    def list_online_udids(self) -> List[str]:
        """获取当前在线设备的 UDID 列表。

        :return: 在线设备 UDID 列表
        :raises PhoneCommandError: 命令执行失败时抛出
        """

    @abstractmethod
    def connect(self, device: DeviceInfo) -> bool:
        """连接指定设备。

        :param device: 设备信息
        :return: 连接成功返回 True
        :raises PhoneConnectError: 设备不在线或连接失败时抛出
        """

    @abstractmethod
    def disconnect(self, udid: str) -> None:
        """断开指定设备连接。

        :param udid: 设备 UDID
        """

    def is_online(self, udid: str) -> bool:
        """判断设备是否在线（默认基于在线列表判断，子类可覆写）。

        :param udid: 设备 UDID
        :return: 在线返回 True
        """
        return udid in self.list_online_udids()


class AndroidAdbConnector(BasePhoneConnector):
    """Android 设备连接器，基于 adb 命令实现。"""

    TOOL_NAME = "adb"

    def list_online_udids(self) -> List[str]:
        """解析 `adb devices` 输出，返回状态为 device 的 UDID 列表。"""
        output = self.run_command(["adb", "devices"])
        udids = []
        for line in output.splitlines()[1:]:
            parts = line.strip().split()
            # 格式：UDID \t device / offline / unauthorized
            if len(parts) >= 2 and parts[1] == "device":
                udids.append(parts[0])
        logger.debug(f"adb 在线设备：{udids}")
        return udids

    def connect(self, device: DeviceInfo) -> bool:
        """连接 Android 设备。

        :param device: 设备信息
        :return: 连接成功返回 True
        :raises PhoneConnectError: 设备未授权 / 不在线 / 配置不匹配时抛出
        """
        online_udids = self.list_online_udids()

        if device.udid not in online_udids:
            # 模拟器场景尝试 adb connect
            if device.udid.startswith(("127.", "localhost")):
                logger.info(f"模拟器设备 [{device.udid}] 不在线，尝试 adb connect ...")
                self.run_command(["adb", "connect", device.udid])
                online_udids = self.list_online_udids()
                if device.udid not in online_udids:
                    msg = f"模拟器设备 [{device.udid}] adb connect 后仍不在线"
                    logger.error(msg)
                    raise PhoneConnectError(msg)
            else:
                msg = (f"Android 设备 [{device.user_name}:{device.udid}] 不在线，"
                       f"当前在线设备：{online_udids}")
                logger.error(msg)
                raise PhoneConnectError(msg)

        # 二次确认设备状态
        state = self.run_command(["adb", "-s", device.udid, "get-state"]).strip()
        if state != "device":
            msg = f"设备 [{device.udid}] 状态异常：{state}"
            logger.error(msg)
            raise PhoneConnectError(msg)

        device.online = True
        logger.info(f"Android 设备连接成功：[{device.user_name}] udid=[{device.udid}]")
        return True

    def disconnect(self, udid: str) -> None:
        """断开设备连接。

        真机无法通过 adb 主动断开（仅提示），模拟器使用 adb disconnect。
        """
        if udid.startswith(("127.", "localhost")):
            self.run_command(["adb", "disconnect", udid])
            logger.info(f"模拟器设备已断开：[{udid}]")
        else:
            logger.info(f"真机设备 [{udid}] 需物理断开 USB 连接（adb 无法主动断开）")

    # ---------------- Android 扩展能力 ----------------

    def run_shell(self, udid: str, shell_cmd: str) -> str:
        """在指定设备上执行 shell 命令。

        :param udid: 设备 UDID
        :param shell_cmd: shell 命令字符串
        :return: 命令输出
        """
        return self.run_command(["adb", "-s", udid, "shell", shell_cmd])

    def install_app(self, udid: str, apk_path: str) -> None:
        """安装 apk 到指定设备。

        :param udid: 设备 UDID
        :param apk_path: apk 文件路径
        :raises PhoneCommandError: 安装失败时抛出
        """
        if not Path(apk_path).is_file():
            msg = f"apk 文件不存在：{apk_path}"
            logger.error(msg)
            raise PhoneCommandError(msg)
        self.run_command(["adb", "-s", udid, "install", "-r", "-t", apk_path])
        logger.info(f"apk 安装成功：[{udid}] <- {apk_path}")


class IosXcodeConnector(BasePhoneConnector):
    """iOS 设备连接器，基于 Xcode 命令行工具实现。

    优先使用 xcrun devicectl（Xcode 15+），不可用时回退到 xctrace。
    """

    TOOL_NAME = "xcrun"

    def _list_udids_by_devicectl(self) -> Optional[List[str]]:
        """通过 xcrun devicectl 获取已连接设备的 UDID 列表。

        :return: UDID 列表；命令不可用时返回 None（表示需回退到 xctrace）
        """
        try:
            output = self.run_command(["xcrun", "devicectl", "list", "devices"])
        except PhoneCommandError:
            return None

        udids = []
        for line in output.splitlines():
            line_lower = line.lower()
            # 统计已连接/可用状态的行；注意 unavailable 含 available 子串，需排除
            is_usable = ("connected" in line_lower
                         or ("available" in line_lower and "unavailable" not in line_lower))
            if not is_usable:
                continue
            # 兼容经典 UDID 与 CoreDevice UUID 两种 identifier 格式
            for pattern in (_IOS_UDID_PATTERN, _COREDEVICE_UUID_PATTERN):
                matched = pattern.search(line)
                if matched:
                    udids.append(matched.group())
                    break
        return udids

    def _list_udids_by_xctrace(self) -> List[str]:
        """通过 xctrace list devices 获取设备 UDID 列表（Xcode 15 以下回退方案）。"""
        output = self.run_command(["xcrun", "xctrace", "list", "devices"])
        udids = []
        for line in output.splitlines():
            matched = _IOS_UDID_PATTERN.search(line)
            if matched:
                udids.append(matched.group())
        return udids

    def list_online_udids(self) -> List[str]:
        """获取当前通过 USB 连接的 iOS 设备 UDID 列表。"""
        udids = self._list_udids_by_devicectl()
        if udids is None:
            logger.info("devicectl 不可用（Xcode < 15），回退到 xctrace 获取设备列表")
            udids = self._list_udids_by_xctrace()
        logger.debug(f"iOS 在线设备：{udids}")
        return udids

    def connect(self, device: DeviceInfo) -> bool:
        """连接 iOS 设备（校验设备已被 Xcode 识别）。

        :param device: 设备信息
        :return: 连接成功返回 True
        :raises PhoneConnectError: 设备不在线时抛出
        """
        if not self.is_online(device.udid):
            online_udids = self.list_online_udids()
            msg = (f"iOS 设备 [{device.user_name}:{device.udid}] 未被 Xcode 识别，"
                   f"当前在线设备：{online_udids}，请检查 USB 连接并确认已信任此电脑")
            logger.error(msg)
            raise PhoneConnectError(msg)

        device.online = True
        logger.info(f"iOS 设备连接成功：[{device.user_name}] udid=[{device.udid}]")
        return True

    def is_online(self, udid: str) -> bool:
        """判断 iOS 设备是否在线。

        通过 devicectl 按设备 UDID 直接查询（支持经典 UDID / CoreDevice UUID /
        设备名等），避免列表输出中 identifier 格式不一致导致的误判。

        :param udid: 设备 UDID
        :return: 在线返回 True
        """
        try:
            self.run_command(
                ["xcrun", "devicectl", "device", "info", "details", "--device", udid]
            )
            return True
        except PhoneCommandError:
            return False

    def disconnect(self, udid: str) -> None:
        """iOS 真机无法通过命令行主动断开，仅提示。"""
        logger.info(f"iOS 设备 [{udid}] 需物理断开 USB 连接")

    # ---------------- iOS 扩展能力 ----------------

    def install_app(self, udid: str, app_path: str) -> None:
        """安装 app 到指定 iOS 设备。

        :param udid: 设备 UDID
        :param app_path: .app 路径
        :raises PhoneCommandError: 安装失败时抛出
        """
        if not Path(app_path).exists():
            msg = f"app 路径不存在：{app_path}"
            logger.error(msg)
            raise PhoneCommandError(msg)
        self.run_command(
            ["xcrun", "devicectl", "device", "install", "app",
             "--device", udid, app_path]
        )
        logger.info(f"app 安装成功：[{udid}] <- {app_path}")

    def launch_app(self, udid: str, bundle_id: str) -> None:
        """启动指定 app。

        :param udid: 设备 UDID
        :param bundle_id: 应用 Bundle ID
        """
        self.run_command(
            ["xcrun", "devicectl", "device", "process", "launch",
             "--device", udid, bundle_id]
        )
        logger.info(f"应用已启动：[{udid}] {bundle_id}")


class PhoneManager:
    """手机统一管理入口：读取 config.yaml，分发平台连接器，支持多设备批量连接与配置比对。"""

    def __init__(self, config_file: str = "config/config.yaml", timeout: float = 10.0):
        """
        :param config_file: 配置文件路径，默认 config/config.yaml
        :param timeout: 单条命令执行超时时间（秒）
        :raises DeviceConfigMismatchError: 配置文件不存在或格式非法时抛出
        """
        self.config_file = config_file
        self.timeout = timeout
        self._devices: List[DeviceInfo] = []
        self._connectors: Dict[str, BasePhoneConnector] = {}
        self._load_config()

    # ---------------- 配置加载 ----------------

    def _load_config(self) -> None:
        """读取 config.yaml 并解析设备列表。

        :raises DeviceConfigMismatchError: 配置文件不存在 / 无 devices 节点 /
                                          平台不支持 / 缺少必要字段时抛出
        """
        config_path = Path(self.config_file)
        if not config_path.is_file():
            msg = f"配置文件不存在：{config_path.resolve()}"
            logger.error(msg)
            raise DeviceConfigMismatchError(msg)

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        raw_devices = config_data.get("devices")
        if not raw_devices:
            msg = f"配置文件 [{config_path}] 中未找到 devices 设备列表"
            logger.error(msg)
            raise DeviceConfigMismatchError(msg)

        for index, raw in enumerate(raw_devices):
            platform = str(raw.get("platform", "")).strip()
            if platform.lower() not in SUPPORTED_PLATFORMS:
                msg = (f"设备 #{index} 平台 [{platform}] 不支持，"
                       f"当前支持：{list(SUPPORTED_PLATFORMS)}")
                logger.error(msg)
                raise PlatformNotSupportedError(msg)

            udid = str(raw.get("udid", "")).strip()
            if not udid:
                msg = f"设备 #{index}（{raw.get('user_name', '未知')}）缺少 udid 字段"
                logger.error(msg)
                raise DeviceConfigMismatchError(msg)

            self._devices.append(DeviceInfo(
                user_name=str(raw.get("user_name", f"设备_{index}")),
                platform=platform,
                udid=udid,
                phone_model=str(raw.get("phone_model", "")),
                app_package=str(raw.get("app_package", "")),
                wda_port=raw.get("wda_port"),
            ))

        logger.info(f"配置加载完成，共 {len(self._devices)} 台设备："
                    f"{[d.user_name for d in self._devices]}")

    # ---------------- 连接器管理 ----------------

    def get_connector(self, platform: str) -> BasePhoneConnector:
        """根据平台获取（并缓存）对应连接器。

        :param platform: 平台名称（Android / iOS，忽略大小写）
        :return: 平台连接器实例
        :raises PlatformNotSupportedError: 平台不支持时抛出
        """
        key = platform.lower()
        if key == "android":
            connector_cls = AndroidAdbConnector
        elif key == "ios":
            connector_cls = IosXcodeConnector
        else:
            msg = f"不支持的平台 [{platform}]，当前支持：{list(SUPPORTED_PLATFORMS)}"
            logger.error(msg)
            raise PlatformNotSupportedError(msg)

        if key not in self._connectors:
            connector = connector_cls(timeout=self.timeout)
            if not connector.check_tool_available():
                msg = (f"平台 [{platform}] 依赖的命令行工具 "
                       f"[{connector_cls.TOOL_NAME}] 未安装，请先安装对应环境")
                logger.error(msg)
                raise PhoneCommandError(msg)
            self._connectors[key] = connector
            logger.debug(f"已创建平台连接器：{connector_cls.__name__}")

        return self._connectors[key]

    # ---------------- 连接操作 ----------------

    def connect(self, user_name: str) -> DeviceInfo:
        """按配置中的用户名连接单台设备（实际设备信息以 config.yaml 为准）。

        :param user_name: config.yaml 中配置的 user_name
        :return: 连接成功的 DeviceInfo
        :raises PhoneNotFoundError: 配置中不存在该用户时抛出
        :raises PhoneConnectError: 设备连接失败时抛出
        """
        device = self._find_device_by_name(user_name)
        connector = self.get_connector(device.platform)
        connector.connect(device)
        return device

    def connect_all(self) -> Dict[str, DeviceInfo]:
        """批量连接配置文件中的所有设备（单台失败不影响其余设备）。

        :return: dict，key 为 user_name，value 为 DeviceInfo（仅含连接成功的设备）
        """
        result: Dict[str, DeviceInfo] = {}
        total = len(self._devices)
        logger.info(f"开始批量连接 {total} 台设备 ...")

        for index, device in enumerate(self._devices, start=1):
            logger.info(f"[{index}/{total}] 正在连接 [{device.user_name}] "
                        f"({device.platform}:{device.udid}) ...")
            try:
                connector = self.get_connector(device.platform)
                connector.connect(device)
                result[device.user_name] = device
            except (PhoneConnectError, PhoneError) as exc:
                logger.warning(f"[{device.user_name}] 连接失败：{exc}")

        logger.info(f"批量连接完成：成功 {len(result)}/{total} 台")
        return result

    def connect_first_available(self, platform: str) -> DeviceInfo:
        """连接指定平台的第一台在线设备。

        按配置顺序遍历该平台设备，返回首台可连接的设备；
        常用于双端参数化用例中按平台自动选取被测设备。

        :param platform: 平台名称（android / ios，忽略大小写）
        :return: 连接成功的 DeviceInfo
        :raises PhoneNotFoundError: 该平台无任何在线设备时抛出
        """
        for device in self._devices:
            if device.platform.lower() != platform.lower():
                continue
            try:
                connector = self.get_connector(device.platform)
                if connector.is_online(device.udid):
                    device.online = True
                    logger.info(f"平台 [{platform}] 已选定设备："
                                f"[{device.user_name}] udid=[{device.udid}]")
                    return device
                logger.debug(f"[{device.user_name}] 不在线，尝试下一台")
            except PhoneError as exc:
                logger.warning(f"[{device.user_name}] 在线检测失败：{exc}，尝试下一台")

        msg = f"平台 [{platform}] 无任何在线设备，请检查设备连接与 config.yaml 配置"
        logger.error(msg)
        raise PhoneNotFoundError(msg)

    def disconnect_all(self) -> None:
        """断开所有已连接设备。"""
        for device in self._devices:
            if not device.online:
                continue
            connector = self.get_connector(device.platform)
            connector.disconnect(device.udid)
            device.online = False
        logger.info("所有设备已断开")

    # ---------------- 配置比对 ----------------

    def _find_device_by_name(self, user_name: str) -> DeviceInfo:
        """按 user_name 查找配置中的设备。

        :param user_name: 用户名
        :return: DeviceInfo
        :raises PhoneNotFoundError: 未找到时抛出
        """
        for device in self._devices:
            if device.user_name == user_name:
                return device
        msg = (f"配置文件 [{self.config_file}] 中不存在用户 [{user_name}]，"
               f"已配置用户：{[d.user_name for d in self._devices]}")
        logger.error(msg)
        raise PhoneNotFoundError(msg)

    def compare_with_config(self) -> Dict:
        """将实际在线设备与 config.yaml 配置进行比对。

        比对维度：
        1. 已配置且在线的设备（正常）
        2. 已配置但不在线的设备（缺失）
        3. 在线但未在配置中的设备（多余，含各平台）

        :return: 比对结果 dict：{"matched": [...], "missing": [...], "extra": [...]}
        """
        configured_udids = {d.udid for d in self._devices}
        matched: List[Dict] = []
        missing: List[Dict] = []
        extra: List[Dict] = []

        # 逐台校验配置设备的在线状态
        for device in self._devices:
            try:
                connector = self.get_connector(device.platform)
                online = connector.is_online(device.udid)
            except PhoneError as exc:
                logger.warning(f"[{device.user_name}] 状态校验失败：{exc}")
                online = False

            if online:
                matched.append(device.to_dict())
            else:
                missing.append(device.to_dict())

        # 扫描各平台在线设备，找出未在配置中的多余设备
        for platform in SUPPORTED_PLATFORMS:
            try:
                connector = self.get_connector(platform)
                for udid in connector.list_online_udids():
                    if udid not in configured_udids:
                        extra.append({"platform": platform, "udid": udid})
            except PhoneError as exc:
                logger.warning(f"平台 [{platform}] 设备扫描失败：{exc}")

        report = {"matched": matched, "missing": missing, "extra": extra}
        logger.info(f"配置比对结果：匹配 {len(matched)} 台，缺失 {len(missing)} 台，"
                    f"多余 {len(extra)} 台")
        if missing:
            logger.warning(f"缺失设备明细：{missing}")
        if extra:
            logger.warning(f"多余在线设备（未写入配置）：{extra}")
        return report


if __name__ == "__main__":
    # 模块自测：仅执行配置比对，不发起真实连接
    manager = PhoneManager(config_file=str(
        Path(__file__).resolve().parents[1] / "config" / "config.yaml"))
    manager.compare_with_config()
