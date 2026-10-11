"""智能门铃 Chime Base 通用设置页 PO — jingle_general。

入口：jingle 设置页列表点击「通用设置」。
Activity：GeneralSettingActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「通用设置」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump + 行为验证）：
- layout_led + switch_led：工作指示灯开关
- layout_install_guide：「安装指引」入口（→ 3 页翻页流）
- layout_jingle_unbind：「解绑子设备」入口（→ 解绑设备页）
- layout_time_settings / layout_time_setting + switch_time_format：
  12 小时制开关

限制（2026-10-11 真机验证）：
- switch_led / switch_time_format 的 checked 属性恒 False，
  状态断言无可靠 UI 依据（如需断言请用截图比对）
- 工作指示灯切换后的「设置成功」为系统 Toast，poco 不可见
"""

from __future__ import annotations

from pages.android.jingle_install_guide_page import JingleInstallGuidePage
from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.android.jingle_unbind_channel_page import JingleUnbindChannelPage
from pages.base_page import ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleGeneralPage(JingleSubPageBase):
    """通用设置页（GeneralSettingActivity，标题='通用设置'）。"""

    TITLE_TEXT = "通用设置"
    ACTIVITY_KEYWORD = "GeneralSettingActivity"

    # ==================== 定位器 ====================
    LAYOUT_LED = {"name": RID + "layout_led"}               # 工作指示灯行
    SWITCH_LED = {"name": RID + "switch_led"}               # 工作指示灯开关
    ENTRY_INSTALL_GUIDE = {"name": RID + "layout_install_guide"}  # 安装指引
    ENTRY_JINGLE_UNBIND = {"name": RID + "layout_jingle_unbind"}  # 解绑子设备
    LAYOUT_TIME_SETTING = {"name": RID + "layout_time_setting"}   # 12小时制行
    SWITCH_TIME_FORMAT = {"name": RID + "switch_time_format"}     # 12小时制开关

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 开关 ====================

    def toggle_work_led(self) -> "JingleGeneralPage":
        """点击工作指示灯开关（切换当前状态）。

        真机验证（2026-10-11）：切换后提示「设置成功」为系统 Toast，
        poco accessibility 树不可见，无法自动断言；
        switch 的 checked 属性恒 False，状态断言请用截图比对。

        :return: self（支持链式调用）
        :raises ElementNotFoundError: 开关不在屏
        """
        if not self.exists(self.SWITCH_LED):
            raise ElementNotFoundError("工作指示灯开关不在屏")
        self.click(self.SWITCH_LED)
        logger.info("通用设置页：已点击工作指示灯开关（提示 Toast 不可见）")
        return self

    def toggle_time_format(self) -> "JingleGeneralPage":
        """点击 12 小时制开关（切换当前状态）。

        ⚠️ switch 的 checked 属性恒 False（真机验证），无可靠状态
        读取方法；状态断言请用截图比对。

        :return: self（支持链式调用）
        :raises ElementNotFoundError: 开关不在屏
        """
        if not self.exists(self.SWITCH_TIME_FORMAT):
            raise ElementNotFoundError("12小时制开关不在屏")
        self.click(self.SWITCH_TIME_FORMAT)
        logger.info("通用设置页：已点击 12 小时制开关")
        return self

    # ==================== 下级页面入口 ====================

    def open_install_guide_page(self) -> JingleInstallGuidePage:
        """点击「安装指引」，进入安装指引页（3 页翻页流）。支持链式调用。

        :raises ElementNotFoundError: 点击后未进入指引页
        """
        self.click(self.ENTRY_INSTALL_GUIDE)
        logger.info("通用设置页：已点击「安装指引」")
        guide = JingleInstallGuidePage(self.poco, self.udid)
        if not guide.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                "点击「安装指引」后未进入指引页"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return guide

    def open_unbind_page(self) -> JingleUnbindChannelPage:
        """点击「解绑子设备」，进入解绑设备页。支持链式调用。

        解绑页仅识别与返回，「删除设备」按钮永不点击（安全红线）。

        :raises ElementNotFoundError: 点击后未进入解绑页
        """
        self.click(self.ENTRY_JINGLE_UNBIND)
        logger.info("通用设置页：已点击「解绑子设备」")
        unbind = JingleUnbindChannelPage(self.poco, self.udid)
        if not unbind.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                "点击「解绑子设备」后未进入解绑页"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return unbind
