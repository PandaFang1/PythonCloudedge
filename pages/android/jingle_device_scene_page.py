"""智能门铃 Chime Base 设备使用场景页 PO — jingle_device_scene。

入口：设备信息页点击「设备使用场景」（layout_device_scene）。
Activity：DeviceSceneActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备使用场景」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- recyclerView：12 个场景标签（两列宫格），定位靠 tvName 文本
  （厨房安防/客厅安防/卧室安防/看老人/看宠物/看小孩/门口安防/
   庭院安防/车库安防/农场安防/门店安防）
- tvSave：底部「保存」按钮

限制（2026-10-11 真机验证）：
- 场景标签 selected 属性恒 False，选中态无 UI 断言依据；
  保存后可通过重进页面或设备信息页间接验证
"""

from __future__ import annotations

from typing import List

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()

# 全部可选场景（2026-10-10 真机 dump 验证，两列宫格顺序）
ALL_SCENES: List[str] = [
    "厨房安防", "客厅安防", "卧室安防", "看老人",
    "看宠物", "看小孩", "门口安防", "庭院安防",
    "车库安防", "农场安防", "门店安防",
]


class JingleDeviceScenePage(JingleSubPageBase):
    """设备使用场景页（DeviceSceneActivity，标题='设备使用场景'）。"""

    TITLE_TEXT = "设备使用场景"
    ACTIVITY_KEYWORD = "DeviceSceneActivity"

    # ==================== 定位器 ====================
    TV_SAVE = {"name": RID + "tvSave"}   # 底部「保存」按钮

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_available_scenes(self) -> List[str]:
        """读取当前可见的场景标签列表（宫格内 tvName 文本）。

        :return: 场景名称列表（如 ['厨房安防', '客厅安防', ...]）
        """
        proxy = self.poco(RID + "tvName")
        scenes = [proxy[i].attr("text") for i in range(len(proxy))]
        logger.debug(f"使用场景页：可见场景 {scenes}")
        return scenes

    def select_scene(self, scene: str) -> "JingleDeviceScenePage":
        """点击指定场景标签。

        ⚠️ 仅选中不保存；tvSave 保存后为真实写入，验证后需恢复。

        :param scene: 场景名称（如 '看宠物'）
        :return: self（支持链式调用）
        :raises OperationFailedError: 场景名不在可选列表
        """
        if scene not in ALL_SCENES:
            raise OperationFailedError(
                f"场景 {scene!r} 不在可选列表 {ALL_SCENES}"
            )
        self.click({"text": scene})
        logger.info(f"使用场景页：已点击场景 {scene!r}")
        return self

    def save(self) -> "JingleDeviceScenePage":
        """点击底部「保存」（真实写入设备配置）。"""
        self.click(self.TV_SAVE)
        logger.info("使用场景页：已点击「保存」")
        return self
