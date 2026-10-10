"""账号模块 · 账号切换测试：同一设备上退出登录后切换登录另一账号。

业务背景：
    同一设备上先登录 A 账号（美国区），通过「我的 → 我的信息 → 退出登录」
    退出后，回到登录页重新选择国家/地区（中国），登录 B 账号。
    退出登录时「记住密码」会使账号/密码框预填 A 账号（已真机验证：
    poco set_text 为替换行为，直接输入 B 账号即可覆盖，无需清空）。

前置条件（由 android_test_env fixture 保证）：
    pm clear → 预授权 11 项权限 → 禁用 autofill

fixture 选择说明：
    本测试需要执行两次完整登录（A → 退出 → B），无法直接复用 android_logged_in
    （它只登录一次），故使用更底层的 android_test_env 自行管理登录流程，
    并直接调用共享工具 wait_for_main_activity / wait_for_activity。

运行方式：
    pytest testcases/android/account/test_switch.py --platform android
    python run.py --platform android -k test_switch_account
"""

import time

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.android.my_page import CloudEdgeMyPage
from pages.page_factory import PageFactory
from testcases.android.conftest import wait_for_activity, wait_for_main_activity


# 账号 A：美国区（先登录）
US_REGION = "美国"
US_ACCOUNT = "358632847@qq.com"
US_PASSWORD = "82102353qweR"

# 账号 B：中国区（退出后切换登录）
CN_REGION = "中国"
CN_ACCOUNT = "ceshi011@qq.com"
CN_PASSWORD = "56565099A"


@pytest.mark.android
@allure.epic("登录")
@allure.feature("账号切换")
@allure.story("退出登录后切换登录另一账号")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("美国账号登录 → 退出登录 → 中国账号登录")
def test_switch_account(android_test_env, platform, poco_driver, device_info):
    """完整账号切换流程：美国账号登录 → 退出 → 中国账号登录。

    步骤：
    1. 账号 A（美国区）登录，断言进入 MainActivity
    2. 切到「我的」页 → 账号入口 tv_account → 「我的信息」页
    3. 退出登录（弹窗「确定」），断言回到登录页
    4. 账号 B（中国区）登录：选国家「中国」+ 账号密码（覆盖预填的 A 账号）
    5. 断言再次进入 MainActivity
    6. 切到「我的」页，断言顶部账号文本已变为 B 账号
    """
    if platform != "android":
        pytest.skip("账号切换流程仅适用于 Android（CloudEdge），iOS 端跳过")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    # android_test_env 负责 pm clear / 预授权 / autofill 禁用与还原
    _ = android_test_env

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    my_page = CloudEdgeMyPage(poco=poco_driver, udid=device_info.udid)
    account_page = PageFactory.create(
        platform, "account_page", poco=poco_driver, udid=device_info.udid
    )

    try:
        # ---- 阶段 1：账号 A（美国区）登录 ----
        with allure.step(f"账号 A 登录：选国家「{US_REGION}」 + {US_ACCOUNT}"):
            login_page.start_app(device_info.app_package)
            assert login_page.wait_for_page_loaded(timeout=30), \
                "[android] 未进入登录页，无法执行账号切换流程"
            login_page.login_with_region(
                region_text=US_REGION,
                account=US_ACCOUNT,
                password=US_PASSWORD,
                remember_password=True,
            )

        with allure.step("断言账号 A 登录成功 → 进入 MainActivity"):
            assert wait_for_main_activity(login_page, timeout=60), (
                f"[android] 账号 A 登录后前台 Activity 仍为 "
                f"{login_page.get_current_activity()}，未切换到 MainActivity"
            )

        # ---- 阶段 2：进入我的信息页 + 退出登录 ----
        with allure.step("切到「我的」页并点击账号入口 tv_account"):
            time.sleep(2.0)  # 等待主页渲染稳定
            main_page.open_my_page()
            assert my_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的」页"

            # 点击账号入口并等待 Activity 跳转；登录后立即点击偶发不生效，带重试
            jumped = False
            for _ in range(3):
                my_page.open_account_page()
                if wait_for_activity(login_page, "MyInformationActivity", timeout=8):
                    jumped = True
                    break
            assert jumped, (
                "[android] 点击账号入口 tv_account 3 次后仍未跳转"
                f"「我的信息」页（当前 Activity="
                f"{login_page.get_current_activity().strip()}）"
            )

        with allure.step("断言进入「我的信息」页且显示账号 A"):
            assert account_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的信息」页"
            assert account_page.get_account() == US_ACCOUNT, (
                f"[android] 账号显示不符：期望 {US_ACCOUNT}，"
                f"实际 {account_page.get_account()}"
            )

        with allure.step("退出登录（弹窗「确定」）"):
            account_page.logout(confirm=True)

        with allure.step("断言回到登录页"):
            assert login_page.wait_for_page_loaded(timeout=20), \
                "[android] 退出登录后未回到登录页（et_account/et_password 未出现）"

        # ---- 阶段 3：账号 B（中国区）登录 ----
        with allure.step(f"账号 B 登录：选国家「{CN_REGION}」 + {CN_ACCOUNT}"):
            # 退出登录时「记住密码」预填了账号 A 的账号/密码，
            # 真机验证 poco set_text 为替换行为，直接输入即可覆盖
            login_page.login_with_region(
                region_text=CN_REGION,
                account=CN_ACCOUNT,
                password=CN_PASSWORD,
                remember_password=True,
            )

        with allure.step("断言账号 B 登录成功 → 再次进入 MainActivity"):
            assert wait_for_main_activity(login_page, timeout=60), (
                f"[android] 账号 B 登录后前台 Activity 仍为 "
                f"{login_page.get_current_activity()}，未切换到 MainActivity"
            )

        # ---- 阶段 4：验证账号已切换 ----
        with allure.step("验证「我的」页账号文本已变为账号 B"):
            time.sleep(2.0)  # 等待主页渲染稳定
            main_page.open_my_page()
            assert my_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的」页"
            actual = my_page.get_account()
            assert actual == CN_ACCOUNT, (
                f"[android] 账号切换失败：「我的」页账号显示 {actual}，"
                f"期望 {CN_ACCOUNT}"
            )
    finally:
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)
