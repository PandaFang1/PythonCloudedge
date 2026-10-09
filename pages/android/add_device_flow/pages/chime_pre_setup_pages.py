"""Chime Base 添加流程 — 物理准备阶段 PO。

包含 2 个页面（均位于 `PowerOnActivity`，通过 tv_des_title 区分）：
1. `ChimeInstallLocationPage` — 「选择 Chime Base 页面」（提示安装位置，tv_power_on_title）
2. `ChimePowerSupplyPage` — 「接入电源」提示页面（tv_des_title）

定位器已替换为真机 dump 提取的真实 resource-id。
"""

from __future__ import annotations

import time
from typing import Optional

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


# 通用按钮文本（resource-id 已有，但仍可在文本断言中使用）
TEXT_NEXT = "下一步"
TEXT_DONE = "完成"
TEXT_CONFIRM = "确定"


class ChimeInstallLocationPage(BasePage):
    """「选择 Chime Base 页面」（提示安装位置）。

    页面职责：展示 Chime Base 安装位置建议，用户确认后点击「下一步」。
    PowerOnActivity 第一个引导页。
    """

    # 真机 dump 提取的资源 id（PAGE 1 dump）
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # "添加Chime Base"
    SDV_SKETCH = {"name": "com.cloudedge.smarteye:id/sdv_sketch"}  # 示意图
    TV_POWER_ON_TITLE = {"name": "com.cloudedge.smarteye:id/tv_power_on_title"}  # "安装位置"
    TV_POWER_ON_DES = {"name": "com.cloudedge.smarteye:id/tv_power_on_des"}  # 描述
    LAYOUT_NEXT = {"name": "com.cloudedge.smarteye:id/layout_next"}  # 下一步容器
    TV_NEXT = {"name": "com.cloudedge.smarteye:id/tv_next", "text": TEXT_NEXT}
    IV_BACK = {"name": "com.cloudedge.smarteye:id/iv_back"}  # 返回按钮

    EXPECTED_TITLE_KEYWORDS = ("安装位置", "安装", "位置")

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待页面加载完成（tv_power_on_title 出现且含「安装位置」）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_POWER_ON_TITLE):
                title = self.get_text(self.TV_POWER_ON_TITLE)
                if any(kw in title for kw in self.EXPECTED_TITLE_KEYWORDS):
                    logger.debug(f"Chime 安装位置页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 安装位置页在 {timeout}s 内未加载")
        return False

    def click_next(self) -> None:
        """点击底部「下一步」按钮（精确文本「下一步」）。"""
        self.click(self.TV_NEXT)
        logger.info("Chime 安装位置页：已点击「下一步」")


class ChimePowerSupplyPage(BasePage):
    """「接入电源」提示页面（PowerOnActivity 第二个引导页）。

    页面职责：提示用户给 Chime Base 接入电源，确认后点击「下一步」。
    与安装位置页共享同一 Activity（PowerOnActivity），通过 tv_des_title 区分。
    """

    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    TV_DES_TITLE = {"name": "com.cloudedge.smarteye:id/tv_des_title"}  # "接入电源"
    TV_DES = {"name": "com.cloudedge.smarteye:id/tv_des"}  # 描述
    LAYOUT_NEXT = {"name": "com.cloudedge.smarteye:id/layout_next"}
    TV_NEXT = {"name": "com.cloudedge.smarteye:id/tv_next", "text": TEXT_NEXT}
    IV_BACK = {"name": "com.cloudedge.smarteye:id/iv_back"}
    # 问题反馈（可能存在「问题」按钮）
    TV_PROBLEM2 = {"name": "com.cloudedge.smarteye:id/tv_problem2"}
    TV_PROBLEM3 = {"name": "com.cloudedge.smarteye:id/tv_problem3"}

    EXPECTED_DES_TITLE_KEYWORDS = ("接入电源", "电源", "上电")

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待页面加载完成（tv_des_title 出现且含「电源」）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_DES_TITLE):
                title = self.get_text(self.TV_DES_TITLE)
                if any(kw in title for kw in self.EXPECTED_DES_TITLE_KEYWORDS):
                    logger.debug(f"Chime 电源页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 电源页在 {timeout}s 内未加载")
        return False

    def click_next(self) -> None:
        """点击底部「下一步」按钮。"""
        self.click(self.TV_NEXT)
        logger.info("Chime 电源页：已点击「下一步」")
