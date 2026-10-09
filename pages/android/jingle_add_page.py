"""智能门铃（Chime Base）一站式添加页面 PO — jingle_add。

封装从「选择设备类别」页开始到「添加完成（主页断言）」的**完整**添加流程：

    选择设备类别页
        → 选大类别「智能门铃」 → 选小类别「Chime Base」
        → 安装位置指引 →「下一步」
        → 接入电源指引 →「下一步」
        → 连接设备页：点击目标 SN 右侧「添加」
        → 无线连接页：输入 SSID → 点右侧箭头收起列表 → 输入密码 →「下一步」
        → 确认弹框：比对 WiFi 名称/密码 →「确定」
        → 连接网络页：等待设备入网
        → 连接成功页 →「下一步」
        → 设置房间页 →「完成」
        → 安装指引页 →「下一步」
        → 网络诊断页 →「返回首页」
        → 主页断言：设备列表含目标 SN（tvJingleBaseName）

内部组合复用既有模块，不重复实现任何步骤：
- `CloudEdgeAddDeviceCategoryPage.start_flow()` — 类别/类型选择 + Flow 分发
- `DoorbellChimeBaseFlow.run()` — 9 步配网流程（真机 2026-10-09 验证）
- `CloudEdgeMainPage.get_device_list()` — 主页设备列表断言

用例用法：
    jingle_page = PageFactory.create(
        "android", "jingle_add_page", poco=poco, udid=udid,
    )
    devices = jingle_page.add_jingle_device()          # 全默认参数
    devices = jingle_page.add_jingle_device(
        sn="131903239",
        ssid="xiaoMI-楼顶拷机IPC",
        password="56565099",
    )
"""

from __future__ import annotations

from typing import Any, List, Optional

from pages.android.add_device_category_page import CloudEdgeAddDeviceCategoryPage
from pages.android.add_device_flow.doorbell_chime_base_flow import (
    DEFAULT_DEVICE_SN,
    DEFAULT_WIFI_PASSWORD,
    DEFAULT_WIFI_SSID,
    DoorbellChimeBaseFlow,
)
from pages.android.main_page import CloudEdgeMainPage
from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleAddPage(BasePage):
    """智能门铃 Chime Base 一站式添加页面（从设备类别页到添加完成）。

    作为门面（Facade）PO：自身不持有定位器，全部操作委托给
    类别选择页 / DoorbellChimeBaseFlow / 主页 三个既有模块，
    对用例暴露单一入口 `add_jingle_device()`。
    """

    # 设备类型标识（智能门铃 → Chime Base）
    CATEGORY_NAME = "智能门铃"
    TYPE_NAME = "Chime Base"

    def __init__(self, poco: Any, udid: str = "") -> None:
        super().__init__(poco, udid)
        self.category_page = CloudEdgeAddDeviceCategoryPage(poco, udid)
        self.main_page = CloudEdgeMainPage(poco, udid)

    # ==================== 页面等待 ====================

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「选择设备类别」页加载完成（本流程的起点页面）。"""
        return self.category_page.wait_for_page_loaded(timeout=timeout)

    # ==================== 一站式入口 ====================

    def add_jingle_device(
        self,
        sn: Optional[str] = None,
        ssid: Optional[str] = None,
        password: Optional[str] = None,
        type_des: Optional[str] = None,
        timeout: float = 30.0,
        timeout_loading: float = 30.0,
        timeout_connecting: float = 120.0,
    ) -> List[str]:
        """一站式添加智能门铃 Chime Base：设备类别页 → 主页断言。

        完整链路（真机 2026-10-09 验证）：
        1. 「选择设备类别」页选大类别「智能门铃」→ 小类别「Chime Base」
        2. 安装位置 → 接入电源 → 连接设备（点 SN「添加」）
        3. 无线连接（输 SSID → 点箭头收列表 → 输密码 → 下一步）
        4. 弹框比对 WiFi 信息 → 确定 → 等待设备入网
        5. 连接成功 → 设置房间「完成」→ 安装指引「下一步」
        6. 网络诊断「返回首页」→ 主页断言设备列表含 SN

        :param sn: 设备 SN（默认 131903239）
        :param ssid: WiFi SSID（默认 xiaoMI-楼顶拷机IPC）
        :param password: WiFi 密码（默认 56565099）
        :param type_des: 小类别描述（可选，同名类型消歧）
        :param timeout: 单步通用超时（秒）
        :param timeout_loading: 页面加载类超时（秒）
        :param timeout_connecting: 设备入网等待超时（秒，首配较慢）
        :return: 主页设备列表（含 SN 视为成功）
        :raises ElementNotFoundError: 任一页面/设备未找到时抛出
        """
        sn = sn or DEFAULT_DEVICE_SN
        ssid = ssid or DEFAULT_WIFI_SSID
        password = password or DEFAULT_WIFI_PASSWORD
        logger.info(
            f"[JingleAddPage] 开始一站式添加：category={self.CATEGORY_NAME!r}，"
            f"type={self.TYPE_NAME!r}，SN={sn!r}，SSID={ssid!r}"
        )

        # 1. 前置：确认「选择设备类别」页已加载
        if not self.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"「选择设备类别」页在 {timeout}s 内未加载，"
                f"请先从主页 ivAddDevice → 弹窗「添加设备」进入"
            )

        # 2. 选大类别 → 小类别 → 拿到 Flow 实例（内部含右侧列表二次断言）
        flow = self.category_page.start_flow(
            category_name=self.CATEGORY_NAME,
            type_name=self.TYPE_NAME,
            type_des=type_des,
        )
        if not isinstance(flow, DoorbellChimeBaseFlow):
            raise ElementNotFoundError(
                f"工厂分发结果类型错误：期望 DoorbellChimeBaseFlow，"
                f"实际 {type(flow).__name__}"
            )

        # 3. 执行 9 步配网流程（真机验证的完整链路）
        flow.run(
            sn=sn,
            ssid=ssid,
            password=password,
            timeout=timeout,
            timeout_loading=timeout_loading,
            timeout_connecting=timeout_connecting,
        )

        # 4. 主页断言：设备列表含目标 SN
        devices = self.assert_device_added(sn)
        logger.info(f"[JingleAddPage] 一站式添加完成：主页设备列表 {devices}")
        return devices

    # ==================== 断言辅助 ====================

    def assert_device_added(self, sn: str, timeout: float = 30.0) -> List[str]:
        """断言主页设备列表含指定 SN。

        :param sn: 设备 SN
        :return: 主页设备列表
        :raises ElementNotFoundError: 主页未加载或列表不含该 SN
        """
        if not self.main_page.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"添加完成后未在 {timeout}s 内回到主页"
            )
        devices = self.main_page.get_device_list()
        if sn not in devices:
            raise ElementNotFoundError(
                f"主页设备列表应含 SN={sn!r}，实际：{devices}"
            )
        logger.info(f"主页设备列表断言通过：含 SN={sn!r}")

        # 附加在线状态检查（非致命，仅记录）
        if self.main_page.is_device_online(sn):
            logger.info(f"设备 SN={sn!r} 当前状态：在线")
        else:
            logger.warning(f"设备 SN={sn!r} 当前状态：离线/未获取到")
        return devices
