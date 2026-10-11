"""智能门铃 Chime Base 解绑设备页 PO — jingle_unbind_channel。

入口：通用设置页点击「解绑子设备」（layout_jingle_unbind）。
Activity：JingleUnbindChannelActivity
（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「解绑设备」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- layout_delete 容器 + btn_delete（'删除设备'）

⚠️ 安全红线：btn_delete 为解绑/删除入口，点击后进入删除确认流程，
本 PO 永不点击该按钮，仅提供页面识别与按钮可见性断言；
解绑流程不在测试范围（会破坏被测设备绑定关系）。
"""

from __future__ import annotations

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()


class JingleUnbindChannelPage(JingleSubPageBase):
    """解绑设备页（JingleUnbindChannelActivity，标题='解绑设备'）。

    仅识别 + 返回；btn_delete 永不点击（安全红线）。
    """

    TITLE_TEXT = "解绑设备"
    ACTIVITY_KEYWORD = "JingleUnbindChannelActivity"

    # ==================== 定位器 ====================
    LAYOUT_DELETE = {"name": RID + "layout_delete"}   # 删除按钮容器
    BTN_DELETE = {"name": RID + "btn_delete"}         # 「删除设备」按钮（永不点击）

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def is_delete_button_visible(self) -> bool:
        """断言「删除设备」按钮在屏（仅可见性判断，不点击）。"""
        try:
            visible = (self.exists(self.BTN_DELETE)
                       and self.get_text(self.BTN_DELETE) == "删除设备")
        except Exception:  # noqa: BLE001 页面切换中节点瞬时不可查
            return False
        if visible:
            logger.debug("解绑页：「删除设备」按钮在屏（按约定不点击）")
        return visible
