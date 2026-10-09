"""4G 摄像机添加流程（存根）。

4G 摄像机不需要 WiFi 配网，通过 4G SIM 卡入网，步骤与 WiFi 设备差异较大。
"""

from __future__ import annotations

from typing import Any

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow


class Mobile4GCameraFlow(BaseAddDeviceFlow):
    """4G 摄像机添加流程（存根）。

    已知关键差异（待实现时参考）：
    - 步骤 4-6：不需要 WiFi 配网，跳过 `wait_wifi_ready` /
      `input_wifi_credentials` / `confirm_wifi_popup`，改走 SIM 卡激活
    - 步骤 7-9：可能走 APN 配置 / 4G 注册
    """

    FLOW_NAME = "Mobile4GCameraFlow"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
