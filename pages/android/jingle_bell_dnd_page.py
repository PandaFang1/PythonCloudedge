"""智能门铃 Chime Base 铃铛勿扰页 PO — jingle_bell_dnd。

入口：jingle 设置页宫格点击「铃铛勿扰」。
Activity：SleepTimeListActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「铃铛勿扰」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump 验证）：
- tv_jingle_des：勿扰说明文案
- layout_time_list：时间段列表容器
- empty_view：空态（'当前暂无时间段'，无 id TextView）
- layout_bottom_view + btn_add：底部「添加时间段」入口
"""

from __future__ import annotations

from pages.android.jingle_sleep_time_add_page import JingleSleepTimeAddPage
from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleBellDndPage(JingleSubPageBase):
    """铃铛勿扰页（SleepTimeListActivity，标题='铃铛勿扰'）。"""

    TITLE_TEXT = "铃铛勿扰"
    ACTIVITY_KEYWORD = "SleepTimeListActivity"

    # ==================== 定位器 ====================
    TV_DES = {"name": RID + "tv_jingle_des"}           # 勿扰说明文案
    LAYOUT_TIME_LIST = {"name": RID + "layout_time_list"}  # 时间段列表容器
    EMPTY_VIEW = {"name": RID + "empty_view"}          # 空态容器
    LAYOUT_BOTTOM = {"name": RID + "layout_bottom_view"}  # 底部按钮容器
    BTN_ADD = {"name": RID + "btn_add"}                # '添加时间段'

    EMPTY_TEXT = "当前暂无时间段"

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_description(self) -> str:
        """读取勿扰说明文案。"""
        return self.get_text(self.TV_DES)

    def is_time_list_empty(self) -> bool:
        """判定时间段列表是否为空（空态文本在屏）。"""
        try:
            return self.exists(self.EMPTY_VIEW) and (
                self.poco(text=self.EMPTY_TEXT).exists()
            )
        except Exception:  # noqa: BLE001 列表加载中节点瞬时不可查
            return False

    def open_sleep_time_add_page(self) -> JingleSleepTimeAddPage:
        """点击「添加时间段」，进入添加时间段页。支持链式调用。

        :raises ElementNotFoundError: 点击后未进入添加页
        """
        self.click(self.BTN_ADD)
        logger.info("铃铛勿扰页：已点击「添加时间段」")
        add_page = JingleSleepTimeAddPage(self.poco, self.udid)
        if not add_page.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                "点击「添加时间段」后未进入添加页"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return add_page

    def open_sleep_time_edit_page(self, item_text: str) -> JingleSleepTimeAddPage:
        """点击时间段列表项，进入编辑时间段页（编辑模式）。

        编辑模式提供「删除计划」入口（恢复/清理勿扰时间段用）。

        :param item_text: 列表项时间文本（如 '01:00 ~ 02:00'）
        :return: 编辑模式的时间段页实例
        :raises ElementNotFoundError: 列表项不存在或点击后未进入编辑页
        """
        if not self.poco(text=item_text).exists():
            raise ElementNotFoundError(f"勿扰时间段列表项 {item_text!r} 不存在")
        self.poco(text=item_text).click()
        logger.info(f"铃铛勿扰页：已点击时间段项 {item_text!r}")
        edit_page = JingleSleepTimeAddPage(self.poco, self.udid)
        if not edit_page.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                "点击时间段项后未进入编辑页"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return edit_page
