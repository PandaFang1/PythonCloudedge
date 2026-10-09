"""Chime Base 添加流程 — 收尾阶段 PO。

包含 2 个页面：
1. `ChimeInstallGuidePage` — 「安装指引」页面（点「下一步」）
2. `ChimeNetworkDiagnosticPage` — 「网络诊断」页面（点「返回首页」+ 断言）

「网络诊断」页底部点击「返回首页」后，断言首页设备列表含目标 SN。
"""

from __future__ import annotations

import time

from pages.android.main_page import CloudEdgeMainPage
from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


TEXT_NEXT = "下一步"
TEXT_BACK_HOME = "返回首页"
TEXT_INSTALL_GUIDE_KEYWORDS = ("安装", "指引", "位置", "挂载")
TEXT_DIAGNOSTIC_KEYWORDS = ("网络", "诊断", "检测", "信号")


class ChimeInstallGuidePage(BasePage):
    """「安装指引」页面（GuideRightPlacePicActivity）。

    真机验证：tv_content 为安装位置说明文案，
    底部「下一步」按钮为 tv_next_vp。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '安装指引'
    TV_CONTENT = {"name": "com.cloudedge.smarteye:id/tv_content"}  # 安装说明文案
    BTN_NEXT = {"name": "com.cloudedge.smarteye:id/tv_next_vp", "text": TEXT_NEXT}

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待「安装指引」页加载完成。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TITLE):
                title = self.get_text(self.TV_TITLE)
                if any(kw in title for kw in TEXT_INSTALL_GUIDE_KEYWORDS):
                    logger.debug(f"Chime 安装指引页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 安装指引页在 {timeout}s 内未加载")
        return False

    def click_next(self) -> None:
        """点击「下一步」（进入网络诊断页）。"""
        self.click(self.BTN_NEXT)
        logger.info("安装指引页：已点击「下一步」")


class ChimeNetworkDiagnosticPage(BasePage):
    """「网络诊断」页面（NetworkDiagnosticActivity）。

    真机验证：tv_des_title='WIFI信号强度'、tv_desc_wifi_strength='强'、
    tv_back_home='返回首页'（底部主按钮）、next='检查更新'。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '网络诊断'
    TV_RIGHT_TEXT = {"name": "com.cloudedge.smarteye:id/tv_right_text"}  # '跳过'
    TV_DES_TITLE = {"name": "com.cloudedge.smarteye:id/tv_des_title"}  # 'WIFI信号强度'
    TV_DESC_WIFI_STRENGTH = {
        "name": "com.cloudedge.smarteye:id/tv_desc_wifi_strength",
    }  # '强' / '中' / '弱'
    TV_DESC_CONTENT = {"name": "com.cloudedge.smarteye:id/tv_desc_content"}  # 诊断结论
    BTN_BACK_HOME = {
        "name": "com.cloudedge.smarteye:id/tv_back_home",
        "text": TEXT_BACK_HOME,
    }  # 底部「返回首页」
    BTN_CHECK_UPDATE = {"name": "com.cloudedge.smarteye:id/next"}  # '检查更新'

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待「网络诊断」页加载完成。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TITLE):
                title = self.get_text(self.TV_TITLE)
                if any(kw in title for kw in TEXT_DIAGNOSTIC_KEYWORDS):
                    logger.debug(f"Chime 网络诊断页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 网络诊断页在 {timeout}s 内未加载")
        return False

    def click_back_to_homepage(self, timeout: float = 15.0) -> None:
        """点击底部「返回首页」按钮。"""
        if not self.wait_for_element(self.BTN_BACK_HOME, timeout=timeout):
            raise ElementNotFoundError(
                f"「{TEXT_BACK_HOME}」按钮在 {timeout}s 内未出现"
            )
        self.click(self.BTN_BACK_HOME)
        logger.info("网络诊断页：已点击「返回首页」")

    def assert_device_added(self, sn: str, timeout: float = 30.0) -> None:
        """断言已跳到首页且设备列表含指定 SN（带轮询重试）。

        真机调试（2026-10-09）：点「返回首页」后主页设备列表需要
        渲染时间，立即查询 `tvDeviceName` 会抛
        `PocoNoSuchNodeException`。因此先等主页加载，再在 timeout
        内轮询设备列表直至包含 SN。

        :param sn: 设备 SN / 型号
        :raises ElementNotFoundError: 首页设备列表在超时内未含该 SN
        """
        # 复用已有 CloudEdgeMainPage 检查设备列表
        main_page = CloudEdgeMainPage(self.poco, self.udid)
        if not main_page.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"「返回首页」后未能在 {timeout}s 内进入主页"
            )
        deadline = time.time() + timeout
        last_devices: list = []
        while time.time() < deadline:
            try:
                last_devices = main_page.get_device_list()
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"设备列表暂不可查（渲染中）：{exc}")
                last_devices = []
            if sn in last_devices:
                logger.info(f"主页设备列表断言通过：含 SN={sn!r}")
                return
            time.sleep(2.0)
        raise ElementNotFoundError(
            f"主页设备列表应含 SN={sn!r}，实际：{last_devices}"
        )
