"""智能门铃 Chime Base 添加时间段页 PO — jingle_sleep_time_add。

入口：
- 添加模式：铃铛勿扰页点击「添加时间段」（btn_add），标题「添加时间段」
- 编辑模式：铃铛勿扰页点击时间段列表项，标题「编辑时间段」
Activity：SleepTimeAddActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题（添加/编辑两种）+ Activity 关键字（真机 dump 验证）。

页面结构（2026-10-11 真机 dump + 行为验证）：
- tv_des：说明文案
- start_layout / text_start_time（'00:00'）/ iv_arrow_start：开启时间
- end_layout / text_end_time / iv_arrow_end：结束时间
- text_week（'重复'）+ layout_week_2 容器内 7 个星期项：
  layout_sun_2 ~ layout_sta_2（配 text_sun_check_2 等选中标记）
- 添加模式：底部 btn_add（'保存'）
- 编辑模式：右上 tv_right_text（'保存'）+ 底部 btn_delete（'删除计划'）

时间选择器（点击 start_layout / end_layout 弹出，同 Activity）：
- optionspicker：滚轮（options_hour 时轮 + options_min 分轮）
- btnCancel（'取消'）/ btnSubmit（'确定'）

行为要点（2026-10-11 真机验证）：
- 滚轮步长不稳定（单次向上滑 ≈ +1 或 +2 小时），设置起止时间的可靠
  策略是「end 同向多滑一次，保证 end > start」
- 同日内 start >= end 的时段会被 app 拒绝保存（停留本页不返回）
- 保存为真实写入，验证后用编辑模式「删除计划」恢复
"""

from __future__ import annotations

import time
from typing import Dict

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()

# 星期项定位器（2026-10-10 真机 dump 验证）
WEEKDAY_LOCATORS: Dict[str, dict] = {
    "日": {"name": RID + "layout_sun_2"},
    "一": {"name": RID + "layout_mon_2"},
    "二": {"name": RID + "layout_tue_2"},
    "三": {"name": RID + "layout_wen_2"},
    "四": {"name": RID + "layout_thu_2"},
    "五": {"name": RID + "layout_fri_2"},
    "六": {"name": RID + "layout_sta_2"},
}


class JingleSleepTimeAddPage(JingleSubPageBase):
    """添加/编辑时间段页（SleepTimeAddActivity）。

    添加模式标题='添加时间段'，编辑模式标题='编辑时间段'。
    """

    TITLE_TEXT = "添加时间段"
    EDIT_TITLE_TEXT = "编辑时间段"
    ACCEPT_TITLES = ("添加时间段", "编辑时间段")
    ACTIVITY_KEYWORD = "SleepTimeAddActivity"

    # ==================== 定位器 ====================
    TV_DES = {"name": RID + "tv_des"}
    LAYOUT_START = {"name": RID + "start_layout"}         # 开启时间行
    TEXT_START_TIME = {"name": RID + "text_start_time"}   # 开启时间值（'00:00'）
    LAYOUT_END = {"name": RID + "end_layout"}             # 结束时间行
    TEXT_END_TIME = {"name": RID + "text_end_time"}       # 结束时间值
    BTN_SAVE = {"name": RID + "btn_add"}                  # 添加模式底部「保存」

    # 编辑模式
    BTN_SAVE_TOP = {"name": RID + "tv_right_text"}        # 右上「保存」
    BTN_DELETE_PLAN = {"name": RID + "btn_delete"}        # 底部「删除计划」

    # 时间选择器（同 Activity 弹出）
    TIME_PICKER = {"name": RID + "optionspicker"}
    BTN_TIME_CANCEL = {"name": RID + "btnCancel"}         # 选择器「取消」
    BTN_TIME_SUBMIT = {"name": RID + "btnSubmit"}         # 选择器「确定」

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 页面识别（兼容添加/编辑两种标题） ====================

    def wait_for_page_loaded(self, timeout: float = 15.0) -> bool:
        """等待页面加载完成（标题为「添加时间段」或「编辑时间段」）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if (self.exists(self.TV_TITLE)
                        and self.get_text(self.TV_TITLE) in self.ACCEPT_TITLES
                        and self.ACTIVITY_KEYWORD in self.get_current_activity()):
                    logger.debug(
                        f"时间段页已加载：{self.get_text(self.TV_TITLE)!r}"
                        f"（{self.ACTIVITY_KEYWORD}）"
                    )
                    return True
            except Exception:  # noqa: BLE001 页面切换中元素可能瞬时不可查
                pass
            time.sleep(0.5)
        logger.warning(
            f"时间段页在 {timeout}s 内未加载完成"
            f"（当前 Activity={self.get_current_activity()}）"
        )
        return False

    def is_edit_mode(self) -> bool:
        """判定当前是否为编辑模式（标题='编辑时间段'）。"""
        try:
            return self.get_text(self.TV_TITLE) == self.EDIT_TITLE_TEXT
        except Exception:  # noqa: BLE001 页面切换中元素可能瞬时不可查
            return False

    # ==================== 业务方法 ====================

    def get_start_time(self) -> str:
        """读取开启时间文本（如 '00:00'）。"""
        return self.get_text(self.TEXT_START_TIME)

    def get_end_time(self) -> str:
        """读取结束时间文本（如 '00:00'）。"""
        return self.get_text(self.TEXT_END_TIME)

    def select_weekday(self, day: str) -> "JingleSleepTimeAddPage":
        """勾选指定星期（重复周期）。

        :param day: '日'/'一'/'二'/'三'/'四'/'五'/'六'
        :return: self（支持链式调用）
        :raises KeyError: 星期参数非法
        """
        locator = WEEKDAY_LOCATORS[day]
        self.click(locator)
        logger.info(f"时间段页：已点击星期「{day}」")
        return self

    def open_start_time_picker(self) -> "JingleSleepTimeAddPage":
        """点击开启时间行，弹出时间选择器。"""
        self.click(self.LAYOUT_START)
        logger.info("时间段页：已点击开启时间（弹出选择器）")
        return self

    def open_end_time_picker(self) -> "JingleSleepTimeAddPage":
        """点击结束时间行，弹出时间选择器。"""
        self.click(self.LAYOUT_END)
        logger.info("时间段页：已点击结束时间（弹出选择器）")
        return self

    def is_time_picker_shown(self) -> bool:
        """判定时间选择器是否在屏。"""
        return self.exists(self.TIME_PICKER)

    def cancel_time_picker(self) -> "JingleSleepTimeAddPage":
        """点击时间选择器「取消」并等待其消失。"""
        self.click(self.BTN_TIME_CANCEL)
        self.wait_for_element_disappear(self.TIME_PICKER, timeout=5)
        logger.info("时间段页：时间选择器已取消")
        return self

    def scroll_picker_hour_up(self, times: int = 1) -> "JingleSleepTimeAddPage":
        """在已打开的时间选择器上向上滚动时轮（值增加）。

        滚轮数字不在 accessibility 树，只能手势滚动；单次滚动步长
        不稳定（+1 或 +2 小时），需要精确值时以滚动后提交的实际
        文本为准。

        :param times: 滚动次数
        :return: self（支持链式调用）
        :raises OperationFailedError: 选择器未打开
        """
        if not self.is_time_picker_shown():
            from pages.base_page import OperationFailedError

            raise OperationFailedError("时间选择器未打开")
        hour = self.poco(RID + "options_hour")
        pos = hour.attr("pos")
        for _ in range(times):
            self.poco.swipe([pos[0], pos[1]], [pos[0], pos[1] - 0.05],
                            duration=0.4)
            time.sleep(0.8)
        logger.info(f"时间段页：时轮已向上滚动 {times} 次")
        return self

    def submit_time_picker(self) -> "JingleSleepTimeAddPage":
        """点击时间选择器「确定」。"""
        self.click(self.BTN_TIME_SUBMIT)
        self.wait_for_element_disappear(self.TIME_PICKER, timeout=5)
        logger.info("时间段页：时间选择器已确定")
        return self

    def save(self) -> "JingleSleepTimeAddPage":
        """点击保存（真实写入勿扰时间段，验证后需删除恢复）。

        添加模式点底部 btn_add，编辑模式点右上 tv_right_text。
        同日内 start >= end 的时段会被 app 拒绝（停留本页）。
        """
        btn = self.BTN_SAVE_TOP if self.is_edit_mode() else self.BTN_SAVE
        self.click(btn)
        logger.info("时间段页：已点击「保存」")
        return self

    def delete_plan(self) -> "JingleSleepTimeAddPage":
        """点击底部「删除计划」删除当前时间段（仅编辑模式）。

        删除后返回勿扰列表页。

        :return: self（支持链式调用）
        :raises OperationFailedError: 非编辑模式（按钮不存在）
        """
        if not self.exists(self.BTN_DELETE_PLAN):
            from pages.base_page import OperationFailedError

            raise OperationFailedError("「删除计划」按钮不在屏（需编辑模式）")
        self.click(self.BTN_DELETE_PLAN)
        logger.info("时间段页：已点击「删除计划」")
        return self
