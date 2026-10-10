"""安卓端（CloudEdge）共享 conftest：跨模块工具与 fixture。

职责：
1. 维护跨模块共享的常量（Activity 关键字、运行时权限列表）
2. 提供跨模块共享的工具函数（Activity 等待）
3. 封装跨模块通用的测试环境样板（pm clear / 预授权 / 禁用 autofill）
4. 提供跨模块通用的登录/启动 fixture

模块边界（强约束）：
- 本 conftest 只暴露跨多个模块共用的能力
- 单模块特有 fixture 必须放在各模块自己的 conftest.py（如 account/conftest.py）
- 禁止反向依赖：模块 conftest.py 可以依赖本文件，但本文件绝不依赖任何模块 conftest

fixture 复用链（自底向上）：
    app_page（testcases/conftest.py 全局）
        ↓
    android_test_env（本文件）：pm clear + 预授权 + 禁用/还原 autofill
        ↓
    android_logged_in（本文件）：启动 app + 自动登录（账号模块使用）
    android_preserved_app（本文件）：force-stop + 启动 + 按需登录（设备模块使用）
        ↓
    android_category_page（本文件）：android_logged_in → 「选择设备类别」页
        ↓
    模块特有 fixture（account/conftest.py、jingle_add/conftest.py、jingle_delete/conftest.py）

两条 fixture 链对比：
- 账号模块链：android_test_env → android_logged_in（pm clear 保证从登录页开始）
- 设备模块链：android_preserved_app（不 pm clear，保持已有登录态 + 设备数据）
"""

from __future__ import annotations

import time
from typing import Iterator, List, Tuple

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.page_factory import PageFactory
from utils.log_utils import get_logger

logger = get_logger()


# ==================== 共享常量 ====================

# 安卓登录页 Activity 关键字
LOGIN_ACTIVITY_KEYWORD = "LoginActivity"
# 安卓主页面 Activity 关键字（登录成功、删除完成等场景的硬判定）
MAIN_ACTIVITY_KEYWORD = "MainActivity"
# 「我的信息」页 Activity（点击账号入口 tv_account 后应跳转至此）
MY_INFO_ACTIVITY_KEYWORD = "MyInformationActivity"
# 「选择设备类别」页 Activity（点击「添加设备」条目后应跳转至此）
ADD_DEVICE_ACTIVITY_KEYWORD = "AddSeriesTypeActivity"
# 配网/开机说明页 Activity（选择具体设备类型后跳转至此）
POWER_ON_ACTIVITY_KEYWORD = "PowerOnActivity"

# pm clear 后需预先授予的运行时权限（否则登录后 MIUI 会弹 GrantPermissionsActivity，
# 该弹窗运行在 com.lbe.security.miui 安全沙箱，poco/uiautomator 均无法 dump 与点击）
RUNTIME_PERMISSIONS: List[str] = [
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


# ==================== 共享工具函数 ====================

def wait_for_main_activity(page, timeout: float = 30.0) -> bool:
    """等待设备前台 Activity 切换到 MainActivity。

    Poco 的 DOM dump 在部分机型上与 uiautomator 不一致（识别点可能取不到），
    此处直接以系统 Activity 切换作为登录成功的判定，更稳定。

    附带处理：登录后 app 申请运行时权限（GrantPermissionsActivity）时，
    自动点击「允许 / 仅在使用中允许」放行。

    :param page: BasePage 实例（复用其 adb 命令能力）
    :param timeout: 等待超时时间（秒）
    :return: 已进入 MainActivity 返回 True
    """
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


def wait_for_activity(page, keyword: str, timeout: float = 10.0) -> bool:
    """等待前台 Activity 包含指定关键字。

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


# ==================== 跨模块共享 fixture ====================

@pytest.fixture
def android_test_env(platform, poco_driver, device_info) -> Iterator[str]:
    """清理 app 数据 + 预授权运行时权限 + 禁用系统 autofill（teardown 还原）。

    适用场景：从登录页开始的全流程用例（账号模块的登录/登出/切换）。
    yield 出 `original_autofill`（原始 autofill 服务名），便于其他 fixture 进一步封装。

    实现细节：
    1. pm clear（清空账号、缓存等所有数据，确保从登录页开始）
    2. pm grant × 11（避免登录后 MIUI 安全沙箱权限弹窗阻塞）
    3. 禁用系统 autofill（避免 MIUI 自动填充账号弹窗遮挡登录页）
    4. yield
    5. 还原 autofill 服务（若失败不阻断用例结果上报）

    :return: 原始 autofill 服务名（未设置时为空串）
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )

    # 1. pm clear（异步清理，稍等再授权避免被覆盖）
    with allure.step("清除 app 数据（确保从登录页开始）"):
        login_page._run_device_command(
            ["adb", "-s", device_info.udid, "shell", "pm", "clear",
             device_info.app_package],
            timeout=15,
        )
        time.sleep(2.0)

    # 2. pm grant × 11
    with allure.step("预先授予运行时权限（避免登录后 MIUI 权限弹窗）"):
        for permission in RUNTIME_PERMISSIONS:
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "pm", "grant",
                 device_info.app_package, permission],
                timeout=5,
            )

    # 3. 禁用 autofill（保存原值用于还原）
    with allure.step("禁用系统 autofill 服务（避免 MIUI 自动填充弹窗遮挡）"):
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

    yield original_autofill

    # teardown：还原 autofill（失败不影响用例结果）
    try:
        if original_autofill and original_autofill != "null":
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell",
                 "settings", "put", "secure", "autofill_service",
                 original_autofill],
                timeout=5,
            )
    except Exception as exc:  # noqa: BLE001 还原失败不阻断
        logger.warning(f"还原 autofill 服务失败：{exc}")


@pytest.fixture
def android_logged_in(android_test_env, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """基于 android_test_env，启动 app 并执行登录，断言进入登录态主页。

    yield 出 (login_page, main_page) 元组，便于用例直接使用。
    用例无需关心启动/登录/Activity 等待等样板。

    :return: (CloudEdgeLoginPage, CloudEdgeMainPage) 已登录态实例对
    """
    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)

    with allure.step("启动 CloudEdge"):
        login_page.start_app(device_info.app_package)

    with allure.step("等待登录页加载"):
        assert login_page.wait_for_page_loaded(timeout=30), \
            "[android] 未进入登录页，无法执行登录流程"

    with allure.step("一站式：选国家「美国」+ 登录"):
        login_page.login_with_region(
            region_text="美国",
            account="358632847@qq.com",
            password="82102353qweR",
            remember_password=True,
        )

    with allure.step("断言登录成功 → 进入 MainActivity"):
        assert wait_for_main_activity(login_page, timeout=60), (
            f"[android] 登录后前台 Activity 仍为 "
            f"{login_page.get_current_activity()}，未切换到 MainActivity"
        )

    yield login_page, main_page

    with allure.step("关闭 CloudEdge"):
        login_page.stop_app(device_info.app_package)


@pytest.fixture
def android_preserved_app(platform, poco_driver, device_info) -> Iterator[Tuple]:
    """保持已有登录态的最小化环境（**不做 pm clear**）。

    与 android_logged_in 的差异：
    - android_logged_in 会 pm clear（适用于「从登录页开始」的账号模块）
    - 本 fixture 不做 pm clear，仅 force-stop + 按需登录
    - 适用于「保持已有登录态」的添加/删除设备用例，避免破坏账号、设备数据

    流程：
    1. 禁用系统 autofill（teardown 还原）
    2. force-stop app（清掉上次运行残留的 Activity 栈）
    3. start_app 启动
    4. 检测当前 Activity：若为 LoginActivity 则自动登录（兜底）
    5. 断言进入登录态主页（MainActivity）

    yield (login_page, main_page) 给用例使用。
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)

    # 1. 禁用 autofill（保存原值）
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

    try:
        # 2. force-stop 清掉上次运行残留的 Activity 栈，重启回 MainActivity
        login_page._run_device_command(
            ["adb", "-s", device_info.udid, "shell", "am", "force-stop",
             device_info.app_package],
            timeout=10,
        )
        time.sleep(1.5)
        login_page.start_app(device_info.app_package)
        time.sleep(3.0)

        # 3. 检测当前 Activity，按需登录
        current = login_page.get_current_activity().strip()
        with allure.step("启动 app（保持已有登录态）"):
            if LOGIN_ACTIVITY_KEYWORD in current:
                # 兜底：app 数据被清过时自动登录一次
                assert login_page.wait_for_page_loaded(timeout=30), \
                    "[android] 未进入登录页"
                login_page.login_with_region(
                    region_text="美国",
                    account="358632847@qq.com",
                    password="82102353qweR",
                    remember_password=True,
                )
                assert wait_for_main_activity(login_page, timeout=60), (
                    f"[android] 登录后未进入 MainActivity（当前="
                    f"{login_page.get_current_activity().strip()}）"
                )
            else:
                assert wait_for_main_activity(login_page, timeout=30), (
                    f"[android] 未处于登录态主页（当前={current}）"
                )

        yield login_page, main_page
    finally:
        # teardown：还原 autofill
        try:
            if original_autofill and original_autofill != "null":
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell",
                     "settings", "put", "secure", "autofill_service",
                     original_autofill],
                    timeout=5,
                )
        except Exception as exc:  # noqa: BLE001 还原失败不阻断
            logger.warning(f"还原 autofill 服务失败：{exc}")
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)


@pytest.fixture
def android_category_page(android_logged_in, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """基于 android_logged_in，登录后主页 → 「选择设备类别」页。

    yield 出 (login_page, main_page, add_device_page) 元组。
    主要用于 jingle_add 模块的快捷流程（无需通过类别选择，但需要先在主页稳定）。

    :return: (CloudEdgeLoginPage, CloudEdgeMainPage,
              CloudEdgeAddDeviceCategoryPage) 已进入「选择设备类别」页
    """
    login_page, main_page = android_logged_in
    add_device_page = PageFactory.create(
        platform, "add_device_category_page",
        poco=poco_driver, udid=device_info.udid,
    )

    # 主页稳定 + 处理新手引导浮层（避免遮挡「添加设备」按钮）
    time.sleep(3.0)
    main_page.handle_guide()
    time.sleep(2.0)

    with allure.step("主页 → 添加设备 → 进入「选择设备类别」页"):
        main_page.open_add_device_category_page()
        jumped = False
        for _ in range(3):
            if wait_for_activity(login_page, ADD_DEVICE_ACTIVITY_KEYWORD, timeout=8):
                jumped = True
                break
            main_page.open_add_device_category_page()  # 重试
        assert jumped, (
            f"[android] 3 次尝试后仍未进入「选择设备类别」页（Activity="
            f"{login_page.get_current_activity().strip()}）"
        )
        assert add_device_page.wait_for_page_loaded(timeout=15), \
            "[android] 进入「选择设备类别」页后识别点未出现"

    yield login_page, main_page, add_device_page
