"""Jingle 添加模块 · 特定设备端到端添加测试：智能门铃 Chime Base SN=131903227
+ 特定 WiFi「xiaoMI-楼顶拷机IPC」。

业务背景：
    从首页「添加设备」入口进入「选择设备类别」页，选择「智能门铃 → Chime Base」，
    走完整配网流程（9 步）：
        1. 安装位置指引 → 2. 接入电源指引 →
        3. 在搜到的设备中按 SN=131903227 选择 →
        4. 等待 WiFi 搜索完成 → 5. 输入 SSID=xiaoMI-楼顶拷机IPC + 密码 56565099 →
        6. 比对 WiFi 信息弹框 → 7. 等待连接网络 →
        8. 连接成功「下一步」→「完成」 → 9. 安装指引「下一步」 →
        10. 网络诊断「返回首页」+ 断言首页含 SN=131903227

前置条件（由 jingle_category_page fixture 保证）：
    1. 设备已连接，并通过 `adb devices` 可见
    2. 已预授权运行时权限（复用账号模块策略）
    3. force-stop app 后启动（保持已有登录态，按需自动登录）
    4. 已进入「选择设备类别」页

硬件依赖（真机专用，环境无硬件时通过 HARDWARE_READY=False 跳过）：
    - **真实 Chime Base 设备 131903227**：已上电且处于配对态（蓝牙/WiFi 可见）
    - **真实 WiFi 网络**：xiaoMI-楼顶拷机IPC / 56565099（不通过环境变量，硬编码）
    - **设备 SN 已知**：131903227

与通用 test_full.py 的差异：
    - 本用例 SN / WiFi SSID / WiFi 密码全部硬编码
    - 适用于固定的"楼顶拷机"设备场景

运行方式：
    pytest testcases/android/jingle_add/test_add_doorbell_chime_131903227.py \\
        --platform android
"""

import time

import allure
import pytest


# 特定场景参数（全部硬编码，不走环境变量）
SN = "131903227"
WIFI_SSID = "xiaoMI-楼顶拷机IPC"
WIFI_PASSWORD = "56565099"

# 真实设备是否就绪
HARDWARE_READY = True


@pytest.mark.android
@allure.epic("设备")
@allure.feature("添加设备")
@allure.story("智能门铃 Chime Base 特定 SN=131903227 + 特定 WiFi 端到端")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(f"添加智能门铃 Chime Base SN={SN}（WiFi={WIFI_SSID}）")
@pytest.mark.skipif(
    not HARDWARE_READY,
    reason=(
        f"需要真实 Chime Base 设备 {SN} 已上电且处于配对态，"
        f"以及 WiFi {WIFI_SSID} 可用"
    ),
)
def test_add_doorbell_chime_131903227(
    jingle_category_page, platform, device_info,
):
    """端到端添加智能门铃 Chime Base SN=131903227（WiFi=xiaoMI-楼顶拷机IPC）。

    完整链路（真机 2026-10-10 验证）：
    1. 「选择设备类别」页选大类别「智能门铃」→ 小类别「Chime Base」
    2. 安装位置 → 接入电源 → 连接设备（点 SN 右侧「添加」）
    3. 无线连接：输入 SSID=xiaoMI-楼顶拷机IPC → 收起列表 → 输入密码 56565099
    4. 比对 WiFi 信息弹框 → 确定 → 等待设备入网
    5. 连接成功「下一步」→ 设置房间「完成」→ 安装指引「下一步」
    6. 网络诊断「返回首页」→ 主页断言设备列表含 SN=131903227

    关注指标（2026-10-10 新增）：
        - **总耗时**：从开始配网到主页断言通过的端到端时间
        - **WiFi 信息输入页相关步骤耗时**：
          `wait_wifi_ready`（步骤 4） + `input_wifi_credentials`（步骤 5）
          + `confirm_wifi_popup`（步骤 6）
          三个步骤的 log_step 已带"耗时 X.XXs"（见 base_add_device_flow.log_step
          自动计时机制），日志可直接 grep "[Step]" 或 "耗时" 关键字
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)
    allure.dynamic.parameter("sn", SN)
    allure.dynamic.parameter("ssid", WIFI_SSID)

    login_page, main_page, add_device_page, jingle_add_page = jingle_category_page

    with allure.step("一站式添加（jingle_add_page）：设备类别页 → 主页断言"):
        # JingleAddPage 内部串联：选「智能门铃→Chime Base」→ 9 步配网
        # → 主页断言设备列表含 SN
        t0 = time.perf_counter()
        devices = jingle_add_page.add_jingle_device(
            sn=SN,
            ssid=WIFI_SSID,
            password=WIFI_PASSWORD,
            timeout=150.0,  # 2026-10-10 改：搜 SN 超时 → 150s（APP 端 130s 倒计时）
            timeout_loading=30.0,
            timeout_connecting=150.0,  # 2026-10-10 改：连接成功超时 → 150s
        )
        elapsed_total = time.perf_counter() - t0
        allure.attach(
            f"SN={SN}\n总耗时={elapsed_total:.2f}s",
            name="add_jingle_device 总耗时",
            attachment_type=allure.attachment_type.TEXT,
        )
        logger_msg = (
            f"一站式添加 SN={SN} 总耗时 {elapsed_total:.2f}s，"
            "（WiFi 输入相关步骤耗时见 log_step 自动打印）"
        )
        print(logger_msg)  # pytest -s 可见
        assert SN in devices, (
            f"[android] 主页设备列表应含 SN={SN!r}，实际：{devices}"
        )
