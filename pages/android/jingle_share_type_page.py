"""智能门铃 Chime Base 分享方式页 PO — jingle_share_type。

入口：设备分享页点击「添加」（layoutAdd）。
Activity：ShareTypeActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备分享」+ Activity 关键字（与父页同标题，靠
Activity 关键字区分；2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- tv_qr_code_share：方式一「扫描二维码」
  （iv_icon 图标 + tv_title 标题 + iv_pro_check）
- tv_account_share：方式二「输入账号」
  （iv_icon_2 图标 + tv_title_2 标题）
- swipe_refresh_layout / ll_empty：最近联系人列表（空态 '暂无联系人'）

限制（2026-10-11 真机验证）：
- 点击两种方式会进入更深层页面（二维码页 / 账号输入页），
  该层级未探测分类，本 PO 暂不提供进入方法，仅提供识别与读取
"""

from __future__ import annotations

from typing import List

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()


class JingleShareTypePage(JingleSubPageBase):
    """分享方式页（ShareTypeActivity，标题='设备分享'）。"""

    TITLE_TEXT = "设备分享"
    ACTIVITY_KEYWORD = "ShareTypeActivity"

    # ==================== 定位器 ====================
    LAYOUT_QR_CODE = {"name": RID + "tv_qr_code_share"}   # 「扫描二维码」方式
    TV_QR_TITLE = {"name": RID + "tv_title"}              # 方式一标题
    LAYOUT_ACCOUNT = {"name": RID + "tv_account_share"}   # 「输入账号」方式
    TV_ACCOUNT_TITLE = {"name": RID + "tv_title_2"}       # 方式二标题
    LAYOUT_RECENT = {"name": RID + "swipe_refresh_layout"}  # 最近联系人区
    TV_EMPTY = {"name": RID + "ll_empty"}                 # 联系人空态

    QR_CODE_SHARE_TEXT = "扫描二维码"
    ACCOUNT_SHARE_TEXT = "输入账号"
    EMPTY_TEXT = "暂无联系人"

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_share_types(self) -> List[str]:
        """读取两种分享方式标题。

        注意：方式一标题 id（tv_title）与工具栏标题撞名，poco 按
        name 匹配会先命中工具栏，因此方式一改用文本匹配断言
        （2026-10-11 真机验证发现）。

        :return: 如 ['扫描二维码', '输入账号']
        """
        types = []
        if self.poco(text=self.QR_CODE_SHARE_TEXT).exists():
            types.append(self.QR_CODE_SHARE_TEXT)
        if self.exists(self.TV_ACCOUNT_TITLE):
            types.append(self.get_text(self.TV_ACCOUNT_TITLE))
        logger.debug(f"分享方式页：可选方式 {types}")
        return types

    def is_recent_contact_empty(self) -> bool:
        """判定最近联系人是否为空态（ll_empty 在屏）。"""
        return self.exists(self.TV_EMPTY)
