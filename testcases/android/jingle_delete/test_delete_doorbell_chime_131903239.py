"""Jingle 删除模块 · 特定设备端到端删除测试：智能门铃 Chime Base SN=131903239。

业务背景（2026-10-10 用户确认，真机验证）：
    首页点击设备 SN=131903239 → 进入 jingle 首页（JingleBaseActivity）
    → 点击右上角设置按钮 → 进入设置页（CameraSettingNewActivity）
    → 向下滑动找到「删除设备」并点击
    → 确认弹框点击「删除」
    → app 自动返回主页 → 首页设备列表无此设备即为删除成功

前置条件（由 jingle_main_with_target fixture 保证）：
    1. 设备已连接，并通过 `adb devices` 可见
    2. force-stop app 后启动（保持已有登录态，按需自动登录）
    3. 目标 SN 设备已在账号中（前置检查在用例内完成）

硬件依赖：
    - **目标 SN 设备已在账号中**（主页设备列表可见该 SN）
    - 删除为云端操作，设备本体无需处于配对态/在线

与通用 test_delete.py 的差异：
    - 本用例 SN 硬编码为 131903239，不走环境变量
    - 适用于固定的"楼顶拷机"设备（WiFi: xiaoMI-楼顶拷机IPC）

注意：
    - 删除是不可逆操作；删除后如需恢复，须让设备重新进入配对态
      再走添加流程（jingle_add/test_add_doorbell_chime_131903239.py）
    - 本测试不会自动添加设备，需由 jingle_add 模块先添加或测试人员手动添加

运行方式：
    pytest testcases/android/jingle_delete/test_delete_doorbell_chime_131903239.py \\
        --platform android
"""

import allure
import pytest


# 特定场景参数：待删除的设备 SN（楼顶拷机 Chime Base）
SN = "131903239"

# 真实设备是否就绪（真机调试时保持 True；纯环境调试改为 False 跳过）
HARDWARE_READY = True


@pytest.mark.android
@allure.epic("设备")
@allure.feature("删除设备")
@allure.story("智能门铃 Chime Base 特定 SN=131903239 删除")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(f"删除智能门铃 Chime Base SN={SN}")
@pytest.mark.skipif(
    not HARDWARE_READY,
    reason=f"需要目标 SN={SN} 设备已在账号中（主页设备列表可见）",
)
def test_delete_doorbell_chime_131903239(
    jingle_main_with_target, platform, device_info,
):
    """删除智能门铃 Chime Base SN=131903239。

    完整链路（真机 2026-10-10 全流程验证）：
    1. 主页点 SN=131903239 → jingle 首页（JingleBaseActivity）
    2. 右上角设置按钮（iv_submit）→ 设置页（CameraSettingNewActivity）
    3. 下滑找到「删除设备」（btn_delete）→ 点击
    4. 确认弹框点「删除」（tv_confirm）
    5. app 自动返回主页 → 断言设备列表不含 SN=131903239
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)
    allure.dynamic.parameter("sn", SN)

    login_page, main_page, jingle_delete_page = jingle_main_with_target

    with allure.step(f"前置检查：主页设备列表应含 {SN}"):
        devices = main_page.get_device_list()
        assert SN in devices, (
            f"[android] 主页设备列表应含待删除 SN={SN!r}，实际：{devices}"
        )

    with allure.step("一站式删除：主页点 SN → 设置 → 删除设备 → 确认"):
        # JingleDeletePage 内部串联 5 步：点 SN → 设置 → 下滑点删除 → 弹框点删除
        # → 自动回主页 → 断言列表无 SN
        remain_devices = jingle_delete_page.delete_jingle_device(sn=SN)

    with allure.step(f"断言：删除后主页设备列表不含 {SN}"):
        assert SN not in remain_devices, (
            f"[android] 删除后主页设备列表不应再含 SN={SN!r}，"
            f"实际：{remain_devices}"
        )
