"""安卓端特有用例：登录页「国家/地区选择 + 账号密码登录」全流程。

业务背景：
    CloudEdge 首启或退出登录后会进入登录页。若需选择非默认国家/地区，
    用户点击「layout_region」容器进入国家选择页，再通过搜索定位目标国家。
    搜框原生 IME 无法直接输入中文，本用例通过 ADBKeyboard 发送「美国」，
    完成：选国家 → 输入账号 → 输入密码 → 勾选记住密码 → 登录。

前置条件：
    1. 设备已连接，并通过 `adb devices` 可见
    2. 已安装并启用 ADBKeyboard：
         adb install -r ADBKeyboard.apk
         adb shell ime enable com.android.adbkeyboard/.AdbIME
    3. config.yaml 中至少配置一台 Android 设备（device_info fixture 依赖）

运行方式：
    pytest testcases/android/test_login_region.py --platform android
    python run.py --platform android -k test_login_with_region
"""

import time

import allure
import pytest

from pages.page_factory import PageFactory
from pages.android.main_page import CloudEdgeMainPage

# 登录页 Activity（登录成功后应切换到 MainActivity）
LOGIN_ACTIVITY_KEYWORD = "LoginActivity"
MAIN_ACTIVITY_KEYWORD = "MainActivity"

# pm clear 后需预先授予的运行时权限（否则登录后 MIUI 会弹 GrantPermissionsActivity，
# 该弹窗运行在 com.lbe.security.miui 安全沙箱，poco/uiautomator 均无法 dump 与点击）
RUNTIME_PERMISSIONS = [
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.READ_MEDIA_AUDIO",
    "android.permission.READ_PHONE_STATE",
    "android.permission.POST_NOTIFICATIONS",
    "android.permission.BLUETOOTH_SCAN",
    "android.permission.BLUETOOTH_CONNECT",
]


def _wait_for_main_activity(page, timeout: float = 30.0) -> bool:
    """等待设备前台 Activity 切换到 MainActivity。

    Poco 的 DOM dump 在部分机型上与 uiautomator 不一致（识别点可能取不到），
    此处直接以系统 Activity 切换作为登录成功的判定，更稳定。

    附带处理：登录后 app 申请运行时权限（GrantPermissionsActivity）时，
    自动点击「允许 / 仅在使用中允许」放行。

    :param page: BasePage 实例（复用其 adb 命令能力）
    :param timeout: 等待超时时间（秒）
    :return: 已进入 MainActivity 返回 True
    """
    import time

    # 常见运行时权限弹窗「允许」按钮定位器（原生 + MIUI 不同文案）
    allow_locators = [
        {"text": "仅在使用中允许"},
        {"text": "仅在使用该应用时允许"},
        {"text": "本次使用允许"},
        {"text": "始终允许"},
        {"text": "允许"},
        {"name": "com.android.permissioncontroller:id/permission_allow_button"},
        {"name": "com.android.permissioncontroller:id/permission_allow_foreground_only_button"},
        {"name": "com.lbe.security.miui:id/permission_allow_btn"},
    ]

    deadline = time.time() + timeout
    while time.time() < deadline:
        activity = page.get_current_activity()

        # 权限弹窗：优先点击「允许」放行；点击失败（MIUI 安全沙箱弹窗控件
        # pos 可能越界导致 poco click 抛错）则按 BACK 拒绝放行，登录流程不受影响
        if "GrantPermissions" in activity or "packageinstaller" in activity:
            clicked = False
            for locator in allow_locators:
                try:
                    if page.click_if_exists(locator):
                        clicked = True
                        time.sleep(0.8)
                        break
                except Exception:  # noqa: BLE001 pos 越界等点击异常，尝试下一候选
                    continue
            if not clicked:
                page.press_back()
                time.sleep(1.0)
            time.sleep(0.5)
            continue

        if MAIN_ACTIVITY_KEYWORD in activity and LOGIN_ACTIVITY_KEYWORD not in activity:
            return True
        time.sleep(1.0)
    return False


@pytest.mark.android
@allure.epic("登录")
@allure.feature("账号密码登录")
@allure.story("ADBKeyboard 搜索国家并登录")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("选择国家「美国」并完成账号密码登录")
def test_login_with_region(platform, poco_driver, device_info):
    """登录全流程：ADBKeyboard 输入「美国」选国家 → 账号密码登录。

    步骤：
    1. 启动 CloudEdge，断言进入登录页（账号/密码输入框同时可见）
    2. 点击「layout_region」国家容器，进入国家选择页
    3. 切换 ADBKeyboard → 点击搜索框 → 发送「美国」→ 还原 IME
    4. 点击过滤后列表中的「美国」项，断言返回登录页
    5. 若「记住密码」未勾选则勾选
    6. 输入账号 `358632847@qq.com` 与密码 `82102353qweR`
    7. 点击「登录」按钮
    """
    if platform != "android":
        pytest.skip("国家/地区选择流程仅适用于 Android（CloudEdge），iOS 端跳过")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)

    try:
        # 前置：清除 app 数据，确保从登录页开始（app 处于已登录态时直接落在 MainActivity）
        with allure.step("清除 app 数据（确保从登录页开始）"):
            page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "pm", "clear",
                 device_info.app_package],
                timeout=15,
            )
            # MIUI 上 pm clear 为异步清理，立即授权可能被后续清理覆盖，稍等再授权
            time.sleep(2.0)

        # 前置：预先授予所有运行时权限（pm clear 后全部 revoked），
        # 避免 MIUI 权限弹窗（GrantPermissionsActivity，安全沙箱无法自动化）阻塞流程
        with allure.step("预先授予运行时权限（避免登录后 MIUI 权限弹窗）"):
            granted = []
            for permission in RUNTIME_PERMISSIONS:
                result = page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell", "pm", "grant",
                     device_info.app_package, permission],
                    timeout=5,
                )
                granted.append(f"{permission} -> ok" if result is not None else permission)
            allure.attach(
                "\n".join(granted), name="已授予权限",
                attachment_type=allure.attachment_type.TEXT,
            )

        # 前置：临时禁用系统 autofill 服务，避免 MIUI「自动填充账号」弹窗遮挡登录页
        # （press_back 无法可靠关闭该弹窗，且可能把 app 退到后台）
        with allure.step("禁用系统 autofill 服务（避免 MIUI 自动填充弹窗遮挡）"):
            original_autofill = page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "get", "secure", "autofill_service"],
                timeout=5,
            ).strip()
            page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "put", "secure", "autofill_service", "null"],
                timeout=5,
            )
            allure.attach(
                f"原 autofill 服务：{original_autofill}",
                name="autofill 原值（用例结束还原）",
                attachment_type=allure.attachment_type.TEXT,
            )

        # 前置：启动 app
        with allure.step("启动 CloudEdge"):
            page.start_app(device_info.app_package)

        # 一站式：选国家 + 勾选记住密码 + 输入账号密码 + 登录
        with allure.step("等待登录页加载（账号 + 密码输入框同时可见）"):
            assert page.wait_for_page_loaded(timeout=30), \
                "[android] 未进入登录页，无法执行国家/地区选择流程"

        with allure.step("一站式：选国家「美国」 + 登录"):
            page.login_with_region(
                region_text="美国",
                account="358632847@qq.com",
                password="82102353qweR",
                remember_password=True,
            )

        # 断言：登录成功后进入 main_page
        # 双重判定：① 系统级 Activity 已切换到 MainActivity（硬断言）
        #          ② Poco DOM 中主页面识别点出现（软断言，仅记录）
        with allure.step("断言登录成功 → 进入 main_page（Activity 切换判定）"):
            assert _wait_for_main_activity(page, timeout=60), (
                f"[android] 登录后前台 Activity 仍为 {page.get_current_activity()}，"
                "未切换到 MainActivity"
            )

        with allure.step("验证 main_page 识别点（Poco DOM，软断言）"):
            loaded = main_page.wait_for_page_loaded(timeout=10)
            if not loaded:
                allure.attach(
                    "Poco DOM 未识别到 ivAddDevice/ivMenu（部分机型 Poco dump "
                    "与 uiautomator 存在差异，Activity 已切换故不影响判定）",
                    name="main_page 识别点说明",
                    attachment_type=allure.attachment_type.TEXT,
                )
    finally:
        # 后置：还原系统 autofill 服务（若有原值）
        try:
            if original_autofill and original_autofill != "null":
                page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell",
                     "settings", "put", "secure", "autofill_service",
                     original_autofill],
                    timeout=5,
                )
        except Exception as exc:  # noqa: BLE001 还原失败不影响用例结果上报
            print(f"[警告] 还原 autofill 服务失败：{exc}")

        # 后置：关闭 app
        with allure.step("关闭 CloudEdge"):
            page.stop_app(device_info.app_package)