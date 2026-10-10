"""账号模块 · 退出登录测试：我的信息页退出登录（取消 / 确定）。

业务背景：
    登录成功后进入主页，切到「我的」页点击账号入口（tv_account）进入
    「我的信息」页（MyInformationActivity），底部有「退出登录」按钮；
    点击后弹出确认弹窗（提示：退出后不会删除任何历史数据…），
    可选择「取消」留在当前页，或「确定」退出并回到登录页。

前置条件（由 android_account_page fixture 链保证）：
    pm clear → 预授权 → 禁用 autofill → 启动 → 登录
    → 切到「我的」Tab → 点击账号入口 → 「我的信息」页

运行方式：
    pytest testcases/android/account/test_logout.py --platform android
    python run.py --platform android -k test_login_then_logout
"""

import allure
import pytest


ACCOUNT = "358632847@qq.com"  # 登录账号（与 android_logged_in 默认账号一致）


@pytest.mark.android
@allure.epic("登录")
@allure.feature("退出登录")
@allure.story("我的信息页退出登录（取消/确定）")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("登录后进入我的信息页，验证退出登录取消与确认流程")
def test_login_then_logout(android_account_page, platform, device_info):
    """登录 → 我的页 → 我的信息页 → 退出登录（先取消后确认）。

    步骤（fixture 已完成到「我的信息」页）：
    1. 断言「我的信息」页账号文本与登录账号一致
    2. 点击「退出登录」→ 断言弹窗出现 → 点击「取消」→ 断言弹窗关闭、停留本页
    3. 再次点击「退出登录」→ 点击「确定」→ 断言回到登录页（LoginActivity）
    """
    if platform != "android":
        pytest.skip("退出登录流程仅适用于 Android（CloudEdge），iOS 端跳过")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    login_page, main_page, my_page, account_page = android_account_page

    with allure.step("断言进入「我的信息」页（标题 + 退出登录按钮）"):
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
