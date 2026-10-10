"""Jingle 添加模块 · 快捷流程测试：蓝牙区域点 SN 直达 WiFi 输入。

业务背景（2026-10-10 用户确认的快捷路径，区别于完整流程）：
    首页点击「添加设备」→ 弹窗选「添加设备」→ 进入「选择设备类别」页
    → 顶部蓝牙区域**直接点击设备 SN 号**（超量时点「查看更多」，
    抽屉内下滑寻找）→ 直达 WiFi 信息输入页
    → 之后与完整流程一致：
        输入 SSID/密码 → 弹框确定 → 等待入网 → 成功页「下一步」
        → 设置房间「完成」→ 安装指引 → 网络诊断「返回首页」
        → 主页断言设备列表含 SN

对比完整流程（test_full.py）：
    快捷流程跳过「安装位置/接入电源指引」与「连接设备」两阶段，
    由蓝牙区域点 SN 直接进入无线连接页，步骤更少、耗时更短。

前置条件（由 jingle_category_page fixture 保证）：
    同 test_full.py（已进入「选择设备类别」页 + 已登录态）

硬件依赖：
    - **真实 Chime Base 设备**：已上电且处于配对态（蓝牙可被搜索到）
    - **真实 WiFi 网络**：`TP-LINK_BEB6` / `18268056861`（可被参数覆盖）
    - **设备 SN 已知**：`131805981`（可被参数覆盖）

运行方式：
    pytest testcases/android/jingle_add/test_quick.py --platform android
"""

import allure
import pytest

from pages.android.add_device_flow import (
    DEFAULT_DEVICE_SN,
    DEFAULT_WIFI_PASSWORD,
    DEFAULT_WIFI_SSID,
)

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
    jingle_category_page, platform, device_info,
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

    login_page, main_page, add_device_page, jingle_add_page = jingle_category_page

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
