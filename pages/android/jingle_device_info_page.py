"""智能门铃 Chime Base 设备信息页 PO — jingle_device_info。

入口：jingle 设置页点击设备信息卡片（layout_device_info）。
Activity：DeviceInfoActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备信息」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump 验证）：
- 设备昵称行：'设备昵称' + tv_device_name（值，点击进设备名称页）
- 设备使用场景行（点击进场景页）
- SN 行：tv_sn
- 位置管理行：tv_location_manager（标题）+ tv_room_name（值，
  点击进位置管理页）
- WiFi名称：tv_wifi_name2 / 信号强度：tv_signal_strength /
  IP：tv_ip / MAC地址：tv_mac / 时区：tv_time_zone /
  设备平台：tv_platform / WiFi频段：tv_f / 设备版本：tv_version
- 4 个下级页面入口：layout_device_name（设备名称）/
  layout_device_scene（设备使用场景）/
  layout_location_manager（位置管理）/
  layout_firmware_version（设备版本）
"""

from __future__ import annotations

from pages.android.jingle_device_location_page import JingleDeviceLocationPage
from pages.android.jingle_device_name_page import JingleDeviceNamePage
from pages.android.jingle_device_scene_page import JingleDeviceScenePage
from pages.android.jingle_device_version_page import JingleDeviceVersionPage
from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeviceInfoPage(JingleSubPageBase):
    """设备信息页（DeviceInfoActivity，标题='设备信息'）。"""

    TITLE_TEXT = "设备信息"
    ACTIVITY_KEYWORD = "DeviceInfoActivity"

    # ==================== 字段定位器（名称-内容对） ====================
    TV_DEVICE_NAME = {"name": RID + "tv_device_name"}      # 设备昵称值
    TV_SN = {"name": RID + "tv_sn"}                        # SN
    TV_ROOM_NAME = {"name": RID + "tv_room_name"}          # 位置管理值
    TV_WIFI_NAME = {"name": RID + "tv_wifi_name2"}         # WiFi名称值
    TV_SIGNAL_STRENGTH = {"name": RID + "tv_signal_strength"}  # 信号强度值
    TV_IP = {"name": RID + "tv_ip"}                        # IP 值
    TV_MAC = {"name": RID + "tv_mac"}                      # MAC 值
    TV_TIME_ZONE = {"name": RID + "tv_time_zone"}          # 时区值
    TV_PLATFORM = {"name": RID + "tv_platform"}            # 设备平台值
    TV_WIFI_BAND = {"name": RID + "tv_f"}                  # WiFi频段值
    TV_VERSION = {"name": RID + "tv_version"}              # 设备版本值

    # ==================== 下级页面入口 ====================
    ENTRY_DEVICE_NAME = {"name": RID + "layout_device_name"}        # 设备名称
    ENTRY_DEVICE_SCENE = {"name": RID + "layout_device_scene"}      # 设备使用场景
    ENTRY_LOCATION_MANAGER = {"name": RID + "layout_location_manager"}  # 位置管理
    ENTRY_FIRMWARE_VERSION = {"name": RID + "layout_firmware_version"}  # 设备版本

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 字段 getter ====================

    def get_device_name(self) -> str:
        """读取设备昵称（如 '131903227'）。"""
        return self.get_text(self.TV_DEVICE_NAME)

    def get_sn(self) -> str:
        """读取设备 SN（如 'ppsb0f8fd64b303b45d9'）。"""
        return self.get_text(self.TV_SN)

    def get_room_name(self) -> str:
        """读取位置管理值（如 '方小C的家'）。"""
        return self.get_text(self.TV_ROOM_NAME)

    def get_wifi_name(self) -> str:
        """读取 WiFi 名称（如 'xiaoMI-楼顶拷机IPC'）。"""
        return self.get_text(self.TV_WIFI_NAME)

    def get_signal_strength(self) -> str:
        """读取信号强度（如 '100%'）。"""
        return self.get_text(self.TV_SIGNAL_STRENGTH)

    def get_ip(self) -> str:
        """读取设备 IP（如 '192.168.50.237'）。"""
        return self.get_text(self.TV_IP)

    def get_mac(self) -> str:
        """读取 MAC 地址（如 '1c:4e:a2:15:1a:c9'）。"""
        return self.get_text(self.TV_MAC)

    def get_time_zone(self) -> str:
        """读取时区（如 'Asia/Shanghai'）。"""
        return self.get_text(self.TV_TIME_ZONE)

    def get_platform(self) -> str:
        """读取设备平台（如 'T411E'）。"""
        return self.get_text(self.TV_PLATFORM)

    def get_wifi_band(self) -> str:
        """读取 WiFi 频段（如 '2.4G'）。"""
        return self.get_text(self.TV_WIFI_BAND)

    def get_version(self) -> str:
        """读取设备版本（如 '6.2.0.20260921'）。"""
        return self.get_text(self.TV_VERSION)

    # ==================== 下级页面入口（点击 → 验证 → 返回实例） ====================

    def _open_next_page(self, entry, next_page, action_desc: str):
        """通用下级页面导航：点击入口 → 验证加载 → 返回实例。"""
        self.click(entry)
        logger.info(f"设备信息页：已点击{action_desc}")
        if not next_page.wait_for_page_loaded(timeout=15.0):
            from pages.base_page import ElementNotFoundError

            raise ElementNotFoundError(
                f"点击{action_desc}后未进入对应页面"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return next_page

    def open_device_name_page(self) -> JingleDeviceNamePage:
        """进入设备名称页。支持链式调用。"""
        return self._open_next_page(
            self.ENTRY_DEVICE_NAME,
            JingleDeviceNamePage(self.poco, self.udid),
            "「设备名称」",
        )

    def open_device_scene_page(self) -> JingleDeviceScenePage:
        """进入设备使用场景页。支持链式调用。"""
        return self._open_next_page(
            self.ENTRY_DEVICE_SCENE,
            JingleDeviceScenePage(self.poco, self.udid),
            "「设备使用场景」",
        )

    def open_location_manager_page(self) -> JingleDeviceLocationPage:
        """进入位置管理页。支持链式调用。"""
        return self._open_next_page(
            self.ENTRY_LOCATION_MANAGER,
            JingleDeviceLocationPage(self.poco, self.udid),
            "「位置管理」",
        )

    def open_device_version_page(self) -> JingleDeviceVersionPage:
        """进入设备版本页。支持链式调用。"""
        return self._open_next_page(
            self.ENTRY_FIRMWARE_VERSION,
            JingleDeviceVersionPage(self.poco, self.udid),
            "「设备版本」",
        )
