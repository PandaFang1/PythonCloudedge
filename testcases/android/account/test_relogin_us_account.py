"""账号模块 · 退出 + 重新登录美国账号测试（特定场景）。

业务背景：
    保持当前登录态（任意账号）→ 我的 Tab → 我的信息页 → 退出登录
    → 选国家「美国」+ 账号 358632847@qq.com + 密码 82102353qweR
    → 切到「我的」页，断言账号文本为 358632847@qq.com

账号：358632847@qq.com / 82102353qweR
区域：美国

前置条件（由 android_preserved_app fixture 保证）：
    1. 设备已连接，并通过 `adb devices` 可见
    2. force-stop app 后启动（保持已有登录态，按需自动登录）
    3. 已禁用系统 autofill（teardown 还原）

与通用 test_switch.py / test_login.py 的差异：
    - test_login.py：从登录页开始（pm clear）的干净登录
    - test_switch.py：US→CN 完整切换（pm clear 后从登录页开始两次登录）
    - 本用例保留当前登录态，做"退出+重新登录"流程，更贴近"重登"场景
    - 通过 account.conftest.perform_account_switch 共用工具实现退出+登录
    - 断言通过「我的」页账号文本（my_page.get_account()）而非「我的信息」页

运行方式：
    pytest testcases/android/account/test_relogin_us_account.py --platform android
"""

import time

import allure
import pytest

from pages.android.my_page import CloudEdgeMyPage
from pages.page_factory import PageFactory
from testcases.android.account.conftest import perform_account_switch


# 特定场景参数（全部硬编码）
US_REGION = "美国"
US_ACCOUNT = "358632847@qq.com"
US_PASSWORD = "82102353qweR"


@pytest.mark.android
@allure.epic("登录")
@allure.feature("账号切换")
@allure.story("退出 + 重新登录美国账号")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(f"退出当前账号 → 重新登录美国账号 {US_ACCOUNT}")
def test_relogin_us_account(
    android_preserved_app, platform, poco_driver, device_info,
):
    """退出当前账号 → 重新登录美国账号（358632847@qq.com）。

    步骤：
    1. 保持已有登录态（任意账号，如刚登的中国账号）
    2. 若已登录：我的 → 我的信息 → 退出登录 → 回到登录页
    3. 登录美国账号（选国家「美国」+ 账号密码 + 记住密码）
    4. 断言进入 MainActivity
    5. 切到「我的」页，断言账号文本为 US_ACCOUNT
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)
    allure.dynamic.parameter("region", US_REGION)
    allure.dynamic.parameter("account", US_ACCOUNT)

    login_page, main_page = android_preserved_app
    my_page = CloudEdgeMyPage(poco=poco_driver, udid=device_info.udid)
    account_page = PageFactory.create(
        platform, "account_page", poco=poco_driver, udid=device_info.udid
    )

    # 共用工具：若已登录则退出，再登录到目标账号
    perform_account_switch(
        login_page, main_page, my_page, account_page,
        target_region=US_REGION,
        target_account=US_ACCOUNT,
        target_password=US_PASSWORD,
    )

    with allure.step(f"切到「我的」页，断言账号文本为 {US_ACCOUNT}"):
        time.sleep(2.0)  # 登录后主页渲染稳定再切
        main_page.open_my_page()
        assert my_page.wait_for_page_loaded(timeout=15), \
            "[android] 未进入「我的」页"
        actual = my_page.get_account()
        assert actual == US_ACCOUNT, (
            f"[android] 「我的」页账号显示 {actual!r}，期望 {US_ACCOUNT!r}"
        )
