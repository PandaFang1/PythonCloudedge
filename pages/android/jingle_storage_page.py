"""智能门铃 Chime Base 存储管理页 PO — jingle_storage。

入口：jingle 设置页列表点击「存储管理」。
Activity：SdCardActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「存储管理」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump + 行为验证）：
- tv_sdcard：'存储卡容量' 标题
- tv_progress_percent：容量占用百分比（如 '27%'）
- tv_capacity：容量大小（如 '59.464G'）
- tv_remaining_capacity：剩余容量（如 '43.549G'）
- tv_warning：格式化警告文案
- btn_format：'格式化' 按钮（位于页面下方，首屏可能需上滑）
- 格式化确认弹框：title='提示' / message（警告文案）/
  negativeButton='取消' / positiveButton='确定'

⚠️ 安全红线：格式化确认弹框的「确定」永不点击（会清除 SD 卡全部
数据），本 PO 只提供取消路径。
"""

from __future__ import annotations

import time

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleStoragePage(JingleSubPageBase):
    """存储管理页（SdCardActivity，标题='存储管理'）。"""

    TITLE_TEXT = "存储管理"
    ACTIVITY_KEYWORD = "SdCardActivity"

    # ==================== 定位器 ====================
    TV_SDCARD = {"name": RID + "tv_sdcard"}                 # '存储卡容量'
    TV_PROGRESS_PERCENT = {"name": RID + "tv_progress_percent"}  # 占用百分比
    TV_CAPACITY = {"name": RID + "tv_capacity"}             # 容量大小
    TV_REMAINING_CAPACITY = {"name": RID + "tv_remaining_capacity"}  # 剩余容量
    TV_WARNING = {"name": RID + "tv_warning"}               # 格式化警告
    BTN_FORMAT = {"name": RID + "btn_format"}               # '格式化'

    # ==================== 格式化确认弹框 ====================
    DIALOG_TITLE = {"name": RID + "title"}                  # '提示'
    DIALOG_MESSAGE = {"name": RID + "message"}              # 警告文案
    DIALOG_BTN_CANCEL = {"name": RID + "negativeButton"}    # '取消'
    DIALOG_BTN_CONFIRM = {"name": RID + "positiveButton"}   # '确定'（永不点击）

    DIALOG_TITLE_TEXT = "提示"

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 容量信息 getter ====================

    def get_capacity_percent(self) -> str:
        """读取容量占用百分比（如 '27%'）。"""
        return self.get_text(self.TV_PROGRESS_PERCENT)

    def get_capacity_total(self) -> str:
        """读取容量大小（如 '59.464G'）。"""
        return self.get_text(self.TV_CAPACITY)

    def get_capacity_remaining(self) -> str:
        """读取剩余容量（如 '43.549G'）。"""
        return self.get_text(self.TV_REMAINING_CAPACITY)

    def is_sdcard_present(self) -> bool:
        """判定存储卡信息是否在屏（有卡时容量字段可见）。"""
        return self.exists(self.TV_PROGRESS_PERCENT)

    # ==================== 格式化（只取消） ====================

    def _ensure_format_button_visible(self) -> bool:
        """确保格式化按钮在屏（必要时上滑查找）。"""
        if self.exists(self.BTN_FORMAT):
            return True
        for _ in range(3):
            self.poco.swipe([0.5, 0.75], [0.5, 0.35], duration=0.6)
            time.sleep(1.0)
            if self.exists(self.BTN_FORMAT):
                return True
        return False

    def click_format_and_cancel(self) -> "JingleStoragePage":
        """点击「格式化」并在确认弹框点「取消」。

        ⚠️ 安全红线：弹框「确定」（positiveButton）永不点击，
        会清除 SD 卡全部数据；本方法只走取消路径。

        :return: self（支持链式调用）
        :raises ElementNotFoundError: 按钮缺失或确认弹框未出现
        """
        if not self._ensure_format_button_visible():
            raise ElementNotFoundError("格式化按钮不在屏（上滑后仍未找到）")
        self.click(self.BTN_FORMAT)
        logger.info("存储管理页：已点击「格式化」")

        # 等待确认弹框（title='提示' + negativeButton 在屏）
        deadline = time.time() + 10
        shown = False
        while time.time() < deadline:
            try:
                if (self.exists(self.DIALOG_TITLE)
                        and self.get_text(self.DIALOG_TITLE)
                        == self.DIALOG_TITLE_TEXT
                        and self.exists(self.DIALOG_BTN_CANCEL)):
                    shown = True
                    break
            except Exception:  # noqa: BLE001 弹框出现中节点瞬时不可查
                pass
            time.sleep(0.5)
        if not shown:
            raise ElementNotFoundError("点击「格式化」后确认弹框未出现")

        self.click(self.DIALOG_BTN_CANCEL)
        self.wait_for_element_disappear(self.DIALOG_TITLE, timeout=10)
        logger.info("存储管理页：格式化弹框已点「取消」（确定永不点击）")
        return self
