"""智能门铃 + Chime Base 端到端添加流程（完整实现）。

业务路径（真机 2026-10-09 全流程验证通过）：
    智能门铃（category） → Chime Base（type） →

    步骤 1：等待「选择 Chime Base 页面」加载（提示安装位置），点击「下一步」
            （PowerOnActivity）
    步骤 2：等待「接入电源」页面加载，点击「下一步」（PowerOnActivity）
    步骤 3：等待「连接设备」页面加载（BleSearchDeviceActivity 整页列表），
            在搜到的设备中点击目标 SN 右侧的「添加」按钮
    步骤 4：等待「无线连接」页面加载完成（忽略提示文案，以 WiFi 列表渲染为准；
            WiFi 2.4G / 5G 均支持）（AddDeviceGetWifiListActivity）
    步骤 5：输入 WiFi 名称 → 点 SSID 框右侧箭头收起列表（密码框才出现）
            → 输入密码 → 点击「下一步」
    步骤 6：弹框（title='提示'）比对 WiFi 名称/密码与输入一致，点击「确定」
    步骤 7：等待「连接网络」页（SmartWiFiActivity）设备入网完成
    步骤 8：「连接成功」页（SearchDeviceActivity）点「下一步」→
            「设置房间」页（AddDeviceSetRoomActivity）点「完成」
    步骤 9a：「安装指引」页（GuideRightPlacePicActivity）点「下一步」
    步骤 9b：「网络诊断」页（NetworkDiagnosticActivity）点「返回首页」
            + 断言首页含 SN（tvJingleBaseName）

默认测试数据（不硬编码在代码/文档中，运行时通过环境变量注入）：
    SSID     <- 环境变量 CLOUDEDGE_WIFI_SSID
    PASSWORD <- 环境变量 CLOUDEDGE_WIFI_PASSWORD
    SN       <- 环境变量 CLOUDEDGE_DEVICE_SN
也可在调用 run() / add_jingle_device() 时通过参数直接覆盖。

所有 9 步调用下游 PO（`pages.android.add_device_flow.pages.*`），
PO 内具体定位器真机确认后需替换；本 Flow 仅串联调用并提供统一日志。
"""

from __future__ import annotations

import os
from typing import Any, Optional

from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow
from pages.android.add_device_flow.pages.chime_connection_pages import (
    ChimeConnectingPage,
    ChimeSetRoomPage,
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


# 默认测试数据：从环境变量读取，不在代码/文档中硬编码真实值
DEFAULT_WIFI_SSID = os.getenv("CLOUDEDGE_WIFI_SSID", "")
DEFAULT_WIFI_PASSWORD = os.getenv("CLOUDEDGE_WIFI_PASSWORD", "")
DEFAULT_DEVICE_SN = os.getenv("CLOUDEDGE_DEVICE_SN", "")


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
        self.set_room_page = ChimeSetRoomPage(poco, udid)
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

    def select_device_by_sn(self, sn: str, timeout: float = 150.0) -> None:
        """步骤 3：在搜到的设备中点击目标 SN 右侧的「添加」按钮。

        :param sn: 设备 SN / 序列号（默认 `DEFAULT_DEVICE_SN`）
        :param timeout: 等待超时（2026-10-10 由 30s 改为 150s，对齐
            APP 端蓝牙搜索 130s 倒计时 + 20s buffer）

        :param sn: 设备 SN / 序列号（默认 `DEFAULT_DEVICE_SN`）
        """
        sn = sn or DEFAULT_DEVICE_SN
        self.log_step("select_device_by_sn", f"开始（SN={sn!r}）")
        self.select_device_page.wait_for_page_loaded(timeout=timeout)
        self.select_device_page.click_add_button_by_sn(sn, timeout=timeout)
        self.log_step("select_device_by_sn", "完成")

    def wait_wifi_ready(self, timeout_loading: float = 30.0) -> None:
        """步骤 4：等待「无线连接」页加载完成（SSID 输入框就绪）。

        2026-10-10 优化：原实现连续等两次「WiFi 列表（rv_wifi_list）渲染
        完成」，单步 30s，合计 60s 必超时但仍返回 False，浪费严重。
        根因：APP 进入「无线连接」页时**先出标题+SSID 输入框**（< 1s），
        **再异步扫周边 WiFi + 渲染 rv_wifi_list**（~30-60s）。但我们
        走**手动输入 SSID 路径**，根本不用列表项 —— WiFi 列表渲染
        只在 `ensure_wifi_list_collapsed` 中用于「是否点箭头收起」判断，
        而后者有显式 10s `wait_for_element(tv_change_wifi)`，能 handle
        列表未渲染场景。

        新实现：只等 `wifi_name_et`（SSID 输入框）出现，< 1s 通过。
        """
        self.log_step("wait_wifi_ready", "开始")
        if not self.wifi_config_page.wait_for_page_loaded(timeout=timeout_loading):
            raise ElementNotFoundError(
                f"「无线连接」页 SSID 输入框（wifi_name_et）在 "
                f"{timeout_loading}s 内未出现"
            )
        # 不再调 wait_wifi_search_finished（冗余）
        self.log_step("wait_wifi_ready", "完成")

    def input_wifi_credentials(
        self, ssid: str, password: str, timeout: float = 30.0,
    ) -> None:
        """步骤 5：输入 WiFi 名称，收起列表，输入密码，点「下一步」。

        真机调试（2026-10-09）方案：
        1. **先切输入法为 ADBKeyboard**（点击输入框不会弹系统键盘，
           从根本上避免键盘遮挡密码框/「下一步」按钮）
        2. 输入 SSID 后检测 WiFi 列表是否显示，显示则点 SSID 框右侧
           箭头（tv_change_wifi）收起，密码框才可见
        3. 输入密码（带校验重试）→ 点「下一步」
        4. finally 还原原输入法

        :param ssid: WiFi SSID（默认 `DEFAULT_WIFI_SSID`）
        :param password: WiFi 密码（默认 `DEFAULT_WIFI_PASSWORD`）
        """
        ssid = ssid or DEFAULT_WIFI_SSID
        password = password or DEFAULT_WIFI_PASSWORD
        self.log_step("input_wifi_credentials", f"开始（SSID={ssid!r}）")
        original_ime = self.wifi_config_page.switch_to_adb_keyboard()
        try:
            self.wifi_config_page.input_ssid(ssid, timeout=timeout)
            self.wifi_config_page.ensure_wifi_list_collapsed(timeout=timeout)
            self.wifi_config_page.input_password(password, timeout=timeout)
            self.wifi_config_page.click_next()
        finally:
            self.wifi_config_page.restore_ime(original_ime)
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

    def wait_network_connected(self, timeout_connecting: float = 150.0) -> None:
        """步骤 7：等待「连接网络」转圈消失，进入「连接成功」页。

        :param timeout_connecting: 等待超时（2026-10-10 由 90s 改为 150s，
            对齐首配对 + 中文 SSID 等慢场景；典型 ~30-60s，但首配对会
            触发「注册到云端」等额外网络请求）
        """
        self.log_step("wait_network_connected", "开始")
        self.connecting_page.wait_for_page_loaded(timeout=15.0)
        self.connecting_page.wait_connected(timeout=timeout_connecting)
        self.log_step("wait_network_connected", "完成")

    def click_next_and_finish(self, timeout: float = 30.0) -> None:
        """步骤 8：成功页「下一步」→ 设置房间页「完成」。

        真机验证：成功页点「下一步」后进入 AddDeviceSetRoomActivity
        （设置房间页），点底部「完成」进入安装指引页。
        """
        self.log_step("click_next_and_finish", "开始")
        self.success_page.wait_for_page_loaded(timeout=timeout)
        self.success_page.click_next()
        self.set_room_page.click_finish(timeout=timeout)
        self.log_step("click_next_and_finish", "完成")

    def skip_install_guide(self, timeout: float = 30.0) -> None:
        """步骤 9a：安装指引页点「下一步」（容错：页面未出现则跳过）。

        真机调试（2026-10-09）：设置房间页点「完成」后，安装指引页
        （tv_next_vp）可能不出现（app 版本差异 / 直接进入网络诊断页
        或主页），因此页面未加载时记录警告并直接继续，由后续步骤
        `back_to_homepage_and_assert` 完成剩余导航与断言。
        """
        self.log_step("skip_install_guide", "开始")
        if self.install_guide_page.wait_for_page_loaded(timeout=timeout):
            self.install_guide_page.click_next()
            self.log_step("skip_install_guide", "完成")
        else:
            logger.warning(
                "安装指引页未出现，跳过本步骤"
                "（后续按网络诊断页/主页继续）"
            )
            self.log_step("skip_install_guide", "跳过（页面未出现）")

    def back_to_homepage_and_assert(self, sn: str, timeout: float = 30.0) -> None:
        """步骤 9b：网络诊断页底部「返回首页」+ 断言首页含 SN（容错）。

        网络诊断页未出现时（app 直接回到主页的场景），跳过点击
        「返回首页」，直接执行主页断言。

        :param sn: 期望出现在首页的设备 SN（默认 `DEFAULT_DEVICE_SN`）
        """
        sn = sn or DEFAULT_DEVICE_SN
        self.log_step("back_to_homepage_and_assert", f"开始（SN={sn!r}）")
        if self.network_diagnostic_page.wait_for_page_loaded(timeout=timeout):
            self.network_diagnostic_page.click_back_to_homepage()
        else:
            logger.warning("网络诊断页未出现，直接执行主页断言")
        # 断言已跳到 MainActivity 且设备列表含 SN
        self.network_diagnostic_page.assert_device_added(sn, timeout=timeout)
        self.log_step("back_to_homepage_and_assert", "完成")

    # ==================== 快捷流程（蓝牙直达）====================

    def run_quick(self, **kwargs: Any) -> None:
        """快捷流程模板：跳过步骤 1-3，从步骤 4（无线连接页）开始执行。

        快捷路径（真机 2026-10-10 用户确认）：
        在「选择设备类别」页顶部蓝牙区域**直接点击设备 SN**（或
        「查看更多」抽屉下滑查找），app 跳过「安装位置/接入电源指引」
        和「连接设备」页，直达 WiFi 信息输入页（AddDeviceGetWifiListActivity），
        之后的步骤 4-9 与完整流程 `run()` 完全一致。

        调用前提：调用方已在类别页蓝牙区域点击目标 SN
        （如 `add_device_category_page.select_bt_device_auto(sn)`）。

        :param kwargs: 同 `run()`（sn/ssid/password/timeout 等）
        """
        logger.info(
            f"[{self.FLOW_NAME}] 开始快捷端到端添加流程（蓝牙直达 WiFi 输入页）："
            f"category={self.category!r}，type_name={self.type_name!r}，"
            f"SN={kwargs.get('sn', '')!r}"
        )
        # 步骤 4-5：无线连接
        self.wait_wifi_ready(timeout_loading=kwargs.get("timeout_loading", 30))
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
            timeout_connecting=kwargs.get("timeout_connecting", 150),
        )
        self.click_next_and_finish(timeout=kwargs.get("timeout", 30))
        # 步骤 9：安装指引 + 返回首页
        self.skip_install_guide(timeout=kwargs.get("timeout", 30))
        self.back_to_homepage_and_assert(
            kwargs.get("sn", ""),
            timeout=kwargs.get("timeout", 30),
        )
        logger.info(
            f"[{self.FLOW_NAME}] 快捷端到端添加流程已完成："
            f"category={self.category!r}，type_name={self.type_name!r}"
        )
        # 2026-10-10 增：打印每步耗时表，便于回归时定位瓶颈
        self.print_step_durations()
