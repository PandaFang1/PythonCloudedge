"""Jingle 添加模块 · 完整流程测试：智能门铃 Chime Base 端到端配网。

业务背景：
    从首页「添加设备」入口进入「选择设备类别」页，选择「智能门铃 → Chime Base」，
    走完整配网流程：
        1. 安装位置指引 → 2. 接入电源指引 →
        3. 在搜到的设备中按 SN 选择 →
        4. 等待 WiFi 搜索完成 → 5. 输入 SSID + 密码 →
        6. 比对 WiFi 信息弹框 → 7. 等待连接网络 →
        8. 连接成功「下一步」→「完成」 → 9. 安装指引「下一步」 →
        10. 网络诊断「返回首页」+ 断言首页含 SN

前置条件（由 jingle_category_page fixture 保证）：
    1. 设备已连接，并通过 `adb devices` 可见
    2. 已预授权运行时权限（复用账号模块策略）
    3. force-stop app 后启动（保持已有登录态，按需自动登录）
    4. 已进入「选择设备类别」页

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
    pytest testcases/android/jingle_add/test_full.py --platform android
"""

import allure
import pytest

from pages.android.add_device_flow import (
    DEFAULT_DEVICE_SN,
    DEFAULT_WIFI_PASSWORD,
    DEFAULT_WIFI_SSID,
)

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
    jingle_category_page, platform, device_info,
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

    login_page, main_page, add_device_page, jingle_add_page = jingle_category_page

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
