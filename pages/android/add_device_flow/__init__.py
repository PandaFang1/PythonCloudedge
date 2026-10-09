"""add_device_flow 子包对外导出。"""

from pages.android.add_device_flow.base_add_device_flow import (
    BaseAddDeviceFlow,
    FlowStepNotImplementedError,
    HardwareInteractionRequired,
)
from pages.android.add_device_flow.battery_camera_flow import BatteryCameraFlow
from pages.android.add_device_flow.doorbell_chime_base_flow import (
    DEFAULT_DEVICE_SN,
    DEFAULT_WIFI_PASSWORD,
    DEFAULT_WIFI_SSID,
    DoorbellChimeBaseFlow,
)
from pages.android.add_device_flow.factory import (
    REGISTRY,
    DeviceFlowFactory,
    UnsupportedDeviceTypeError,
)
from pages.android.add_device_flow.mobile_4g_camera_flow import Mobile4GCameraFlow
from pages.android.add_device_flow.ptz_camera_flow import PtzCameraFlow
from pages.android.add_device_flow.wired_camera_flow import WiredCameraFlow

__all__ = [
    # 基类与异常
    "BaseAddDeviceFlow",
    "FlowStepNotImplementedError",
    "HardwareInteractionRequired",
    # Flow 子类
    "DoorbellChimeBaseFlow",
    "BatteryCameraFlow",
    "WiredCameraFlow",
    "Mobile4GCameraFlow",
    "PtzCameraFlow",
    # 工厂
    "DeviceFlowFactory",
    "UnsupportedDeviceTypeError",
    "REGISTRY",
    # 默认测试数据
    "DEFAULT_WIFI_SSID",
    "DEFAULT_WIFI_PASSWORD",
    "DEFAULT_DEVICE_SN",
]
