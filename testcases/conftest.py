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

import allure
import pytest

from pages.page_factory import PageFactory
from utils.log_utils import get_logger
from utils.phone_manager import DeviceInfo, PhoneManager

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
    for marker in ("android", "ios", "smoke", "regression"):
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
