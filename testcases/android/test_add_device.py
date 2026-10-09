"""安卓端特有用例：添加设备（设备类别选择页）—— 验证两种添加方式。

业务背景：
    从首页「添加设备」入口进入「选择设备类别」页
    （`com.dctrain.module_add_device.view.AddSeriesTypeActivity`），有两种
    添加设备方式：
    1. **方式 A（按类别）**：左侧分类列表选择设备类别（如「电池摄像机」），
       右侧类型列表选择具体类型（如「电池摄像机 (2.4G Wi-Fi)」），
       进入下一步配网流程（`PowerOnActivity`）
    2. **方式 B（蓝牙）**：顶部蓝牙区域选择已搜索到的设备；
       当搜索结果超过显示数量时，第 6 个槽位显示「查看更多」按钮，
       点击可展开其余设备

前置条件：同登录用例（pm clear、预授权 11 项权限、禁用 autofill）

运行方式：
    pytest testcases/android/test_add_device.py --platform android
    python run.py --platform android -k test_add_device_category
"""

import time

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.page_factory import PageFactory
from testcases.android.test_login_region import RUNTIME_PERMISSIONS
from testcases.android.test_login_region import _wait_for_main_activity
from testcases.android.test_logout import _wait_for_activity

# 设备类别选择页 Activity（点击「添加设备」条目后应跳转至此）
ADD_DEVICE_ACTIVITY_KEYWORD = "AddSeriesTypeActivity"
# 配网/开机说明页 Activity（选择具体设备类型后跳转至此）
POWER_ON_ACTIVITY_KEYWORD = "PowerOnActivity"

ACCOUNT = "358632847@qq.com"
PASSWORD = "82102353qweR"
REGION = "美国"


def _open_category_page(login_page, main_page, add_device_page):
    """从登录后主页一路导航到「选择设备类别」页（带重试）。"""
    main_page.open_add_device_category_page()
    jumped = False
    for _ in range(3):
        if _wait_for_activity(
            login_page, ADD_DEVICE_ACTIVITY_KEYWORD, timeout=8
        ):
            jumped = True
            break
        # 重试：可能在弹窗阶段未点击成功
        main_page.open_add_device_category_page()
    assert jumped, (
        "[android] 3 次尝试后仍未进入「选择设备类别」页（Activity="
        f"{login_page.get_current_activity().strip()}）"
    )
    assert add_device_page.wait_for_page_loaded(timeout=15), \
        "[android] 进入「选择设备类别」页后识别点未出现"


@pytest.mark.android
@allure.epic("设备")
@allure.feature("添加设备")
@allure.story("按设备类别选择添加（方式 A）")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("首页 → 添加设备 → 选择设备类别 → 选择电池摄像机类型 → 进入配网页")
def test_add_device_by_category(platform, poco_driver, device_info):
    """验证方式 A：从分类列表选择「电池摄像机」→「电池摄像机 (2.4G Wi-Fi)」。

    步骤：
    1. 登录（复用前置）
    2. 主页 → 添加设备弹窗 → 「添加设备」条目 → 「选择设备类别」页
    3. 验证页面识别点（标题 + 分类列表）
    4. 选择分类「电池摄像机」，选择类型「电池摄像机」
    5. 断言进入配网/开机说明页（PowerOnActivity）
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    add_device_page = PageFactory.create(
        platform, "add_device_category_page", poco=poco_driver, udid=device_info.udid
    )

    original_autofill = ""
    try:
        with allure.step("前置：清除 app 数据 + 预授权 + 禁用 autofill"):
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "pm", "clear",
                 device_info.app_package],
                timeout=15,
            )
            time.sleep(2.0)
            for permission in RUNTIME_PERMISSIONS:
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell", "pm", "grant",
                     device_info.app_package, permission],
                    timeout=5,
                )
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

        with allure.step("登录账号（选国家「美国」）"):
            login_page.start_app(device_info.app_package)
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

        with allure.step("主页 → 添加设备 → 「选择设备类别」页"):
            _open_category_page(login_page, main_page, add_device_page)

        with allure.step("验证「选择设备类别」页识别点"):
            assert add_device_page.get_page_title() == "选择设备类别", (
                f"[android] 页面标题不符：{add_device_page.get_page_title()!r}"
            )
            categories = add_device_page.get_categories()
            assert "电池摄像机" in categories, (
                f"[android] 左侧分类列表应包含「电池摄像机」，实际：{categories}"
            )

        with allure.step("选择分类「电池摄像机」→ 选择类型「电池摄像机 (2.4G Wi-Fi)」"):
            # 用一站式方法强制按"大类别→小类别"顺序执行，避免误点
            add_device_page.add_device_by_category(
                category_name="电池摄像机",
                type_name="电池摄像机",
                type_des="(2.4G Wi-Fi)",
            )
            # 点击后 app 已导航至 PowerOnActivity，下一步断言会校验

        with allure.step("断言进入配网/开机说明页（PowerOnActivity）"):
            assert _wait_for_activity(
                login_page, POWER_ON_ACTIVITY_KEYWORD, timeout=15
            ), (
                f"[android] 选择设备类型后未进入 PowerOnActivity（当前="
                f"{login_page.get_current_activity().strip()}）"
            )
    finally:
        try:
            if original_autofill and original_autofill != "null":
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell",
                     "settings", "put", "secure", "autofill_service",
                     original_autofill],
                    timeout=5,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"[警告] 还原 autofill 服务失败：{exc}")
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)


@pytest.mark.android
@allure.epic("设备")
@allure.feature("添加设备")
@allure.story("蓝牙搜索设备（方式 B）+ 查看更多")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("首页 → 添加设备 → 蓝牙区域：列出设备 / 查看更多 / 选择设备")
def test_add_device_by_bluetooth(platform, poco_driver, device_info):
    """验证方式 B：蓝牙区域结构、查看更多按钮、选择蓝牙设备。

    步骤：
    1. 登录（复用前置）
    2. 进入「选择设备类别」页
    3. 断言蓝牙区域可见（ll_bt 存在）
    4. 获取蓝牙设备列表，含「查看更多」时点击展开
    5. 选择列表中第一个非「查看更多」的设备，断言触发下一步跳转
       （具体跳转目标 Activity 因设备型号而异，此处仅断言 Activity 改变）
    """
    if platform != "android":
        pytest.skip("仅适用于 Android（CloudEdge）")

    allure.dynamic.tag(platform)
    allure.dynamic.parameter("device", device_info.user_name)

    login_page = PageFactory.create(
        platform, "login_page", poco=poco_driver, udid=device_info.udid
    )
    main_page = CloudEdgeMainPage(poco=poco_driver, udid=device_info.udid)
    add_device_page = PageFactory.create(
        platform, "add_device_category_page", poco=poco_driver, udid=device_info.udid
    )

    original_autofill = ""
    try:
        with allure.step("前置：清除 app 数据 + 预授权 + 禁用 autofill"):
            login_page._run_device_command(
                ["adb", "-s", device_info.udid, "shell", "pm", "clear",
                 device_info.app_package],
                timeout=15,
            )
            time.sleep(2.0)
            for permission in RUNTIME_PERMISSIONS:
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell", "pm", "grant",
                     device_info.app_package, permission],
                    timeout=5,
                )
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

        with allure.step("登录账号（选国家「美国」）"):
            login_page.start_app(device_info.app_package)
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

        with allure.step("进入「选择设备类别」页"):
            _open_category_page(login_page, main_page, add_device_page)

        with allure.step("断言蓝牙区域可见 + 获取设备列表"):
            assert add_device_page.is_bluetooth_area_visible(), (
                "[android] 蓝牙区域 ll_bt 不可见（附近无 BT 设备时不显示）"
            )
            bt_devices = add_device_page.get_bluetooth_devices()
            assert len(bt_devices) > 0, "[android] 蓝牙设备列表为空"

        with allure.step("「查看更多」按钮可见时点击展开"):
            if add_device_page.has_more_bt_devices_button():
                add_device_page.click_more_bt_devices()
                time.sleep(1.5)
                # 展开后「查看更多」应消失，底部抽屉（design_bottom_sheet）应可见
                assert add_device_page.is_more_devices_sheet_visible(), (
                    "[android] 点击「查看更多」后底部抽屉未弹出"
                )
                sheet_devices = add_device_page.get_bluetooth_devices()
                assert "查看更多" not in sheet_devices, (
                    f"[android] 展开后「查看更多」占位应消失，"
                    f"实际仍包含（列表：{sheet_devices}）"
                )
                # 关掉抽屉
                add_device_page.close_more_devices_sheet()
                time.sleep(0.8)

        with allure.step("选择列表中第一个具体蓝牙设备"):
            # 重新获取设备列表（可能已展开），过滤掉非设备项
            current = [
                d for d in add_device_page.get_bluetooth_devices()
                if d and d != "查看更多"
            ]
            assert current, "[android] 蓝牙设备列表为空，无法选择"
            activity_before = login_page.get_current_activity().strip()
            add_device_page.select_bluetooth_device(current[0])
            # 等待 Activity 切换（可能为 PowerOnActivity 或其他配网页）
            time.sleep(2.0)
            activity_after = login_page.get_current_activity().strip()
            assert activity_before != activity_after, (
                f"[android] 点击蓝牙设备「{current[0]}」后 Activity 未变化"
                f"（仍为 {activity_after}）"
            )
    finally:
        try:
            if original_autofill and original_autofill != "null":
                login_page._run_device_command(
                    ["adb", "-s", device_info.udid, "shell",
                     "settings", "put", "secure", "autofill_service",
                     original_autofill],
                    timeout=5,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"[警告] 还原 autofill 服务失败：{exc}")
        with allure.step("关闭 CloudEdge"):
            login_page.stop_app(device_info.app_package)
