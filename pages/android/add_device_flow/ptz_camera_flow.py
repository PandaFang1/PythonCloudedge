"""摇头机（PTZ）添加流程（存根）。"""

from __future__ import annotations

from typing import Any

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow


class PtzCameraFlow(BaseAddDeviceFlow):
    """摇头机添加流程（存根）。

    已知关键差异（待实现时参考）：
    - 步骤 1：可能多一步「扫码下载云台控制 app」或「对准二维码」
    - 步骤 5：WiFi 2.4G / 5G 均支持（无需按频段区分，与 Chime Base 一致）
    - 步骤 9：重命名页可能有预设名称列表
    """

    FLOW_NAME = "PtzCameraFlow"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
