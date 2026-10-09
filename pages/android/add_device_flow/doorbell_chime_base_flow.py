"""智能门铃 + Chime Base 端到端添加流程（完整实现）。

业务路径（用户已确认）：
    智能门铃（category） → Chime Base（type） →

    步骤 1：等待「选择 Chime Base 页面」加载（提示安装位置），点击「下一步」
    步骤 2：等待「接入电源」页面加载，点击「下一步」
    步骤 3：等待「连接设备」页面加载，在搜到的设备中点击目标 SN
            右侧的「添加」按钮
    步骤 4：等待「无线连接」页面加载完成（忽略提示文案，以 WiFi 列表渲染为准；
            WiFi 2.4G / 5G 均支持）
    步骤 5：输入 WiFi 名称和密码，点击「下一步」
    步骤 6：弹框比对 WiFi 信息与输入一致，点击「确定」
    步骤 7：等待「连接网络」页面转圈消失
    步骤 8：在「连接成功」页面点击「下一步」→「完成」
    步骤 9a：在「安装指引」页面点击「下一步」
    步骤 9b：在「网络诊断」页面底部点击「返回首页」+ 断言首页含 SN

默认测试数据（用户已提供，可在 run() 时覆盖）：
    SSID     = "xiaoMI-楼顶拷机IPC"
    PASSWORD = "56565099"
    SN       = "131903239"

所有 9 步调用下游 PO（`pages.android.add_device_flow.pages.*`），
PO 内具体定位器真机确认后需替换；本 Flow 仅串联调用并提供统一日志。
"""

from __future__ import annotations

from typing import Any, Optional

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow
from pages.android.add_device_flow.pages.chime_connection_pages import (
    ChimeConnectingPage,
    ChimeSuccessPage,
)
from pages.android.add_device_flow.pages.chime_device_pairing_pages import (
    ChimeSelectDevicePage,
    ChimeWifiConfigPage,
)
from pages.android.add_device_flow.pages.chime_post_setup_pages import (
    ChimeInstallGuidePage,
    ChimeNetworkDiagnosticPage,
)
from pages.android.add_device_flow.pages.chime_pre_setup_pages import (
    ChimeInstallLocationPage,
    ChimePowerSupplyPage,
)
from utils.log_utils import get_logger

logger = get_logger()


# 默认测试数据（用户已提供）
DEFAULT_WIFI_SSID = "xiaoMI-楼顶拷机IPC"
DEFAULT_WIFI_PASSWORD = "56565099"
DEFAULT_DEVICE_SN = "131903239"


class DoorbellChimeBaseFlow(BaseAddDeviceFlow):
    """智能门铃 + Chime Base 端到端添加流程。

    设计要点：
    - 每个步骤方法复用对应 PO（PageObject），保持职责单一
    - 步骤 4-5 等待 + 输入的时长用 kwargs 透传（默认 30s）
    - 步骤 7（连接网络）默认 90s，设备首次入网较慢
    - 步骤 9b（断言首页）复用已有 CloudEdgeMainPage 检查设备列表
    """

    FLOW_NAME = "DoorbellChimeBaseFlow"

    def __init__(
        self,
        poco: Any,
        udid: str,
        category: str = "智能门铃",
        type_name: str = "Chime Base",
        type_des: Optional[str] = None,
    ) -> None:
        super().__init__(poco, udid, category, type_name, type_des)
        # 构造各步骤所需的 PO 实例（共享同一 poco/udid）
        self.install_location_page = ChimeInstallLocationPage(poco, udid)
        self.power_supply_page = ChimePowerSupplyPage(poco, udid)
        self.select_device_page = ChimeSelectDevicePage(poco, udid)
        self.wifi_config_page = ChimeWifiConfigPage(poco, udid)
        self.connecting_page = ChimeConnectingPage(poco, udid)
        self.success_page = ChimeSuccessPage(poco, udid)
        self.install_guide_page = ChimeInstallGuidePage(poco, udid)
        self.network_diagnostic_page = ChimeNetworkDiagnosticPage(poco, udid)

    # ==================== 步骤实现 ====================

    def wait_chime_install_page(self, timeout: float = 30.0) -> None:
        """步骤 1：等待「选择 Chime Base 页面」（提示安装位置），点「下一步」。"""
        self.log_step("wait_chime_install_page", "开始")
        self.install_location_page.wait_for_page_loaded(timeout=timeout)
        self.install_location_page.click_next()
        self.log_step("wait_chime_install_page", "完成")

    def confirm_power_supply(self, timeout: float = 30.0) -> None:
        """步骤 2：等待「接入电源」页面，点「下一步」。"""
        self.log_step("confirm_power_supply", "开始")
        self.power_supply_page.wait_for_page_loaded(timeout=timeout)
        self.power_supply_page.click_next()
        self.log_step("confirm_power_supply", "完成")

    def select_device_by_sn(self, sn: str, timeout: float = 30.0) -> None:
        """步骤 3：在搜到的设备中点击目标 SN 右侧的「添加」按钮。

        :param sn: 设备 SN / 序列号（默认 `DEFAULT_DEVICE_SN`）
        """
        sn = sn or DEFAULT_DEVICE_SN
        self.log_step("select_device_by_sn", f"开始（SN={sn!r}）")
        self.select_device_page.wait_for_page_loaded(timeout=timeout)
        self.select_device_page.click_add_button_by_sn(sn, timeout=timeout)
        self.log_step("select_device_by_sn", "完成")

    def wait_wifi_ready(self, timeout_loading: float = 30.0) -> None:
        """步骤 4：等待「无线连接」页加载完成（忽略提示文案，列表渲染即就绪）。"""
        self.log_step("wait_wifi_ready", "开始")
        self.wifi_config_page.wait_for_page_loaded(timeout=timeout_loading)
        self.wifi_config_page.wait_wifi_search_finished(timeout=timeout_loading)
        self.log_step("wait_wifi_ready", "完成")

    def input_wifi_credentials(
        self, ssid: str, password: str, timeout: float = 30.0,
    ) -> None:
        """步骤 5：输入 WiFi 名称和密码，点「下一步」。

        :param ssid: WiFi SSID（默认 `DEFAULT_WIFI_SSID`）
        :param password: WiFi 密码（默认 `DEFAULT_WIFI_PASSWORD`）
        """
        ssid = ssid or DEFAULT_WIFI_SSID
        password = password or DEFAULT_WIFI_PASSWORD
        self.log_step("input_wifi_credentials", f"开始（SSID={ssid!r}）")
        self.wifi_config_page.input_ssid(ssid, timeout=timeout)
        self.wifi_config_page.input_password(password, timeout=timeout)
        self.wifi_config_page.click_next()
        self.log_step("input_wifi_credentials", "完成")

    def confirm_wifi_popup(
        self,
        expected_ssid: str,
        expected_password: str,
        timeout: float = 30.0,
    ) -> None:
        """步骤 6：比对弹框中 WiFi 信息与输入一致，点「确定」。

        :param expected_ssid: 期望的 SSID（与输入一致）
        :param expected_password: 期望的密码（与输入一致）
        """
        expected_ssid = expected_ssid or DEFAULT_WIFI_SSID
        expected_password = expected_password or DEFAULT_WIFI_PASSWORD
        self.log_step("confirm_wifi_popup", "开始")
        self.wifi_config_page.assert_and_confirm_popup(
            expected_ssid=expected_ssid,
            expected_password=expected_password,
            timeout=timeout,
        )
        self.log_step("confirm_wifi_popup", "完成")

    def wait_network_connected(self, timeout_connecting: float = 90.0) -> None:
        """步骤 7：等待「连接网络」转圈消失，进入「连接成功」页。"""
        self.log_step("wait_network_connected", "开始")
        self.connecting_page.wait_for_page_loaded(timeout=15.0)
        self.connecting_page.wait_connected(timeout=timeout_connecting)
        self.log_step("wait_network_connected", "完成")

    def click_next_and_finish(self, timeout: float = 30.0) -> None:
        """步骤 8：在「连接成功」页点「下一步」→「完成」。"""
        self.log_step("click_next_and_finish", "开始")
        self.success_page.wait_for_page_loaded(timeout=timeout)
        self.success_page.click_next()
        self.success_page.click_finish(timeout=timeout)
        self.log_step("click_next_and_finish", "完成")

    def skip_install_guide(self, timeout: float = 30.0) -> None:
        """步骤 9a：安装指引页点「下一步」。"""
        self.log_step("skip_install_guide", "开始")
        self.install_guide_page.wait_for_page_loaded(timeout=timeout)
        self.install_guide_page.click_next()
        self.log_step("skip_install_guide", "完成")

    def back_to_homepage_and_assert(self, sn: str, timeout: float = 30.0) -> None:
        """步骤 9b：网络诊断页底部「返回首页」+ 断言首页含 SN。

        :param sn: 期望出现在首页的设备 SN（默认 `DEFAULT_DEVICE_SN`）
        """
        sn = sn or DEFAULT_DEVICE_SN
        self.log_step("back_to_homepage_and_assert", f"开始（SN={sn!r}）")
        self.network_diagnostic_page.wait_for_page_loaded(timeout=timeout)
        self.network_diagnostic_page.click_back_to_homepage()
        # 断言已跳到 MainActivity 且设备列表含 SN
        self.network_diagnostic_page.assert_device_added(sn, timeout=timeout)
        self.log_step("back_to_homepage_and_assert", "完成")
