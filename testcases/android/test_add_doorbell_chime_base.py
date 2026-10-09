"""安卓端特有用例：智能门铃 + Chime Base 端到端添加流程。

业务背景：
    从首页「添加设备」入口进入「选择设备类别」页，选择「智能门铃 → Chime Base」，
    走完整配网流程：
        1. 安装位置指引 → 2. 接入电源指引 →
        3. 在搜到的设备中按 SN 选择 →
        4. 等待 WiFi 搜索完成 → 5. 输入 SSID + 密码 →
        6. 比对 WiFi 信息弹框 → 7. 等待连接网络 →
        8. 连接成功「下一步」→「完成」 → 9. 安装指引「下一步」 →
        10. 网络诊断「返回首页」+ 断言首页含 SN

前置条件：**app 保持已有登录态**（登录与添加设备是两个独立模块，
本用例不做 pm clear / 重新登录；若检测到登录页则自动兜底登录一次）

硬件依赖：
    - **真实 Chime Base 设备**：已上电且处于配对态（蓝牙/WiFi 可见）
    - **真实 WiFi 网络**：SSID / 密码不硬编码，运行时通过环境变量注入
      （`CLOUDEDGE_WIFI_SSID` / `CLOUDEDGE_WIFI_PASSWORD`）或调用参数覆盖
    - **设备 SN 已知**：通过环境变量 `CLOUDEDGE_DEVICE_SN` 注入（或调用参数覆盖）

默认 skip：
    - 本用例需要物理硬件，默认 `pytest.mark.skipif` 跳过整套
    - 但 Flow/工厂/PO 模块本身可被单测（`tests/test_device_flow_factory.py`）验证
    - 真机调试时可手动取消 skip

运行方式：
    pytest testcases/android/test_add_doorbell_chime_base.py --platform android
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

# 真实设备是否就绪：通过环境变量 / 真机调试时手动改为 True
# 也可通过 pytest -k 命令单独控制：
#   pytest -k chime_base --override-ini "markers="  (取消 skip)
HARDWARE_READY = True


@pytest.mark.android
@allure.epic("设备")
@allure.feature("添加设备")
@allure.story("智能门铃 Chime Base 端到端")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("智能门铃 Chime Base 端到端配网（需真实 Chime Base 设备）")
@pytest.mark.skipif(
    not HARDWARE_READY,
    reason=(
        "需要真实 Chime Base 设备已上电并处于配对态，"
        "以及真实 WiFi（通过环境变量 CLOUDEDGE_WIFI_SSID / "
        "CLOUDEDGE_WIFI_PASSWORD 注入）"
        "将 HARDWARE_READY 设为 True 启用本用例"
    ),
)
def test_add_doorbell_chime_base(
    platform, poco_driver, device_info,
    sn=DEFAULT_DEVICE_SN,
    ssid=DEFAULT_WIFI_SSID,
    wifi_password=DEFAULT_WIFI_PASSWORD,
):
    """端到端添加智能门铃 Chime Base。

    :param sn: 设备 SN（默认取环境变量 `CLOUDEDGE_DEVICE_SN`）
    :param ssid: WiFi SSID（默认取环境变量 `CLOUDEDGE_WIFI_SSID`）
    :param wifi_password: WiFi 密码（默认取环境变量 `CLOUDEDGE_WIFI_PASSWORD`）
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
    # 一站式添加页面（jingle_add）：从设备类别页到添加完成的完整流程封装
    jingle_add_page = PageFactory.create(
        platform, "jingle_add_page", poco=poco_driver, udid=device_info.udid
    )

    original_autofill = ""
    try:
        with allure.step("启动 app（保持已有登录态，登录/添加是两个独立模块）"):
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "put", "secure", "autofill_service", "null"],
                timeout=5,
            )
            # force-stop 清掉上次运行残留的 Activity 栈（如 ResetDeviceActivity），
            # 重启后回到 MainActivity（登录态不受影响）
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

        with allure.step("一站式添加（jingle_add_page）：设备类别页 → 添加完成"):
            # JingleAddPage 内部串联：选「智能门铃→Chime Base」→ 9 步配网
            # → 主页断言设备列表含 SN（真机 2026-10-09 全流程验证）
            devices = jingle_add_page.add_jingle_device(
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
