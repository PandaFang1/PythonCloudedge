"""安卓端特有用例：智能门铃 + Chime Base 删除流程。

业务背景（2026-10-10 用户确认，真机验证）：
    首页点击设备 SN → 进入 jingle 首页（JingleBaseActivity）
    → 点击右上角设置按钮 → 进入设置页（CameraSettingNewActivity）
    → 向下滑动找到「删除设备」并点击
    → 确认弹框点击「删除」
    → app 自动返回主页 → 首页设备列表无此设备即为删除成功

前置条件：**app 保持已有登录态**（登录与删除设备是两个独立模块，
本用例不做 pm clear / 重新登录；若检测到登录页则自动兜底登录一次）

硬件依赖：
    - **目标 SN 设备已在账号中**（主页设备列表可见该 SN）
    - 删除为云端操作，设备本体无需处于配对态/在线

注意：
    - 删除是不可逆操作；删除后如需恢复，须让设备重新进入配对态
      再走添加流程（test_add_doorbell_chime_base.py / _quick.py）

运行方式：
    pytest testcases/android/test_delete_doorbell_chime.py --platform android
"""

import time

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.android.add_device_flow import DEFAULT_DEVICE_SN
from pages.page_factory import PageFactory
from testcases.android.test_login_region import _wait_for_main_activity

ACCOUNT = "358632847@qq.com"
PASSWORD = "82102353qweR"
REGION = "美国"

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
    platform, poco_driver, device_info,
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

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    # 一站式删除门面：主页点 SN → 设置 → 删除设备 → 确认 → 主页断言
    jingle_delete_page = PageFactory.create(
        platform, "jingle_delete_page", poco=poco_driver, udid=device_info.udid
    )

    try:
        with allure.step("启动 app（保持已有登录态，登录/删除是两个独立模块）"):
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
    finally:
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)
