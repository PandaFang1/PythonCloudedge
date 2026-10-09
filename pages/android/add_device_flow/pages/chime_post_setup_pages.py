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
    """「安装指引」页面（多张图片引导，最后一步「下一步」）。"""

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    BTN_NEXT = {"name": "com.cloudedge.smarteye:id/btn_next", "text": TEXT_NEXT}

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
    """「网络诊断」页面（底部「返回首页」+ 断言首页设备列表）。"""

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    BTN_BACK_HOME = {"name": "com.cloudedge.smarteye:id/btn_back_home", "text": TEXT_BACK_HOME}

    # 诊断结果展示区（占位符）
    TV_DIAGNOSTIC_RESULT = {"name": "com.cloudedge.smarteye:id/tv_diagnostic_result"}

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
        """断言已跳到首页且设备列表含指定 SN。

        :param sn: 设备 SN / 型号
        :raises ElementNotFoundError: 首页设备列表未含该 SN
        """
        # 复用已有 CloudEdgeMainPage 检查设备列表
        main_page = CloudEdgeMainPage(self.poco, self.udid)
        if not main_page.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"「返回首页」后未能在 {timeout}s 内进入主页"
            )
        devices = main_page.get_device_list() if hasattr(main_page, "get_device_list") else []
        if sn not in devices:
            raise ElementNotFoundError(
                f"主页设备列表应含 SN={sn!r}，实际：{devices}"
            )
        logger.info(f"主页设备列表断言通过：含 SN={sn!r}")
