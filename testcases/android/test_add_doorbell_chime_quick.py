"""安卓端特有用例：智能门铃 + Chime Base 快捷添加流程（蓝牙直达）。

业务背景（2026-10-10 用户确认的快捷路径，区别于完整流程）：
    首页点击「添加设备」→ 弹窗选「添加设备」→ 进入「选择设备类别」页
    → 顶部蓝牙区域**直接点击设备 SN 号**（超量时点「查看更多」，
    抽屉内下滑寻找）→ 直达 WiFi 信息输入页
    → 之后与完整流程一致：
        输入 SSID/密码 → 弹框确定 → 等待入网 → 成功页「下一步」
        → 设置房间「完成」→ 安装指引 → 网络诊断「返回首页」
        → 主页断言设备列表含 SN

对比完整流程（test_add_doorbell_chime_base.py）：
    快捷流程跳过「安装位置/接入电源指引」与「连接设备」两阶段，
    由蓝牙区域点 SN 直接进入无线连接页，步骤更少、耗时更短。

前置条件：**app 保持已有登录态**（登录与添加设备是两个独立模块，
本用例不做 pm clear / 重新登录；若检测到登录页则自动兜底登录一次）

硬件依赖：
    - **真实 Chime Base 设备**：已上电且处于配对态（蓝牙可被搜索到）
    - **真实 WiFi 网络**：`TP-LINK_BEB6` / `18268056861`（可被参数覆盖）
    - **设备 SN 已知**：`131805981`（可被参数覆盖）

运行方式：
    pytest testcases/android/test_add_doorbell_chime_quick.py --platform android
"""

import time

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.android.add_device_flow import (
    DEFAULT_DEVICE_SN,
    DEFAULT_WIFI_PASSWORD,
    DEFAULT_WIFI_SSID,
)
from pages.page_factory import PageFactory
from testcases.android.test_add_device import _open_category_page
from testcases.android.test_login_region import RUNTIME_PERMISSIONS
from testcases.android.test_login_region import _wait_for_main_activity

ACCOUNT = "358632847@qq.com"
PASSWORD = "82102353qweR"
REGION = "美国"

# 真实设备是否就绪（真机调试时保持 True）
HARDWARE_READY = True


@pytest.mark.android
@allure.epic("设备")
@allure.feature("添加设备")
@allure.story("智能门铃 Chime Base 快捷流程")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("智能门铃 Chime Base 快捷添加（蓝牙区域点 SN 直达 WiFi 输入）")
@pytest.mark.skipif(
    not HARDWARE_READY,
    reason=(
        "需要真实 Chime Base 设备已上电并处于配对态（蓝牙可见），"
        "以及真实 WiFi（默认 TP-LINK_BEB6 / 18268056861，可参数覆盖）"
        "将 HARDWARE_READY 设为 True 启用本用例"
    ),
)
def test_add_doorbell_chime_quick(
    platform, poco_driver, device_info,
    sn=DEFAULT_DEVICE_SN,
    ssid=DEFAULT_WIFI_SSID,
    wifi_password=DEFAULT_WIFI_PASSWORD,
):
    """快捷添加智能门铃 Chime Base（蓝牙区域点 SN → WiFi 输入 → 配网完成）。

    :param sn: 设备 SN（默认 `131805981`）
    :param ssid: WiFi SSID（默认 `TP-LINK_BEB6`）
    :param wifi_password: WiFi 密码（默认 `18268056861`）
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)
    allure.dynamic.parameter("sn", sn)
    allure.dynamic.parameter("ssid", ssid)

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    add_device_page = PageFactory.create(
        platform, "add_device_category_page", poco=poco_driver, udid=device_info.udid
    )
    jingle_add_page = PageFactory.create(
        platform, "jingle_add_page", poco=poco_driver, udid=device_info.udid
    )

    try:
        with allure.step("启动 app（保持已有登录态，登录/添加是两个独立模块）"):
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "put", "secure", "autofill_service", "null"],
                timeout=5,
            )
            # force-stop 清掉上次运行残留的 Activity 栈，重启回 MainActivity
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "am", "force-stop",
                 device_info.app_package],
                timeout=10,
            )
            time.sleep(1.5)
            login_page.start_app(device_info.app_package)
            time.sleep(3.0)
            current = login_page.get_current_activity().strip()
            if "LoginActivity" in current:
                # 兜底：app 数据被清过时自动登录一次
                assert login_page.wait_for_page_loaded(timeout=30), \
                    "[android] 未进入登录页"
                login_page.login_with_region(
                    region_text=REGION, account=ACCOUNT, password=PASSWORD,
                    remember_password=True,
                )
                assert _wait_for_main_activity(login_page, timeout=60), (
                    f"[android] 登录后未进入 MainActivity（当前="
                    f"{login_page.get_current_activity().strip()}）"
                )
            else:
                assert _wait_for_main_activity(login_page, timeout=30), (
                    f"[android] 未处于登录态主页（当前={current}）"
                )

        with allure.step("主页 → 添加设备 → 进入「选择设备类别」页"):
            _open_category_page(login_page, main_page, add_device_page)

        with allure.step("快捷添加：蓝牙区域点 SN → WiFi 输入 → 配网完成"):
            # 内部串联：蓝牙区域点 SN（自动「查看更多」+下滑查找）
            # → run_quick() 步骤 4-9 → 主页断言设备列表含 SN
            devices = jingle_add_page.add_jingle_device_quick(
                sn=sn,
                ssid=ssid,
                password=wifi_password,
                timeout=30.0,
                timeout_loading=30.0,
                timeout_connecting=90.0,
            )
            assert sn in devices, (
                f"[android] 主页设备列表应含 SN={sn!r}，实际：{devices}"
            )
    finally:
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)
