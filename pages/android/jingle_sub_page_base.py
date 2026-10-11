"""jingle 设置子页面公共基类。

jingle 设置页（CameraSettingNewActivity）的各子设置页共用结构：
顶部工具栏（iv_back 返回 + tv_title 标题），返回后回到设置页。

子类职责（必须覆写的类属性）：
- ``TITLE_TEXT``：工具栏标题文本（如 "设备信息"）
- ``ACTIVITY_KEYWORD``：Activity 类名关键字（如 "DeviceInfoActivity"）

识别点约定（2026-10-10 真机 dump 验证）：标题文本 + Activity 关键字
双条件同时命中才判定加载完成，降低标题撞名 / 页面切换动画期误判。
"""

from __future__ import annotations

import time
from typing import Any

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()

# CloudEdge app resource-id 前缀
RID = "com.cloudedge.smarteye:id/"


class JingleSubPageBase(BasePage):
    """jingle 设置子页面公共基类（工具栏返回 + 双识别点等待）。"""

    # 子类必须覆写
    TV_BACK = {"name": RID + "iv_back"}        # 工具栏返回按钮
    TV_TITLE = {"name": RID + "tv_title"}      # 工具栏标题
    TITLE_TEXT = ""                            # 子类覆写：标题文本
    ACTIVITY_KEYWORD = ""                      # 子类覆写：Activity 类名关键字

    def __init__(self, poco: Any, udid: str = "") -> None:
        super().__init__(poco, udid)

    def wait_for_page_loaded(self, timeout: float = 15.0) -> bool:
        """等待子页面加载完成（标题文本 + Activity 关键字双识别点）。

        :param timeout: 等待超时（秒）
        :return: 加载完成返回 True
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if (self.exists(self.TV_TITLE)
                        and self.get_text(self.TV_TITLE) == self.TITLE_TEXT
                        and self.ACTIVITY_KEYWORD in self.get_current_activity()):
                    logger.debug(
                        f"子页面已加载：{self.TITLE_TEXT!r}"
                        f"（{self.ACTIVITY_KEYWORD}）"
                    )
                    return True
            except Exception:  # noqa: BLE001 页面切换中元素可能瞬时不可查
                pass
            time.sleep(0.5)
        logger.warning(
            f"子页面 {self.TITLE_TEXT!r} 在 {timeout}s 内未加载完成"
            f"（当前 Activity={self.get_current_activity()}）"
        )
        return False

    def back_to_setting_page(self) -> "JingleSubPageBase":
        """点击工具栏返回按钮，回到 jingle 设置页。

        仅执行返回动作；设置页就绪由调用方通过
        ``JingleSettingPage.wait_for_page_loaded()`` 验证。

        支持链式调用。
        """
        self.click(self.TV_BACK)
        logger.debug(f"子页面 {self.TITLE_TEXT!r}：已点击返回")
        return self
