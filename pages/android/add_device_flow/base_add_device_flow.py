"""设备添加流程抽象基类（Strategy Pattern）。

设计目标：
    在「选择设备类别」页（`add_device_category_page`）点击具体设备类型后，
    app 会按设备类型走不同的配网流程。本基类定义「端到端添加设备」通用步骤
    模板（等待配网指引 → 物理准备 → 选设备 → 配 WiFi → 等待入网 → 重命名 →
    断言成功），由各设备类型子类按需重写。

调用链：
    业务用例 → add_device_category_page.start_flow(category, type)
            → DeviceFlowFactory.create(category, type, type_des, poco, udid)
            → 对应 Flow 子类 .run() 触发模板方法按序执行各步骤

扩展方式（新增设备类型）：
    1. 在本目录下新建 XxxFlow，继承 BaseAddDeviceFlow
    2. 重写需要差异化的步骤方法（其余继承基类默认 raise NotImplementedError）
    3. 在 factory.py 的 REGISTRY 中注册 (category, type_name) -> XxxFlow
    4. 在 __init__.py 导出
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from utils.log_utils import get_logger

logger = get_logger()


class FlowStepNotImplementedError(NotImplementedError):
    """设备类型流程步骤未实现异常。

    存根 Flow 的步骤方法默认抛出本异常，提示「该设备类型的此步骤尚未实现，
    请在 XxxFlow 中重写」。
    """

    def __init__(self, flow_name: str, step_name: str, hint: str = "") -> None:
        self.flow_name = flow_name
        self.step_name = step_name
        self.hint = hint
        msg = (
            f"[{flow_name}] 步骤「{step_name}」尚未实现。"
            f"请在 pages/android/add_device_flow/ 中补齐对应实现"
            + (f"（{hint}）" if hint else "")
        )
        super().__init__(msg)


class HardwareInteractionRequired(Exception):
    """需要物理硬件交互的软信号（不计入错误日志，仅提示）。

    电池摄像机按住复位按钮、摄像头扫描手机二维码等步骤无法在 CI 自动化。
    Flow 子类遇到此类步骤时调用 `mark_step()` 抛出本异常，业务测试可捕获
    做特殊处理（mock 状态或跳过），不影响其他软件步骤的断言。
    """

    def __init__(self, step_name: str, reason: str) -> None:
        self.step_name = step_name
        self.reason = reason
        super().__init__(f"步骤「{step_name}」需要硬件交互：{reason}")


class BaseAddDeviceFlow(ABC):
    """设备添加流程抽象基类（Strategy Pattern）。

    核心结构：
    - `run(**kwargs)` 模板方法，按固定顺序串起 9 个步骤
    - 每个步骤是独立方法，子类按需重写
    - 基类提供 `mark_step()` 工具用于跳过硬件交互步骤
    - 基类提供 `assert_step()` / `log_step()` 辅助日志

    子类必须：
    - 设置类属性 `FLOW_NAME`（用于日志与异常文案）
    - 通过 super().__init__(poco, udid, category, type_name, type_des) 调用基类

    子类可选：
    - 重写具体步骤方法
    - 重写 `run()` 增加设备特定的前后置逻辑（但**必须**调用 `super().run()`）
    """

    # 子类需覆盖的设备类型标识（用于日志/异常文案）
    FLOW_NAME: str = "BaseAddDeviceFlow"

    def __init__(
        self,
        poco: Any,
        udid: str,
        category: str,
        type_name: str,
        type_des: Optional[str] = None,
    ) -> None:
        """
        :param poco: poco 驱动实例（AndroidUiautomationPoco 等）
        :param udid: 设备 UDID
        :param category: 大类别名（如「智能门铃」）
        :param type_name: 小类别名（如「Chime Base」）
        :param type_des: 小类别描述（可选，用于消歧）
        """
        self.poco = poco
        self.udid = udid
        self.category = category
        self.type_name = type_name
        self.type_des = type_des
        self._completed_steps: list[str] = []

    # ==================== 模板方法 ====================

    def run(self, **kwargs: Any) -> None:
        """模板方法：按固定顺序执行 9 步配网流程。

        子类一般**不重写**本方法，而是重写下面的步骤方法。如需前后置逻辑，
        可在子类中重写 run()，但必须调用 `super().run(**kwargs)`。

        :param kwargs: 透传至各步骤方法的参数（如 ssid/password/sn）
        :raises FlowStepNotImplementedError: 某步骤在当前 Flow 类中未实现
        :raises HardwareInteractionRequired: 物理硬件交互步骤
        """
        logger.info(
            f"[{self.FLOW_NAME}] 开始端到端添加流程："
            f"category={self.category!r}，type_name={self.type_name!r}，"
            f"type_des={self.type_des!r}"
        )
        # 步骤 1-2：物理准备指引（按设备类型有差异）
        self.wait_chime_install_page(timeout=kwargs.get("timeout", 30))
        self.confirm_power_supply(timeout=kwargs.get("timeout", 30))
        # 步骤 3：选择设备（按 SN 或型号）
        self.select_device_by_sn(
            kwargs.get("sn", ""),
            timeout=kwargs.get("timeout", 30),
        )
        # 步骤 4-5：无线连接（按设备类型可能略不同，但主流都走 WiFi 配网）
        self.wait_wifi_ready(timeout=kwargs.get("timeout_loading", 30))
        self.input_wifi_credentials(
            kwargs.get("ssid", ""),
            kwargs.get("password", ""),
            timeout=kwargs.get("timeout", 30),
        )
        # 步骤 6：弹框确认
        self.confirm_wifi_popup(
            expected_ssid=kwargs.get("ssid", ""),
            expected_password=kwargs.get("password", ""),
            timeout=kwargs.get("timeout", 30),
        )
        # 步骤 7-8：连接与完成
        self.wait_network_connected(
            timeout=kwargs.get("timeout_connecting", 90),
        )
        self.click_next_and_finish(timeout=kwargs.get("timeout", 30))
        # 步骤 9：安装指引 + 返回首页
        self.skip_install_guide(timeout=kwargs.get("timeout", 30))
        self.back_to_homepage_and_assert(
            kwargs.get("sn", ""),
            timeout=kwargs.get("timeout", 30),
        )
        logger.info(
            f"[{self.FLOW_NAME}] 端到端添加流程已完成："
            f"category={self.category!r}，type_name={self.type_name!r}"
        )

    # ==================== 步骤方法（子类按需重写） ====================

    def wait_chime_install_page(self, timeout: float = 30.0) -> None:
        """步骤 1：等待配网前指引页加载（如安装位置提示）。"""
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "wait_chime_install_page",
            "应等待「安装位置」等指引页标题出现",
        )

    def confirm_power_supply(self, timeout: float = 30.0) -> None:
        """步骤 2：等待电源接入指引页加载，点击「下一步」。"""
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "confirm_power_supply",
            "应等待电源页加载并点击「下一步」",
        )

    def select_device_by_sn(self, sn: str, timeout: float = 30.0) -> None:
        """步骤 3：在搜到的设备列表中，点击指定 SN 右侧的「添加」按钮。

        :param sn: 设备 SN / 序列号
        """
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "select_device_by_sn",
            f"应在设备列表中点击 SN={sn!r} 右侧的「添加」",
        )

    def wait_wifi_ready(self, timeout_loading: float = 30.0) -> None:
        """步骤 4：等待无线连接页加载完成（以 WiFi 列表渲染为准）。

        注：忽略「WiFi 搜索中」等提示文案（用户已确认），
        直接以 WiFi 列表渲染完成判定；WiFi 2.4G / 5G 均支持。
        """
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "wait_wifi_ready",
            "应等待无线连接页 WiFi 列表渲染完成（忽略提示文案）",
        )

    def input_wifi_credentials(
        self, ssid: str, password: str, timeout: float = 30.0,
    ) -> None:
        """步骤 5：输入 WiFi 名称和密码，点击「下一步」。

        :param ssid: WiFi SSID
        :param password: WiFi 密码
        """
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "input_wifi_credentials",
            f"应输入 SSID={ssid!r} + 密码，然后点「下一步」",
        )

    def confirm_wifi_popup(
        self,
        expected_ssid: str,
        expected_password: str,
        timeout: float = 30.0,
    ) -> None:
        """步骤 6：比对弹框中显示的 WiFi 信息与输入一致，点击「确定」。

        :param expected_ssid: 期望显示的 SSID（与输入一致）
        :param expected_password: 期望显示的密码（与输入一致）
        """
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "confirm_wifi_popup",
            "应比对弹框中显示的 SSID/密码与输入一致后点「确定」",
        )

    def wait_network_connected(self, timeout_connecting: float = 90.0) -> None:
        """步骤 7：等待「连接网络」转圈消失，进入成功页。"""
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "wait_network_connected",
            "应等待连接中转圈消失",
        )

    def click_next_and_finish(self, timeout: float = 30.0) -> None:
        """步骤 8：在连接成功页点击「下一步」→「完成」。"""
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "click_next_and_finish",
            "应点击「下一步」再点击「完成」",
        )

    def skip_install_guide(self, timeout: float = 30.0) -> None:
        """步骤 9a：安装指引页点击「下一步」。"""
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "skip_install_guide",
            "应在安装指引页点「下一步」",
        )

    def back_to_homepage_and_assert(self, sn: str, timeout: float = 30.0) -> None:
        """步骤 9b：网络诊断页底部「返回首页」+ 断言首页设备列表含 SN。

        :param sn: 期望出现在首页的设备 SN
        """
        raise FlowStepNotImplementedError(
            self.FLOW_NAME, "back_to_homepage_and_assert",
            f"应在网络诊断页点「返回首页」并断言 SN={sn!r} 已配对成功",
        )

    # ==================== 工具方法 ====================

    def mark_step(self, step_name: str, reason: str) -> None:
        """标记当前步骤为「需要硬件交互」，记录警告日志并抛出软信号。

        Flow 子类中如某步骤必须人工操作（按住按钮、摄像头扫码等），
        可调用本方法代替完整实现，提示业务测试做特殊处理。

        :param step_name: 步骤名（用于日志/异常）
        :param reason: 硬件交互原因
        :raises HardwareInteractionRequired: 软信号异常，可被业务捕获
        """
        logger.warning(
            f"[{self.FLOW_NAME}] 步骤「{step_name}」需要硬件交互：{reason}"
        )
        raise HardwareInteractionRequired(step_name, reason)

    def log_step(self, step_name: str, message: str) -> None:
        """记录步骤开始/完成的辅助日志。

        :param step_name: 步骤名
        :param message: 描述（如「完成」「跳过」）
        """
        logger.info(f"[{self.FLOW_NAME}] {step_name}：{message}")
        if "完成" in message or "跳过" in message:
            self._completed_steps.append(step_name)

    @property
    def completed_steps(self) -> list[str]:
        """已完成步骤列表（仅记录 log_step 标记为「完成/跳过」的步骤）。"""
        return list(self._completed_steps)

    def describe(self) -> Dict[str, str]:
        """返回 Flow 描述信息（用于日志/调试）。"""
        return {
            "flow": self.FLOW_NAME,
            "category": self.category,
            "type_name": self.type_name,
            "type_des": self.type_des or "",
            "completed": ",".join(self._completed_steps) or "(none)",
        }
