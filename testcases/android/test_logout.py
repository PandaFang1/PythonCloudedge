"""安卓端特有用例：登录 →「我的」→「我的信息」→ 退出登录全流程。

业务背景：
    登录成功后进入主页，切到「我的」页点击账号入口（tv_account）进入
    「我的信息」页（MyInformationActivity），底部有「退出登录」按钮；
    点击后弹出确认弹窗（提示：退出后不会删除任何历史数据…），
    可选择「取消」留在当前页，或「确定」退出并回到登录页。

前置条件：
    1. 设备已连接，并通过 `adb devices` 可见
    2. 已安装并启用 ADBKeyboard：
         adb install -r ADBKeyboard.apk
         adb shell ime enable com.android.adbkeyboard/.AdbIME
    3. config.yaml 中至少配置一台 Android 设备（device_info fixture 依赖）

运行方式：
    pytest testcases/android/test_logout.py --platform android
    python run.py --platform android -k test_login_then_logout
"""

import time

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.android.my_page import CloudEdgeMyPage
from pages.page_factory import PageFactory
from testcases.android.test_login_region import RUNTIME_PERMISSIONS
from testcases.android.test_login_region import _wait_for_main_activity

ACCOUNT = "358632847@qq.com"
PASSWORD = "82102353qweR"

# 「我的信息」页 Activity（点击账号入口 tv_account 后应跳转至此）
MY_INFO_ACTIVITY_KEYWORD = "MyInformationActivity"


def _wait_for_activity(page, keyword: str, timeout: float = 10.0) -> bool:
    """等待前台 Activity 包含指定关键字。

    与登录用例一致，采用系统级 Activity 判定（比 Poco DOM 更稳定）。

    :param page: BasePage 实例（复用其 adb 命令能力）
    :param keyword: Activity 名称关键字（如 "MyInformationActivity"）
    :param timeout: 等待超时时间（秒）
    :return: 命中返回 True
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if keyword in page.get_current_activity():
            return True
        time.sleep(1.0)
    return False


@pytest.mark.android
@allure.epic("登录")
@allure.feature("退出登录")
@allure.story("我的信息页退出登录（取消/确定）")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("登录后进入我的信息页，验证退出登录取消与确认流程")
def test_login_then_logout(platform, poco_driver, device_info):
    """登录 → 我的页 → 我的信息页 → 退出登录（先取消后确认）。

    步骤：
    1. 前置：pm clear / 预授权运行时权限 / 禁用 autofill（复用登录用例策略）
    2. 登录（选国家「美国」+ 账号密码），断言进入 MainActivity
    3. 切到「我的」页，点击账号入口 tv_account，断言进入「我的信息」页
    4. 点击「退出登录」→ 断言弹窗出现 → 点击「取消」→ 断言弹窗关闭、停留本页
    5. 再次点击「退出登录」→ 点击「确定」→ 断言回到登录页（LoginActivity）
    """
    if platform != "android":
        pytest.skip("退出登录流程仅适用于 Android（CloudEdge），iOS 端跳过")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    my_page = CloudEdgeMyPage(poco=poco_driver, udid=device_info.udid)
    account_page = PageFactory.create(
        platform, "account_page", poco=poco_driver, udid=device_info.udid
    )

    original_autofill = ""
    try:
        # ---- 前置：清除 app 数据，确保从登录页开始 ----
        with allure.step("清除 app 数据（确保从登录页开始）"):
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "pm", "clear",
                 device_info.app_package],
                timeout=15,
            )
            # MIUI 上 pm clear 为异步清理，立即授权可能被后续清理覆盖，稍等再授权
            time.sleep(2.0)

        # ---- 前置：预先授予运行时权限（避免 MIUI 安全沙箱权限弹窗阻塞） ----
        with allure.step("预先授予运行时权限"):
            for permission in RUNTIME_PERMISSIONS:
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell", "pm", "grant",
                     device_info.app_package, permission],
                    timeout=5,
                )

        # ---- 前置：禁用系统 autofill 服务（避免 MIUI 自动填充弹窗遮挡登录页） ----
        with allure.step("禁用系统 autofill 服务"):
            original_autofill = login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "get", "secure", "autofill_service"],
                timeout=5,
            ).strip()
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "put", "secure", "autofill_service", "null"],
                timeout=5,
            )

        # ---- 登录 ----
        with allure.step("启动 CloudEdge 并登录（选国家「美国」）"):
            login_page.start_app(device_info.app_package)
            assert login_page.wait_for_page_loaded(timeout=30), \
                "[android] 未进入登录页，无法执行登录流程"
            login_page.login_with_region(
                region_text="美国",
                account=ACCOUNT,
                password=PASSWORD,
                remember_password=True,
            )

        with allure.step("断言登录成功 → 进入 MainActivity"):
            assert _wait_for_main_activity(login_page, timeout=60), (
                f"[android] 登录后前台 Activity 仍为 "
                f"{login_page.get_current_activity()}，未切换到 MainActivity"
            )

        # ---- 我的页 → 我的信息页 ----
        with allure.step("切到「我的」页并点击账号入口 tv_account"):
            time.sleep(2.0)  # 等待主页渲染稳定
            main_page.open_my_page()
            assert my_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的」页"

            # 点击账号入口并等待 Activity 跳转；登录后立即点击偶发不生效，带重试
            jumped = False
            for attempt in range(1, 4):
                my_page.open_account_page()
                if _wait_for_activity(
                    login_page, MY_INFO_ACTIVITY_KEYWORD, timeout=8
                ):
                    jumped = True
                    break
            assert jumped, (
                "[android] 点击账号入口 tv_account 3 次后仍未跳转"
                f"「我的信息」页（当前 Activity="
                f"{login_page.get_current_activity().strip()}）"
            )

        with allure.step("断言进入「我的信息」页（标题 + 退出登录按钮）"):
            assert account_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的信息」页"
            account_text = account_page.get_account()
            assert account_text == ACCOUNT, (
                f"[android] 账号显示不符：期望 {ACCOUNT}，实际 {account_text}"
            )

        # ---- 退出登录：先取消 ----
        with allure.step("退出登录 → 弹窗「取消」：停留在「我的信息」页"):
            account_page.logout(confirm=False)

        # ---- 退出登录：再确认 ----
        with allure.step("退出登录 → 弹窗「确定」：回到登录页"):
            account_page.logout(confirm=True)

        with allure.step("断言回到登录页（Poco DOM 识别点）"):
            assert login_page.wait_for_page_loaded(timeout=20), \
                "[android] 退出登录后未回到登录页（et_account/et_password 未出现）"
    finally:
        # 后置：还原系统 autofill 服务（若有原值）
        try:
            if original_autofill and original_autofill != "null":
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell",
                     "settings", "put", "secure", "autofill_service",
                     original_autofill],
                    timeout=5,
                )
        except Exception as exc:  # noqa: BLE001 还原失败不影响用例结果上报
            print(f"[警告] 还原 autofill 服务失败：{exc}")

        # 后置：关闭 app
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)
