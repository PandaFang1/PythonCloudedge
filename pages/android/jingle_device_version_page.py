"""智能门铃 Chime Base 设备版本页 PO — jingle_device_version。

入口：设备信息页点击「设备版本」（layout_firmware_version）。
Activity：DeviceVersionActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备版本」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- img_camera / tv_device_name：设备图标与名称
- tv_current_version / tv_latest_version：当前 / 最新固件版本
- ll_auto_update + switch_auto：固件自动升级开关
- tv_auto_upgrade_des：自动升级说明
- tv_tips：升级提示（如 '您已是最新版本，无需更新'）
- btn_upgrade：底部按钮（无更新时文本为 '返回'）

限制（2026-10-11 真机验证）：
- switch_auto 的 checked 属性不可靠，不提供状态读取；
  本页为只读信息页，固件升级类操作不在测试范围
"""

from __future__ import annotations

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeviceVersionPage(JingleSubPageBase):
    """设备版本页（DeviceVersionActivity，标题='设备版本'）。"""

    TITLE_TEXT = "设备版本"
    ACTIVITY_KEYWORD = "DeviceVersionActivity"

    # ==================== 定位器 ====================
    TV_DEVICE_NAME = {"name": RID + "tv_device_name"}
    TV_CURRENT_VERSION = {"name": RID + "tv_current_version"}
    TV_LATEST_VERSION = {"name": RID + "tv_latest_version"}
    LAYOUT_AUTO_UPDATE = {"name": RID + "ll_auto_update"}   # 自动升级开关行
    SWITCH_AUTO = {"name": RID + "switch_auto"}             # 固件自动升级开关
    TV_TIPS = {"name": RID + "tv_tips"}                     # 升级提示
    BTN_UPGRADE = {"name": RID + "btn_upgrade"}             # 底部按钮

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_device_name(self) -> str:
        """读取设备名称。"""
        return self.get_text(self.TV_DEVICE_NAME)

    def get_current_version(self) -> str:
        """读取当前固件版本（如 '6.2.0.20260921'）。"""
        return self.get_text(self.TV_CURRENT_VERSION)

    def get_latest_version(self) -> str:
        """读取最新固件版本。"""
        return self.get_text(self.TV_LATEST_VERSION)

    def get_upgrade_tip(self) -> str:
        """读取升级提示文案（如 '您已是最新版本，无需更新'）。"""
        return self.get_text(self.TV_TIPS)

    def get_upgrade_button_text(self) -> str:
        """读取底部按钮文本（无更新时为 '返回'）。"""
        return self.get_text(self.BTN_UPGRADE)
