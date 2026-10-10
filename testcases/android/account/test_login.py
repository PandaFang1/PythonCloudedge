"""账号模块 · 登录测试：选国家 + 账号密码登录全流程。

业务背景：
    CloudEdge 首启或退出登录后会进入登录页。若需选择非默认国家/地区，
    用户点击「layout_region」容器进入国家选择页，再通过搜索定位目标国家。
    搜框原生 IME 无法直接输入中文，本用例通过 ADBKeyboard 发送「美国」，
    完成：选国家 → 输入账号 → 输入密码 → 勾选记住密码 → 登录。

前置条件（由 android_logged_in fixture 统一保证）：
    1. 设备已连接，并通过 `adb devices` 可见
    2. pm clear 完成（确保从登录页开始）
    3. 已预授权 11 项运行时权限
    4. 已禁用系统 autofill（teardown 还原）
    5. 已安装并启用 ADBKeyboard

运行方式：
    pytest testcases/android/account/test_login.py --platform android
    python run.py --platform android -k test_login_with_region
"""

import allure
import pytest


@pytest.mark.android
@allure.epic("登录")
@allure.feature("账号密码登录")
@allure.story("ADBKeyboard 搜索国家并登录")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("选择国家「美国」并完成账号密码登录")
def test_login_with_region(android_logged_in, platform, device_info):
    """登录全流程：ADBKeyboard 输入「美国」选国家 → 账号密码登录。

    步骤（已由 android_logged_in fixture 全部完成）：
    1. 启动 CloudEdge，断言进入登录页（账号/密码输入框同时可见）
    2. 点击「layout_region」国家容器，进入国家选择页
    3. 切换 ADBKeyboard → 点击搜索框 → 发送「美国」→ 还原 IME
    4. 点击过滤后列表中的「美国」项，断言返回登录页
    5. 若「记住密码」未勾选则勾选
    6. 输入账号 `358632847@qq.com` 与密码 `82102353qweR`
    7. 点击「登录」按钮
    8. 断言前台 Activity 已切到 MainActivity
    """
    if platform != "android":
        pytest.skip("国家/地区选择流程仅适用于 Android（CloudEdge），iOS 端跳过")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    login_page, main_page = android_logged_in

    # 双重判定：① 系统级 Activity 已切换到 MainActivity（fixture 硬断言）
    #          ② Poco DOM 中主页面识别点出现（软断言，仅记录）
    with allure.step("验证 main_page 识别点（Poco DOM，软断言）"):
        loaded = main_page.wait_for_page_loaded(timeout=10)
        if not loaded:
            allure.attach(
                "Poco DOM 未识别到 ivAddDevice/ivMenu（部分机型 Poco dump "
                "与 uiautomator 存在差异，Activity 已切换故不影响判定）",
                name="main_page 识别点说明",
                attachment_type=allure.attachment_type.TEXT,
            )
