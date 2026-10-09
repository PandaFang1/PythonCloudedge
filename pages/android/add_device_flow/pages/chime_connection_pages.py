"""Chime Base 添加流程 — 配网完成阶段 PO。

包含 2 个页面：
1. `ChimeConnectingPage` — 「连接网络」页面（转圈）
2. `ChimeSuccessPage` — 「连接成功」页面（「下一步」+「完成」）
"""

from __future__ import annotations

import time

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


TEXT_NEXT = "下一步"
TEXT_DONE = "完成"
TEXT_CONNECTING_KEYWORDS = ("连接", "配网", "正在", "联网")
TEXT_SUCCESS_KEYWORDS = ("成功", "完成", "已添加")


class ChimeConnectingPage(BasePage):
    """「连接网络」页面（转圈等待设备入网）。"""

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    # 转圈进度条（不同设备 SDK 节点不同，placeholder）
    PB_LOADING = {"name": "com.cloudedge.smarteye:id/pb_loading"}
    # 转圈消失后可能出现的「成功」标记
    TV_SUCCESS_HINT = {"name": "com.cloudedge.smarteye:id/tv_success_hint"}

    def wait_for_page_loaded(self, timeout: float = 15.0) -> bool:
        """等待「连接网络」页加载完成（标题含「连接/配网/正在」等）。"""
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

    def wait_connected(self, timeout: float = 90.0) -> bool:
        """等待连接完成（转圈消失 或 出现成功标记）。"""
        return self.wait_for_element_disappear(self.PB_LOADING, timeout=timeout)


class ChimeSuccessPage(BasePage):
    """「连接成功」页面（点击「下一步」→「完成」）。"""

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    BTN_NEXT = {"name": "com.cloudedge.smarteye:id/btn_next", "text": TEXT_NEXT}
    BTN_DONE = {"name": "com.cloudedge.smarteye:id/btn_done", "text": TEXT_DONE}

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

    def click_next(self) -> None:
        """点击「下一步」（进入安装指引页）。"""
        self.click(self.BTN_NEXT)
        logger.info("成功页：已点击「下一步」")

    def click_finish(self, timeout: float = 15.0) -> None:
        """点击「完成」（进入网络诊断页）。"""
        if not self.wait_for_element(self.BTN_DONE, timeout=timeout):
            logger.warning("「完成」按钮未出现，可能流程已结束")
            return
        self.click(self.BTN_DONE)
        logger.info("成功页：已点击「完成」")
