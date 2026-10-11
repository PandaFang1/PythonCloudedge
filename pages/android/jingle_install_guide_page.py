"""智能门铃 Chime Base 安装指引页 PO — jingle_install_guide。

入口：通用设置页点击「安装指引」（layout_install_guide）。
共 3 页翻页流（2026-10-11 真机验证）：
- 第 1 页 GuideRightPlacePicActivity（识别页）：viewPager 轮播 +
  iv_guide 指引图 + tv_content 文案 + indicator 页指示器 +
  tv_next_vp「下一步」
- 第 2 页 GuideRightPlaceActivity：iv_install_guide 指引图 +
  iv_sound_img + tv_des_title 文案 + layout_next/next「下一步」
- 第 3 页 NetworkDiagnosticActivity（标题变「网络诊断」）：
  iv_wifi_strength 信号图标 + tv_des_title='WIFI信号强度' +
  tv_desc_wifi_strength 信号值 + tv_desc_content 诊断结论 +
  layout_next/next「完成」

识别点：标题「安装指引」+ Activity 关键字（GuideRightPlacePicActivity，
仅第 1 页满足；第 2/3 页 Activity 不同、第 3 页标题也不同，
由 next_page() 内部按控件切换处理）。

安全约定：末页「完成」按钮永不点击（会触发安装完成/后续流程）。
"""

from __future__ import annotations

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()


class JingleInstallGuidePage(JingleSubPageBase):
    """安装指引页（3 页翻页流，入口页 GuideRightPlacePicActivity）。"""

    TITLE_TEXT = "安装指引"
    ACTIVITY_KEYWORD = "GuideRightPlacePicActivity"

    # ==================== 第 1 页（识别页）定位器 ====================
    VIEW_PAGER = {"name": RID + "viewPager"}
    IV_GUIDE = {"name": RID + "iv_guide"}
    TV_CONTENT = {"name": RID + "tv_content"}
    INDICATOR = {"name": RID + "indicator"}
    BTN_NEXT_1 = {"name": RID + "tv_next_vp"}     # 第 1 页「下一步」

    # ==================== 第 2/3 页定位器 ====================
    LAYOUT_NEXT = {"name": RID + "layout_next"}   # 下一步按钮容器
    BTN_NEXT = {"name": RID + "next"}             # 第 2/3 页按钮
    TV_DES_TITLE = {"name": RID + "tv_des_title"}
    TV_WIFI_STRENGTH = {"name": RID + "tv_desc_wifi_strength"}  # 第 3 页信号值
    TV_DESC_CONTENT = {"name": RID + "tv_desc_content"}         # 第 3 页诊断结论

    BTN_LAST_TEXT = "完成"   # 末页按钮文本（永不点击）

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_guide_content(self) -> str:
        """读取当前指引文案（第 1 页 tv_content / 第 2、3 页 tv_des_title）。"""
        if self.exists(self.TV_CONTENT):
            return self.get_text(self.TV_CONTENT)
        return self.get_text(self.TV_DES_TITLE)

    def is_last_page(self) -> bool:
        """判定是否已翻至末页（下一步按钮文本为「完成」）。"""
        for btn in (self.BTN_NEXT, self.BTN_NEXT_1):
            try:
                if self.exists(btn):
                    return self.get_text(btn) == self.BTN_LAST_TEXT
            except Exception:  # noqa: BLE001 翻页动画期节点瞬时不可查
                continue
        return False

    def next_page(self) -> "JingleInstallGuidePage":
        """点击「下一步」翻页（第 1 页 tv_next_vp，第 2/3 页 next）。

        :return: self（支持链式调用）
        :raises OperationFailedError: 已在末页或按钮缺失
        """
        if self.is_last_page():
            raise OperationFailedError(
                "已在安装指引末页，「完成」按钮不点击（安全约定）"
            )
        if self.exists(self.BTN_NEXT_1):
            self.click(self.BTN_NEXT_1)
        elif self.exists(self.BTN_NEXT):
            self.click(self.BTN_NEXT)
        else:
            raise OperationFailedError("安装指引页未找到「下一步」按钮")
        logger.info("安装指引页：已翻页")
        return self

    def get_wifi_strength(self) -> str:
        """读取第 3 页 WiFi 信号强度（如 '强'）。"""
        return self.get_text(self.TV_WIFI_STRENGTH)

    def get_diagnostic_conclusion(self) -> str:
        """读取第 3 页诊断结论（如 '当前位置不错，可以安装无线铃铛。'）。"""
        return self.get_text(self.TV_DESC_CONTENT)
