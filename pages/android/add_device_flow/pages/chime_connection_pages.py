"""Chime Base 添加流程 — 配网完成阶段 PO。

包含 3 个页面（真机 2026-10-09 验证）：
1. `ChimeConnectingPage` — 「连接网络」页（SmartWiFiActivity，等待设备入网）
2. `ChimeSuccessPage` — 「连接成功」页（SearchDeviceActivity，「下一步」）
3. `ChimeSetRoomPage` — 「设置房间」页（AddDeviceSetRoomActivity，「完成」）
"""

from __future__ import annotations

import time

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


TEXT_NEXT = "下一步"
TEXT_DONE = "完成"
TEXT_CONNECTING_KEYWORDS = ("连接网络", "连接", "配网", "正在", "联网")
TEXT_SUCCESS_KEYWORDS = ("连接成功", "成功", "已添加")


class ChimeConnectingPage(BasePage):
    """「连接网络」页面（SmartWiFiActivity，等待设备入网）。

    真机验证：页面含倒计时（tv_time）与提示文案（tv_msg1~3），
    设备注册中显示 tvDeviceRegister='注册到云端'；
    连接完成后自动跳转「连接成功」页（SearchDeviceActivity）。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '连接网络'
    TV_TIME = {"name": "com.cloudedge.smarteye:id/tv_time"}  # 倒计时
    TV_MSG1 = {"name": "com.cloudedge.smarteye:id/tv_msg1"}
    TV_MSG2 = {"name": "com.cloudedge.smarteye:id/tv_msg2"}
    TV_MSG3 = {"name": "com.cloudedge.smarteye:id/tv_msg3"}
    TV_DEVICE_REGISTER = {"name": "com.cloudedge.smarteye:id/tvDeviceRegister"}  # '注册到云端'

    # 成功页特征元素（用于判定连接完成）
    SUCCESS_MARKER = {"name": "com.cloudedge.smarteye:id/tv_find_device"}

    def wait_for_page_loaded(self, timeout: float = 15.0) -> bool:
        """等待「连接网络」页加载完成（标题含「连接网络」）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TITLE):
                title = self.get_text(self.TV_TITLE)
                if any(kw in title for kw in TEXT_CONNECTING_KEYWORDS):
                    logger.debug(f"Chime 连接页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 连接页在 {timeout}s 内未加载")
        return False

    def wait_connected(self, timeout: float = 120.0) -> bool:
        """等待设备入网完成（成功页特征元素 tv_find_device 出现）。

        设备首次入网较慢（含注册到云端），默认 120s。
        """
        deadline = time.time() + timeout
        last_log = 0.0
        while time.time() < deadline:
            if self.exists(self.SUCCESS_MARKER):
                logger.info("设备入网完成（检测到成功页特征元素）")
                return True
            now = time.time()
            if now - last_log > 20:
                remain = int(deadline - now)
                logger.info(f"等待设备入网中...（剩余 {remain}s）")
                last_log = now
            time.sleep(2)
        logger.warning(f"设备在 {timeout}s 内未完成入网")
        return False


class ChimeSuccessPage(BasePage):
    """「连接成功」页面（SearchDeviceActivity）。

    真机验证：tv_find_device='添加设备成功'、scan_camera_name=SN、
    底部 pps_back_home='下一步'。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '连接成功'
    TV_FIND_DEVICE = {"name": "com.cloudedge.smarteye:id/tv_find_device"}  # '添加设备成功'
    SCAN_CAMERA_NAME = {"name": "com.cloudedge.smarteye:id/scan_camera_name"}  # SN
    SCAN_CAMERA_TYPE = {"name": "com.cloudedge.smarteye:id/scan_camera_type"}  # '我的设备'
    PPS_BACK_HOME = {
        "name": "com.cloudedge.smarteye:id/pps_back_home",
        "text": TEXT_NEXT,
    }  # 底部「下一步」

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待「连接成功」页加载完成。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TITLE):
                title = self.get_text(self.TV_TITLE)
                if any(kw in title for kw in TEXT_SUCCESS_KEYWORDS):
                    logger.debug(f"Chime 成功页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 成功页在 {timeout}s 内未加载")
        return False

    def get_added_device_sn(self) -> str:
        """获取成功页展示的设备 SN（用于断言与期望 SN 一致）。"""
        return self.get_text(self.SCAN_CAMERA_NAME)

    def click_next(self) -> None:
        """点击「下一步」（进入设置房间页）。"""
        self.click(self.PPS_BACK_HOME)
        logger.info("成功页：已点击「下一步」")


class ChimeSetRoomPage(BasePage):
    """「设置房间」页面（AddDeviceSetRoomActivity）。

    真机验证：显示设备 SN（tv_device_name）与房间分类（tv_category_name），
    底部 pps_back_home='完成'。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '添加设备'
    TV_DEVICE_NAME = {"name": "com.cloudedge.smarteye:id/tv_device_name"}  # SN
    TV_CATEGORY_NAME = {"name": "com.cloudedge.smarteye:id/tv_category_name"}  # 房间名
    PPS_BACK_HOME = {
        "name": "com.cloudedge.smarteye:id/pps_back_home",
        "text": TEXT_DONE,
    }  # 底部「完成」

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待「设置房间」页加载完成（SN 元素 + 「完成」按钮出现）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_DEVICE_NAME) and self.exists(self.PPS_BACK_HOME):
                logger.debug("Chime 设置房间页已加载")
                return True
            time.sleep(0.5)
        logger.warning(f"Chime 设置房间页在 {timeout}s 内未加载")
        return False

    def click_finish(self, timeout: float = 15.0) -> None:
        """点击底部「完成」（进入安装指引页）。"""
        if not self.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError("设置房间页未加载，「完成」按钮无法点击")
        self.click(self.PPS_BACK_HOME)
        logger.info("设置房间页：已点击「完成」")
