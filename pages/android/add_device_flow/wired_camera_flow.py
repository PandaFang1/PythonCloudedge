"""常电摄像机添加流程（存根）。"""

from __future__ import annotations

from typing import Any

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow


class WiredCameraFlow(BaseAddDeviceFlow):
    """常电摄像机添加流程（存根）。

    已知关键差异（待实现时参考）：
    - 步骤 1：等待「插上电源」说明页
    - 步骤 2：等待「等待启动」说明页（约 30s）
    - 步骤 3：搜到的设备（无蓝牙预连）
    - 步骤 4-6：直接走 WiFi 配网
    """

    FLOW_NAME = "WiredCameraFlow"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
