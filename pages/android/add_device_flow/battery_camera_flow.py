"""电池摄像机添加流程（存根）。

后续接入：电池摄像机 (2.4G Wi-Fi) / 电池摄像机 (WIFI+蓝牙) 等类型的具体步骤。
所有 9 步继承基类默认行为（调用即抛 `FlowStepNotImplementedError`），
便于业务代码 import 该类做类型注解；工厂分发时也不会 ImportError。

使用方式：
    flow = DeviceFlowFactory.create("电池摄像机", "电池摄像机", "(2.4G Wi-Fi)", ...)
    flow.run(sn="...", ssid="...", password="...")
    # ↑ 立即抛 FlowStepNotImplementedError，提示「需在 BatteryCameraFlow 中重写」
"""

from __future__ import annotations

from typing import Any

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow


class BatteryCameraFlow(BaseAddDeviceFlow):
    """电池摄像机添加流程（存根）。

    已知关键差异（待实现时参考）：
    - 步骤 1：等待「按住复位按钮 5s」说明页，需 `mark_step` 提示物理操作
    - 步骤 2：等待「指示灯慢闪」说明页
    - 步骤 3：搜到的蓝牙设备（不是 WiFi 列表），按 SN 选择
    - 步骤 4-6：可能直接走蓝牙配对而非 WiFi 配网
    - 步骤 7-9：与门铃相似但缺「安装指引」和「网络诊断」
    """

    FLOW_NAME = "BatteryCameraFlow"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # 子类可在 __init__ 中预设设备特定属性（如默认超时、提示文案等）
