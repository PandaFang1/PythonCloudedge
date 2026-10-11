"""智能门铃 Chime Base 位置管理页 PO — jingle_device_location。

入口：设备信息页点击「位置管理」（layout_location_manager）。
Activity：DeviceAssignmentActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备分配管理」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- 顶部工具栏：iv_back / tv_title（'设备分配管理'）/ tv_right_text（'确定'）
- tv_family_title：分组标题（'我的家庭'）
- 家庭列表项：tvRoomName（家庭名）/ tvDeviceNumber（'1个设备'）/
  iv_select（选择圈）
- layoutCreateFamily：底部「新建家庭」入口（下级页面未探测，暂不提供
  进入方法）
"""

from __future__ import annotations

from typing import List, Tuple

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeviceLocationPage(JingleSubPageBase):
    """位置管理页（DeviceAssignmentActivity，标题='设备分配管理'）。"""

    TITLE_TEXT = "设备分配管理"
    ACTIVITY_KEYWORD = "DeviceAssignmentActivity"

    # ==================== 定位器 ====================
    BTN_CONFIRM = {"name": RID + "tv_right_text"}            # 右上角「确定」
    TV_FAMILY_TITLE = {"name": RID + "tv_family_title"}      # 分组标题
    LAYOUT_CREATE_FAMILY = {"name": RID + "layoutCreateFamily"}  # 「新建家庭」入口

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_family_list(self) -> List[Tuple[str, str]]:
        """读取家庭列表（名称 + 设备数）。

        :return: [(家庭名, 设备数文本), ...]，如 [('方小C的家', '1个设备')]
        """
        names = self.poco(RID + "tvRoomName")
        numbers = self.poco(RID + "tvDeviceNumber")
        count = min(len(names), len(numbers))
        families = [
            (names[i].attr("text"), numbers[i].attr("text"))
            for i in range(count)
        ]
        logger.debug(f"位置管理页：家庭列表 {families}")
        return families

    def select_family(self, name: str) -> "JingleDeviceLocationPage":
        """点击指定家庭（勾选选择圈）。

        ⚠️ 仅选择不提交；确认需点击右上角「确定」（真实写入）。

        :param name: 家庭名称
        :return: self（支持链式调用）
        """
        self.click({"text": name})
        logger.info(f"位置管理页：已点击家庭 {name!r}")
        return self

    def confirm(self) -> "JingleDeviceLocationPage":
        """点击右上角「确定」（真实写入设备位置分配）。"""
        self.click(self.BTN_CONFIRM)
        logger.info("位置管理页：已点击「确定」")
        return self
