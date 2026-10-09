"""设备添加流程工厂单测。

目标：脱离真机验证工厂分发与存根行为（避免每个 PR 都跑完整真机流程）。

覆盖：
1. 已注册类型能正确分发到对应 Flow 类
2. 未注册类型抛 UnsupportedDeviceTypeError
3. 存根 Flow 调用 run() 抛 FlowStepNotImplementedError，提示明确
4. DoorbellChimeBaseFlow 是 DoorbellChimeBaseFlow 实例
5. supported_types() / is_supported() / get_flow_class() 行为正确
6. REGISTRY 包含所有 5 类设备
"""

import pytest

from pages.android.add_device_flow import (
    BatteryCameraFlow,
    BaseAddDeviceFlow,
    DoorbellChimeBaseFlow,
    Mobile4GCameraFlow,
    PtzCameraFlow,
    REGISTRY,
    WiredCameraFlow,
)
from pages.android.add_device_flow.base_add_device_flow import (
    FlowStepNotImplementedError,
    HardwareInteractionRequired,
)
from pages.android.add_device_flow.factory import (
    DeviceFlowFactory,
    UnsupportedDeviceTypeError,
)


# 测试用 fake poco：所有方法返回的对象 .exists() = False，.click() / .set_text() noop
class _FakeElement:
    def exists(self) -> bool:
        return False

    def wait(self, *args, **kwargs):  # noqa: ARG002
        return False

    def click(self) -> None:
        pass

    def set_text(self, *args, **kwargs) -> None:  # noqa: ARG002
        pass

    def attr(self, *args, **kwargs):  # noqa: ARG002
        return None

    def child(self, *args, **kwargs):  # noqa: ARG002
        return _FakeElement()

    def children(self):
        return []

    def offspring(self, *args, **kwargs):  # noqa: ARG002
        return _FakeElement()

    def parent(self):
        return self

    def swipe(self, *args, **kwargs):  # noqa: ARG002
        pass


class _FakePoco:
    def __call__(self, *args, **kwargs):  # noqa: ARG002
        return _FakeElement()

    def children(self):
        return []

    def swipe(self, *args, **kwargs):  # noqa: ARG002
        pass


FAKE_POCO = _FakePoco()
FAKE_UDID = "test_udid_001"


# ==================== 工厂分发正确性 ====================


class TestFactoryDispatch:
    """测试 DeviceFlowFactory.create() 按 (category, type_name) 正确分发。"""

    def test_dispatch_doorbell_chime_base(self):
        """智能门铃 + Chime Base → DoorbellChimeBaseFlow。"""
        flow = DeviceFlowFactory.create(
            "智能门铃", "Chime Base", None, FAKE_POCO, FAKE_UDID,
        )
        assert isinstance(flow, DoorbellChimeBaseFlow)
        assert isinstance(flow, BaseAddDeviceFlow)
        assert flow.category == "智能门铃"
        assert flow.type_name == "Chime Base"
        assert flow.udid == FAKE_UDID

    def test_dispatch_battery_camera(self):
        """电池摄像机 → BatteryCameraFlow。"""
        flow = DeviceFlowFactory.create(
            "电池摄像机", "电池摄像机", "(2.4G Wi-Fi)", FAKE_POCO, FAKE_UDID,
        )
        assert isinstance(flow, BatteryCameraFlow)

    def test_dispatch_wired_camera(self):
        """常电摄像机 → WiredCameraFlow。"""
        flow = DeviceFlowFactory.create(
            "常电摄像机", "常电摄像机", None, FAKE_POCO, FAKE_UDID,
        )
        assert isinstance(flow, WiredCameraFlow)

    def test_dispatch_4g_camera(self):
        """4G摄像机 → Mobile4GCameraFlow。"""
        flow = DeviceFlowFactory.create(
            "4G摄像机", "4G摄像机", None, FAKE_POCO, FAKE_UDID,
        )
        assert isinstance(flow, Mobile4GCameraFlow)

    def test_dispatch_ptz_camera(self):
        """摇头机 → PtzCameraFlow。"""
        flow = DeviceFlowFactory.create(
            "摇头机", "摇头机", None, FAKE_POCO, FAKE_UDID,
        )
        assert isinstance(flow, PtzCameraFlow)

    def test_unsupported_type_raises(self):
        """未注册 (category, type) 抛 UnsupportedDeviceTypeError。"""
        with pytest.raises(UnsupportedDeviceTypeError) as exc_info:
            DeviceFlowFactory.create(
                "未知类别", "未知类型", None, FAKE_POCO, FAKE_UDID,
            )
        assert "未注册" in str(exc_info.value)
        assert exc_info.value.category == "未知类别"
        assert exc_info.value.type_name == "未知类型"

    def test_specific_type_name_in_wrong_category_raises(self):
        """type_name 存在但 category 不对 → 抛异常（不会误分发）。"""
        with pytest.raises(UnsupportedDeviceTypeError):
            # Chime Base 是智能门铃下的，不是电池摄像机下的
            DeviceFlowFactory.create(
                "电池摄像机", "Chime Base", None, FAKE_POCO, FAKE_UDID,
            )

    def test_type_des_passed_through(self):
        """type_des 不参与分发，但会透传至 Flow 实例。"""
        flow = DeviceFlowFactory.create(
            "电池摄像机", "电池摄像机", "(2.4G Wi-Fi)", FAKE_POCO, FAKE_UDID,
        )
        assert flow.type_des == "(2.4G Wi-Fi)"


# ==================== 工厂辅助方法 ====================


class TestFactoryHelpers:
    """测试 DeviceFlowFactory.supported_types() / is_supported() / get_flow_class()。"""

    def test_supported_types_contains_5_entries(self):
        """已注册类型数 = 5（端到端 1 + 存根 4）。"""
        types = DeviceFlowFactory.supported_types()
        assert len(types) == 5, f"已注册类型数应为 5，实际：{types}"

    def test_supported_types_includes_doorbell(self):
        """已注册列表含 (智能门铃, Chime Base)。"""
        assert ("智能门铃", "Chime Base") in DeviceFlowFactory.supported_types()

    def test_is_supported_true(self):
        """已注册 → is_supported() 返回 True。"""
        assert DeviceFlowFactory.is_supported("智能门铃", "Chime Base") is True
        assert DeviceFlowFactory.is_supported("电池摄像机", "电池摄像机") is True

    def test_is_supported_false(self):
        """未注册 → is_supported() 返回 False（不抛异常）。"""
        assert DeviceFlowFactory.is_supported("未知", "未知") is False

    def test_get_flow_class_returns_class(self):
        """get_flow_class() 返回 Flow 类，未命中返回 None。"""
        cls = DeviceFlowFactory.get_flow_class("智能门铃", "Chime Base")
        assert cls is DoorbellChimeBaseFlow
        assert DeviceFlowFactory.get_flow_class("未知", "未知") is None


# ==================== 存根行为 ====================


class TestStubFlowBehavior:
    """存根 Flow 调用 .run() 第一步即抛 FlowStepNotImplementedError。"""

    def test_stub_battery_camera_run_raises(self):
        flow = BatteryCameraFlow(
            FAKE_POCO, FAKE_UDID, "电池摄像机", "电池摄像机",
        )
        with pytest.raises(FlowStepNotImplementedError) as exc_info:
            flow.run()
        assert flow.FLOW_NAME in str(exc_info.value)
        assert "BatteryCameraFlow" in str(exc_info.value)
        assert "wait_chime_install_page" in str(exc_info.value)

    def test_stub_wired_camera_run_raises(self):
        flow = WiredCameraFlow(
            FAKE_POCO, FAKE_UDID, "常电摄像机", "常电摄像机",
        )
        with pytest.raises(FlowStepNotImplementedError):
            flow.run()

    def test_stub_4g_camera_run_raises(self):
        flow = Mobile4GCameraFlow(
            FAKE_POCO, FAKE_UDID, "4G摄像机", "4G摄像机",
        )
        with pytest.raises(FlowStepNotImplementedError):
            flow.run()

    def test_stub_ptz_camera_run_raises(self):
        flow = PtzCameraFlow(
            FAKE_POCO, FAKE_UDID, "摇头机", "摇头机",
        )
        with pytest.raises(FlowStepNotImplementedError):
            flow.run()

    def test_stub_step_method_raises_directly(self):
        """存根 Flow 的步骤方法直接调用也抛 FlowStepNotImplementedError。"""
        flow = WiredCameraFlow(
            FAKE_POCO, FAKE_UDID, "常电摄像机", "常电摄像机",
        )
        with pytest.raises(FlowStepNotImplementedError) as exc_info:
            flow.input_wifi_credentials("ssid", "pwd")
        assert "input_wifi_credentials" in str(exc_info.value)
        assert exc_info.value.flow_name == "WiredCameraFlow"
        assert exc_info.value.step_name == "input_wifi_credentials"


# ==================== 端到端 Flow（不真跑） ====================


class TestDoorbellChimeBaseFlowConstruction:
    """验证 DoorbellChimeBaseFlow 构造与基本属性（不调用 run）。"""

    def test_construction_sets_all_po(self):
        """构造时自动创建 8 个下游 PO 实例。"""
        flow = DoorbellChimeBaseFlow(FAKE_POCO, FAKE_UDID)
        # 所有 PO 实例均已创建
        assert flow.install_location_page is not None
        assert flow.power_supply_page is not None
        assert flow.select_device_page is not None
        assert flow.wifi_config_page is not None
        assert flow.connecting_page is not None
        assert flow.success_page is not None
        assert flow.install_guide_page is not None
        assert flow.network_diagnostic_page is not None

    def test_flow_name(self):
        """FLOW_NAME 类属性正确。"""
        assert DoorbellChimeBaseFlow.FLOW_NAME == "DoorbellChimeBaseFlow"

    def test_describe(self):
        """describe() 返回完整描述字典。"""
        flow = DoorbellChimeBaseFlow(
            FAKE_POCO, FAKE_UDID, "智能门铃", "Chime Base", None,
        )
        desc = flow.describe()
        assert desc["flow"] == "DoorbellChimeBaseFlow"
        assert desc["category"] == "智能门铃"
        assert desc["type_name"] == "Chime Base"
        assert "completed" in desc

    def test_mark_step_raises_hardware_signal(self):
        """mark_step() 抛 HardwareInteractionRequired 软信号。"""
        flow = DoorbellChimeBaseFlow(FAKE_POCO, FAKE_UDID)
        with pytest.raises(HardwareInteractionRequired) as exc_info:
            flow.mark_step("step_x", "需要人工复位")
        assert exc_info.value.step_name == "step_x"
        assert "复位" in exc_info.value.reason

    def test_log_step_records_completion(self):
        """log_step() 含「完成」字样时计入 completed_steps。"""
        flow = DoorbellChimeBaseFlow(FAKE_POCO, FAKE_UDID)
        flow.log_step("step_a", "开始")
        assert "step_a" not in flow.completed_steps
        flow.log_step("step_a", "完成")
        assert "step_a" in flow.completed_steps


# ==================== REGISTRY 完整性 ====================


class TestRegistryIntegrity:
    """验证 REGISTRY 内容完整、key 全部为字符串。"""

    def test_registry_has_5_entries(self):
        assert len(REGISTRY) == 5

    def test_all_registry_values_are_flow_subclasses(self):
        for key, cls in REGISTRY.items():
            assert issubclass(cls, BaseAddDeviceFlow), (
                f"key={key} 的值 {cls} 不是 BaseAddDeviceFlow 子类"
            )

    def test_registry_keys_are_2_tuples_of_strings(self):
        for key in REGISTRY.keys():
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_doorbell_chime_base_is_end_to_end(self):
        """智能门铃 → Chime Base 是端到端实现（非存根）。"""
        assert REGISTRY[("智能门铃", "Chime Base")] is DoorbellChimeBaseFlow

    def test_other_4_are_stubs(self):
        """其他 4 个类型映射到存根 Flow 类。"""
        assert REGISTRY[("电池摄像机", "电池摄像机")] is BatteryCameraFlow
        assert REGISTRY[("常电摄像机", "常电摄像机")] is WiredCameraFlow
        assert REGISTRY[("4G摄像机", "4G摄像机")] is Mobile4GCameraFlow
        assert REGISTRY[("摇头机", "摇头机")] is PtzCameraFlow
