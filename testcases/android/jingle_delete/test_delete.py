"""Jingle 删除模块 · 端到端删除测试：智能门铃 Chime Base 删除。

业务背景（2026-10-10 用户确认，真机验证）：
    首页点击设备 SN → 进入 jingle 首页（JingleBaseActivity）
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

注意：
    - 删除是不可逆操作；删除后如需恢复，须让设备重新进入配对态
      再走添加流程（jingle_add/test_full.py / test_quick.py）
    - 本测试不会自动添加设备，需由 jingle_add 模块先添加或测试人员手动添加

运行方式：
    pytest testcases/android/jingle_delete/test_delete.py --platform android
"""

import allure
import pytest

from pages.android.add_device_flow import DEFAULT_DEVICE_SN


# 真实设备是否就绪（真机调试时保持 True）
HARDWARE_READY = True


@pytest.mark.android
@allure.epic("设备")
@allure.feature("删除设备")
@allure.story("智能门铃 Chime Base 删除流程")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("智能门铃 Chime Base 删除（主页点 SN → 设置 → 删除设备 → 确认）")
@pytest.mark.skipif(
    not HARDWARE_READY,
    reason=(
        "需要目标 SN 设备已在账号中（主页设备列表可见），"
        "将 HARDWARE_READY 设为 True 启用本用例"
    ),
)
def test_delete_doorbell_chime(
    jingle_main_with_target, platform, device_info,
    sn=DEFAULT_DEVICE_SN,
):
    """删除智能门铃 Chime Base 并断言主页设备列表无该 SN。

    :param sn: 设备 SN（默认取 `DEFAULT_DEVICE_SN`，如 131805981）
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)
    allure.dynamic.parameter("sn", sn)

    login_page, main_page, jingle_delete_page = jingle_main_with_target

    with allure.step("前置检查：主页设备列表应含目标 SN"):
        devices = main_page.get_device_list()
        assert sn in devices, (
            f"[android] 主页设备列表应含待删除 SN={sn!r}，实际：{devices}"
        )

    with allure.step("一站式删除：主页点 SN → 设置 → 删除设备 → 确认"):
        # 内部串联：主页点 SN → jingle 首页 → 设置页 → 下滑点「删除设备」
        # → 弹框点「删除」→ 自动返回主页 → 断言列表无 SN
        # （真机 2026-10-10 全流程验证）
        remain_devices = jingle_delete_page.delete_jingle_device(sn=sn)

    with allure.step("断言：删除后主页设备列表不含该 SN"):
        assert sn not in remain_devices, (
            f"[android] 删除后主页设备列表不应再含 SN={sn!r}，"
            f"实际：{remain_devices}"
        )
