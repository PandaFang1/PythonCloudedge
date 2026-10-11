"""智能门铃 Chime Base 设备分享页 PO — jingle_device_share。

入口：jingle 设置页宫格点击「设备分享」。
Activity：DeviceSettingShareActivity
（com.ppstrong.weeye.view.activity.setting.share）。
识别点：标题「设备分享」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（2026-10-11 真机 dump 验证）：
- layoutAdd：添加分享入口（→ 分享方式页 ShareTypeActivity）
- 未分享提示 / 分享视频引导（骨架期已验证的静态文案）
"""

from __future__ import annotations

from pages.android.jingle_share_type_page import JingleShareTypePage
from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeviceSharePage(JingleSubPageBase):
    """设备分享页（DeviceSettingShareActivity，标题='设备分享'）。"""

    TITLE_TEXT = "设备分享"
    ACTIVITY_KEYWORD = "DeviceSettingShareActivity"

    # ==================== 定位器 ====================
    LAYOUT_ADD = {"name": RID + "layoutAdd"}   # 添加分享入口

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def is_add_entry_visible(self) -> bool:
        """断言「添加」入口在屏。"""
        return self.exists(self.LAYOUT_ADD)

    def open_share_type_page(self) -> JingleShareTypePage:
        """点击「添加」，进入分享方式页。支持链式调用。

        分享方式页提供「扫描二维码 / 输入账号」两种方式识别；
        更深层页面未探测，暂不提供进入方法。

        :raises ElementNotFoundError: 点击后未进入分享方式页
        """
        self.click(self.LAYOUT_ADD)
        logger.info("设备分享页：已点击「添加」")
        type_page = JingleShareTypePage(self.poco, self.udid)
        if not type_page.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                "点击「添加」后未进入分享方式页"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return type_page
