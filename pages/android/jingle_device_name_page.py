"""智能门铃 Chime Base 设备名称页 PO — jingle_device_name。

入口：设备信息页点击「设备名称」（layout_device_name）。
Activity：DeviceNameActivity（com.ppstrong.weeye.view.activity.setting）。
识别点：标题「设备昵称」+ Activity 关键字（2026-10-10 真机 dump 验证）。

页面结构（真机 dump 验证）：
- 顶部工具栏：iv_back / tv_title（'设备昵称'）/ tv_right_text（'保存'）
- edt_device_name：名称输入框（当前设备昵称）
- img_delete：清空输入按钮
"""

from __future__ import annotations

from pages.android.jingle_sub_page_base import JingleSubPageBase, RID
from pages.base_page import OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeviceNamePage(JingleSubPageBase):
    """设备名称页（DeviceNameActivity，标题='设备昵称'）。"""

    TITLE_TEXT = "设备昵称"
    ACTIVITY_KEYWORD = "DeviceNameActivity"

    # ==================== 定位器 ====================
    EDT_NAME = {"name": RID + "edt_device_name"}    # 名称输入框
    BTN_CLEAR = {"name": RID + "img_delete"}        # 清空输入按钮
    BTN_SAVE = {"name": RID + "tv_right_text"}      # 右上角「保存」

    def __init__(self, poco, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 业务方法 ====================

    def get_name(self) -> str:
        """读取当前设备昵称（输入框文本）。"""
        return self.get_text(self.EDT_NAME)

    def set_name(self, name: str, save: bool = True) -> "JingleDeviceNamePage":
        """修改设备昵称：清空 → 输入 → 保存。

        ⚠️ save=True 为真实写入设备配置，验证后需恢复原昵称。

        :param name: 新昵称
        :param save: True 点右上角「保存」/ False 仅输入不保存
        :return: self（支持链式调用）
        :raises OperationFailedError: 昵称为空
        """
        if not name:
            raise OperationFailedError("设备昵称不能为空")
        # 清空原值（点击清空按钮逐字删除由系统输入框处理）
        self.click(self.BTN_CLEAR)
        self.input_text(self.EDT_NAME, name)
        logger.info(f"设备名称页：已输入昵称 {name!r}")
        if save:
            self.click(self.BTN_SAVE)
            logger.info(f"设备名称页：已保存昵称 {name!r}")
        return self
