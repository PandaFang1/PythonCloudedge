"""设备添加流程工厂（Factory Pattern）。

职责：
    按 (category, type_name) 元组从注册表分发到对应的 Flow 子类实例。
    业务用例通过 `add_device_category_page.start_flow(category, type)` 调用，
    内部走 `DeviceFlowFactory.create(...)` 获取 Flow。

设计要点：
    - 注册表 `{(category, type_name): FlowClass}`，key 为类别+类型联合
      （解决 type_name 重名但 category 不同的问题）
    - 命中返回实例；未命中抛 `UnsupportedDeviceTypeError`
    - 存根 Flow 创建后调用 `.run()` 才报 FlowStepNotImplementedError，
      这意味着：工厂分发永远成功（业务可先看 Flow 类再决定是否调用 run）
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Type

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow
from pages.android.add_device_flow.battery_camera_flow import BatteryCameraFlow
from pages.android.add_device_flow.doorbell_chime_base_flow import (
    DoorbellChimeBaseFlow,
)
from pages.android.add_device_flow.mobile_4g_camera_flow import Mobile4GCameraFlow
from pages.android.add_device_flow.ptz_camera_flow import PtzCameraFlow
from pages.android.add_device_flow.wired_camera_flow import WiredCameraFlow
from pages.base_page import ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class UnsupportedDeviceTypeError(ElementNotFoundError):
    """不支持的设备类型异常。

    继承 ElementNotFoundError 保持与现有 PO 错误体系一致。
    """

    def __init__(self, category: str, type_name: str, supported: list) -> None:
        self.category = category
        self.type_name = type_name
        self.supported = supported
        msg = (
            f"未注册的设备类型：category={category!r}，type_name={type_name!r}。"
            f"已支持的类型：{supported}。"
            f"如需新增请在 factory.py REGISTRY 中添加映射"
        )
        super().__init__(msg)


# 设备类型注册表：key = (category, type_name)，value = Flow 类
# 注意：type_name 是用户在「选择设备类别」页右侧列表看到的**类型名**（如 Chime Base），
#      并不包含 type_des 描述（type_des 仅用于消歧同名 type，不参与分发）
REGISTRY: Dict[Tuple[str, str], Type[BaseAddDeviceFlow]] = {
    # ★ 端到端已实现
    ("智能门铃", "Chime Base"): DoorbellChimeBaseFlow,
    # 存根（未实现）
    ("电池摄像机", "电池摄像机"): BatteryCameraFlow,
    ("常电摄像机", "常电摄像机"): WiredCameraFlow,
    ("4G摄像机", "4G摄像机"): Mobile4GCameraFlow,
    ("摇头机", "摇头机"): PtzCameraFlow,
}


class DeviceFlowFactory:
    """设备添加流程工厂。

    静态方法 `create()` 是核心入口，按 (category, type_name) 分发到对应 Flow 类。
    工厂只做「按 key 查表」+「构造实例」，不做业务流程控制。
    """

    @staticmethod
    def create(
        category: str,
        type_name: str,
        type_des: Optional[str],
        poco: Any,
        udid: str,
    ) -> BaseAddDeviceFlow:
        """按 (category, type_name) 创建对应 Flow 实例。

        :param category: 大类别名（如「智能门铃」）
        :param type_name: 小类别名（如「Chime Base」）
        :param type_des: 小类别描述（不参与分发，仅透传）
        :param poco: poco 驱动实例
        :param udid: 设备 UDID
        :return: 对应 Flow 子类实例
        :raises UnsupportedDeviceTypeError: 未在 REGISTRY 中找到 (category, type_name)
        """
        key = (category, type_name)
        flow_cls = REGISTRY.get(key)
        if flow_cls is None:
            supported = [f"{c}/{t}" for c, t in REGISTRY.keys()]
            logger.error(
                f"未注册设备类型：({category!r}, {type_name!r})，"
                f"已支持：{supported}"
            )
            raise UnsupportedDeviceTypeError(category, type_name, supported)

        logger.info(
            f"工厂分发：({category!r}, {type_name!r}) -> {flow_cls.__name__}"
        )
        return flow_cls(
            poco=poco, udid=udid,
            category=category, type_name=type_name, type_des=type_des,
        )

    @staticmethod
    def supported_types() -> list:
        """返回所有已注册 (category, type_name) 元组列表。"""
        return list(REGISTRY.keys())

    @staticmethod
    def is_supported(category: str, type_name: str) -> bool:
        """判断给定 (category, type_name) 是否已注册（不抛异常）。"""
        return (category, type_name) in REGISTRY

    @staticmethod
    def get_flow_class(category: str, type_name: str) -> Optional[Type[BaseAddDeviceFlow]]:
        """查表获取 Flow 类，未命中返回 None（不抛异常）。"""
        return REGISTRY.get((category, type_name))
