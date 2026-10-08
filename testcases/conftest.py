"""pytest 全局配置与 fixtures。

职责：
1. --platform 命令行选项：android / ios / all，驱动公共用例双端参数化
2. 设备连接（session 级，复用 PhoneManager 按平台自动选机）
3. airtest 设备与 poco 驱动注入（驱动为 function 级保证用例隔离）
4. app 生命周期控制（用例前启动、用例后关闭，复用 BasePage 能力）
5. 页面工厂注入：用例直接拿到当前平台的页面实例
6. allure 集成：动态标签、失败截图自动附加

fixture 依赖链：
    phone_manager(session) -> device_info(session, 按 platform 参数化)
    -> airtest_device(session) -> poco_driver(function) -> app_page(function)
"""

import os
import time
import urllib.request
from typing import Dict

import allure
import pytest

from pages.page_factory import PageFactory
from utils.log_utils import get_logger
from utils.phone_manager import DeviceInfo, PhoneManager
from utils.serial_utils import SerialConnectError, SerialManager

logger = get_logger()

# 失败截图保存目录
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "reports")

# 平台中文标签（用于 allure 报告分组）
PLATFORM_LABELS = {"android": "安卓端", "ios": "iOS 端"}

# WebDriverAgent 状态检查超时（秒）
WDA_CHECK_TIMEOUT = 3.0


# ==================== 命令行选项与参数化 ====================

def pytest_addoption(parser):
    """注册自定义命令行选项。"""
    group = parser.getgroup("platform")
    group.addoption(
        "--platform",
        default="all",
        choices=["android", "ios", "all"],
        help="指定运行平台：android / ios / all（默认 all，双端全跑）",
    )


def pytest_generate_tests(metafunc):
    """对声明了 platform fixture 的用例按 --platform 选项参数化。"""
    if "platform" in metafunc.fixturenames:
        option = metafunc.config.getoption("--platform")
        platforms = ["android", "ios"] if option == "all" else [option]
        metafunc.parametrize("platform", platforms, scope="session")


def pytest_configure(config):
    """注册自定义 marker。"""
    for marker in ("android", "ios", "smoke", "regression", "serial"):
        config.addinivalue_line("markers", f"{marker}: {marker} 标记")


# ==================== 设备与驱动 fixtures ====================

@pytest.fixture(scope="session")
def phone_manager():
    """设备管理器（session 级，结束时统一断开）。"""
    manager = PhoneManager()
    yield manager
    manager.disconnect_all()


@pytest.fixture(scope="session")
def device_info(phone_manager, platform) -> DeviceInfo:
    """按平台自动连接第一台在线设备。

    :return: 已连接的 DeviceInfo
    """
    return phone_manager.connect_first_available(platform)


def _check_wda_ready(port: int) -> bool:
    """探测 WebDriverAgent 状态接口是否就绪。

    :param port: WDA 端口
    :return: 就绪返回 True
    """
    url = f"http://127.0.0.1:{port}/status"
    try:
        with urllib.request.urlopen(url, timeout=WDA_CHECK_TIMEOUT) as response:
            return response.status == 200
    except Exception as exc:  # noqa: BLE001 探测失败统一按未就绪处理
        logger.debug(f"WDA 状态探测失败 [{url}]：{exc}")
        return False


@pytest.fixture(scope="session")
def airtest_device(platform, device_info):
    """按平台创建 airtest 设备连接（session 级复用）。

    iOS 端依赖 WebDriverAgent，未就绪时给出明确跳过原因，
    不影响安卓端用例运行。

    :return: airtest 设备实例
    """
    from airtest.core.api import connect_device

    if platform == "android":
        uri = f"android:///{device_info.udid}"
    else:
        wda_port = device_info.wda_port or 8100
        if not _check_wda_ready(wda_port):
            pytest.skip(f"iOS WebDriverAgent 未就绪（127.0.0.1:{wda_port}/status "
                        f"不可达），请先启动 WDA 后再运行 iOS 用例")
        uri = f"ios:///127.0.0.1:{wda_port}"

    device = connect_device(uri)
    logger.info(f"airtest 设备已连接：{uri}")
    return device


@pytest.fixture
def poco_driver(platform, airtest_device):
    """创建 poco 驱动（function 级，每次用例重建保证隔离）。

    :return: poco 驱动实例
    """
    if platform == "android":
        from poco.drivers.android.uiautomation import AndroidUiautomationPoco
        return AndroidUiautomationPoco(
            device=airtest_device,
            use_airtest_input=True,
            screenshot_each_action=False,
        )

    from poco.drivers.ios.uiautomation import IOSUiautomationPoco
    return IOSUiautomationPoco(device=airtest_device)


@pytest.fixture
def app_page(platform, poco_driver, device_info):
    """app 生命周期 + 页面注入。

    用例前：打 allure 平台标签、启动 app、创建当前平台页面实例
    用例后：关闭 app

    :return: 当前平台的页面实例（BasePage 子类）
    """
    allure.dynamic.feature(f"{PLATFORM_LABELS[platform]} · app 生命周期")
    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    page = PageFactory.create(
        platform, "main_page", poco=poco_driver, udid=device_info.udid
    )
    page.start_app(device_info.app_package)
    yield page
    page.stop_app(device_info.app_package)


# ==================== 失败截图钩子 ====================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动截图并附加到 allure 报告。"""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    poco = item.funcargs.get("poco_driver")
    if poco is None:
        return

    try:
        os.makedirs(REPORT_DIR, exist_ok=True)
        filename = os.path.join(
            REPORT_DIR, f"failure_{item.name}_{int(time.time())}.png"
        )
        poco.device.snapshot(filename=filename)
        allure.attach.file(
            filename,
            name="失败截图",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:  # noqa: BLE001 截图失败不阻断测试流程
        logger.warning(f"失败截图生成失败：{exc}")

    # 串口用例失败：附加最近串口输出，便于定位
    for fixture_name in SERIAL_FIXTURE_NAMES:
        serial_port = item.funcargs.get(fixture_name)
        if serial_port is None:
            continue
        try:
            recent = serial_port.get_recent_lines(n=200)
            payload = recent if recent else "(串口无历史输出)"
            allure.attach(
                payload,
                name=f"串口输出 [{fixture_name}]",
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception as exc:  # noqa: BLE001 串口 attach 失败不阻断
            logger.warning(f"附加串口输出失败 [{fixture_name}]：{exc}")


# ==================== 串口 fixtures ====================

# 模块级注册表：port -> SerialPort 实例，供失败钩子失败时取最近输出附加到 allure
_SERIAL_REGISTRY: Dict[str, "SerialPort"] = {}

# 串口 fixture 名称（失败钩子据此识别当前用例用到的串口 fixture）
SERIAL_FIXTURE_NAMES = ("serial_port", "serial_control_port", "serial_log_port")


def _register_serial_port(port: str, serial_port: "SerialPort") -> None:
    """注册串口实例到模块级注册表。"""
    _SERIAL_REGISTRY[port] = serial_port


def _unregister_serial_port(port: str) -> None:
    """从注册表移除串口实例。"""
    _SERIAL_REGISTRY.pop(port, None)


def _load_serial_ports():
    """读取并校验 config.yaml 中的 serial_ports 配置。

    :return: 串口配置列表；未配置或读取失败时返回空列表
    """
    try:
        from config.config_manager import load_config
        manager = load_config()
        return manager.validate_serial_ports()
    except Exception as exc:  # noqa: BLE001 串口配置异常按无串口处理
        logger.warning(f"串口配置读取/校验失败，串口用例将被跳过：{exc}")
        return []


def _serial_skip_reason(serial_ports) -> str:
    """根据串口配置情况生成 skip 原因。"""
    if not serial_ports:
        return "未配置串口（config.yaml 无 serial_ports 节点或为空）"
    return None


@pytest.fixture(scope="session")
def serial_manager():
    """串口管理器（session 级，结束时统一关闭所有串口）。

    未配置串口时 yield None，由下游 fixture 据此跳过串口用例。
    """
    serial_ports = _load_serial_ports()
    if not serial_ports:
        yield None
        return

    manager = SerialManager()
    for config in serial_ports:
        try:
            manager.connect(
                port=config["port"],
                baudrate=config.get("baudrate", 115200),
                timeout=config.get("timeout", 1),
            )
        except SerialConnectError as exc:
            logger.warning(f"串口 [{config['name']}:{config['port']}] 连接失败：{exc}")
    yield manager
    manager.close_all()


def _get_serial_port_config(serial_ports, name):
    """按名称查找串口配置。"""
    for config in serial_ports:
        if config.get("name") == name:
            return config
    return None


@pytest.fixture
def serial_port(request, serial_manager):
    """按名称获取串口连接（function 级）。

    用例通过 `@pytest.mark.parametrize("serial_name", ["camera_console"])`
    指定串口名；未配置串口、串口名不存在或连接失败时跳过。

    :return: SerialPort 实例
    """
    serial_ports = _load_serial_ports()
    reason = _serial_skip_reason(serial_ports)
    if reason:
        pytest.skip(reason)

    serial_name = getattr(request, "param", None) or "serial_name"
    config = _get_serial_port_config(serial_ports, serial_name)
    if config is None:
        pytest.skip(f"串口配置中不存在名称 [{serial_name}]")

    if serial_manager is None:
        pytest.skip(f"串口 [{serial_name}] 管理器不可用")

    try:
        port_obj = serial_manager.get(config["port"])
    except SerialConnectError as exc:
        pytest.skip(f"串口 [{serial_name}] 连接失败：{exc}")

    port = config["port"]
    _register_serial_port(port, port_obj)
    try:
        yield port_obj
    finally:
        _unregister_serial_port(port)


@pytest.fixture
def serial_control_port(request, serial_manager):
    """按 purpose=control 选取控制串口（function 级）。"""
    serial_ports = _load_serial_ports()
    reason = _serial_skip_reason(serial_ports)
    if reason:
        pytest.skip(reason)
    if serial_manager is None:
        pytest.skip("串口管理器不可用")

    target = [c for c in serial_ports if c.get("purpose") == "control"]
    if not target:
        pytest.skip("未配置 purpose=control 的串口")
    config = target[0]
    try:
        port_obj = serial_manager.get(config["port"])
    except SerialConnectError as exc:
        pytest.skip(f"控制串口 [{config['name']}] 连接失败：{exc}")

    port = config["port"]
    _register_serial_port(port, port_obj)
    try:
        yield port_obj
    finally:
        _unregister_serial_port(port)


@pytest.fixture
def serial_log_port(request, serial_manager):
    """按 purpose=log 选取日志采集串口（function 级）。"""
    serial_ports = _load_serial_ports()
    reason = _serial_skip_reason(serial_ports)
    if reason:
        pytest.skip(reason)
    if serial_manager is None:
        pytest.skip("串口管理器不可用")

    target = [c for c in serial_ports if c.get("purpose") == "log"]
    if not target:
        pytest.skip("未配置 purpose=log 的串口")
    config = target[0]
    try:
        port_obj = serial_manager.get(config["port"])
    except SerialConnectError as exc:
        pytest.skip(f"日志串口 [{config['name']}] 连接失败：{exc}")

    port = config["port"]
    _register_serial_port(port, port_obj)
    try:
        yield port_obj
    finally:
        _unregister_serial_port(port)
