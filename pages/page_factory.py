"""页面工厂模块。

职责：
1. 维护「平台 + 页面名 → 页面类」的统一注册表
2. 按平台分发页面实例，业务用例面向工厂编程，不感知平台细节

设计说明：
- 双端同一业务页面实现同名方法（如 wait_for_page_loaded），
  用例通过工厂获取当前平台的页面实例后按统一接口调用
- 新增页面：在 pages/android 与 pages/ios 各实现一个页面类，
  并在本文件 REGISTRY 中注册即可（开闭原则，无需改动用例代码）
"""

from typing import Dict, Tuple, Type

from pages.android import (
    CloudEdgeAccountPage,
    CloudEdgeAddDeviceCategoryPage,
    CloudEdgeLoginPage,
    CloudEdgeMainPage,
    CloudEdgeMessagePage,
    CloudEdgeMyPage,
    JingleAddPage,
    JingleBellDndPage,
    JingleDeletePage,
    JingleDeviceInfoPage,
    JingleDeviceLocationPage,
    JingleDeviceNamePage,
    JingleDeviceScenePage,
    JingleDeviceSharePage,
    JingleDeviceVersionPage,
    JingleGeneralPage,
    JingleInstallGuidePage,
    JingleRingtonePage,
    JingleSettingPage,
    JingleShareTypePage,
    JingleSleepTimeAddPage,
    JingleSoundPage,
    JingleStoragePage,
    JingleUnbindChannelPage,
)
from pages.base_page import BasePage
from pages.ios import YunjiMainPage, YunjiMessagePage, YunjiMyPage
from utils.log_utils import get_logger

logger = get_logger()

# 页面注册表：key 为 (平台, 页面名)，value 为页面类
REGISTRY: Dict[Tuple[str, str], Type[BasePage]] = {
    ("android", "login_page"): CloudEdgeLoginPage,
    ("android", "account_page"): CloudEdgeAccountPage,
    ("android", "add_device_category_page"): CloudEdgeAddDeviceCategoryPage,
    ("android", "jingle_add_page"): JingleAddPage,
    ("android", "jingle_delete_page"): JingleDeletePage,
    ("android", "jingle_setting_page"): JingleSettingPage,
    ("android", "jingle_device_info_page"): JingleDeviceInfoPage,
    ("android", "jingle_bell_dnd_page"): JingleBellDndPage,
    ("android", "jingle_ringtone_page"): JingleRingtonePage,
    ("android", "jingle_device_share_page"): JingleDeviceSharePage,
    ("android", "jingle_sound_page"): JingleSoundPage,
    ("android", "jingle_storage_page"): JingleStoragePage,
    ("android", "jingle_general_page"): JingleGeneralPage,
    ("android", "jingle_device_name_page"): JingleDeviceNamePage,
    ("android", "jingle_device_scene_page"): JingleDeviceScenePage,
    ("android", "jingle_device_location_page"): JingleDeviceLocationPage,
    ("android", "jingle_device_version_page"): JingleDeviceVersionPage,
    ("android", "jingle_sleep_time_add_page"): JingleSleepTimeAddPage,
    ("android", "jingle_share_type_page"): JingleShareTypePage,
    ("android", "jingle_install_guide_page"): JingleInstallGuidePage,
    ("android", "jingle_unbind_channel_page"): JingleUnbindChannelPage,
    ("android", "main_page"): CloudEdgeMainPage,
    ("ios", "main_page"): YunjiMainPage,
    ("android", "my_page"): CloudEdgeMyPage,
    ("ios", "my_page"): YunjiMyPage,
    ("android", "message_page"): CloudEdgeMessagePage,
    ("ios", "message_page"): YunjiMessagePage,
}


class PageFactoryError(Exception):
    """页面工厂异常基类。"""

    pass


class PageNotRegisteredError(PageFactoryError):
    """页面未注册异常。"""

    pass


class PageFactory:
    """页面工厂：按平台创建对应页面实例。"""

    @staticmethod
    def register(platform: str, page_name: str, page_cls: Type[BasePage]) -> None:
        """注册页面类（支持测试或扩展时动态注册）。

        :param platform: 平台名称（android / ios）
        :param page_name: 页面唯一名称（如 "main_page"）
        :param page_cls: 页面类（须继承 BasePage）
        :raises PageNotRegisteredError: 页面类未继承 BasePage 时抛出
        """
        if not (isinstance(page_cls, type) and issubclass(page_cls, BasePage)):
            msg = f"页面类 [{page_cls}] 未继承 BasePage，注册失败"
            logger.error(msg)
            raise PageNotRegisteredError(msg)

        REGISTRY[(platform.lower(), page_name)] = page_cls
        logger.debug(f"页面已注册：({platform}, {page_name}) -> {page_cls.__name__}")

    @staticmethod
    def create(platform: str, page_name: str, poco, udid: str = "") -> BasePage:
        """按平台创建页面实例。

        :param platform: 平台名称（android / ios，忽略大小写）
        :param page_name: 页面唯一名称（如 "main_page"）
        :param poco: poco 驱动实例
        :param udid: 设备 UDID，用于页面内 app 生命周期控制
        :return: 对应平台的页面实例
        :raises PageNotRegisteredError: 页面未注册时抛出
        """
        key = (platform.lower(), page_name)
        page_cls = REGISTRY.get(key)

        if page_cls is None:
            available = sorted(f"{p}:{n}" for p, n in REGISTRY)
            msg = (f"页面 [{page_name}] 在平台 [{platform}] 上未注册，"
                   f"当前已注册页面：{available}")
            logger.error(msg)
            raise PageNotRegisteredError(msg)

        page = page_cls(poco=poco, udid=udid)
        logger.info(f"页面已创建：[{platform}:{page_name}] -> {page_cls.__name__}")
        return page
