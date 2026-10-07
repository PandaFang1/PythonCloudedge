"""app 生命周期公共用例（双端共用，按 platform 参数化运行）。

覆盖场景：
1. app 启动后主页面加载
2. app 关闭后重新打开（冷重启）
3. 主页面 Tab 导航

运行方式：
    pytest testcases/test_app_lifecycle.py                    # 双端全跑
    pytest testcases/test_app_lifecycle.py --platform android # 仅安卓端
    pytest testcases/test_app_lifecycle.py --platform ios     # 仅 iOS 端
"""

import allure
import pytest

from pages.android.main_page import CloudEdgeMainPage
from pages.ios.main_page import YunjiMainPage


@allure.epic("app 生命周期")
@allure.story("启动与主页面")
@allure.severity(allure.severity_level.CRITICAL)
class TestAppLifecycle:
    """app 生命周期用例（app_page fixture 已完成启动/关闭的前置后置）。"""

    @allure.title("app 启动后主页面加载完成 [{platform}]")
    def test_main_page_loaded(self, app_page, platform):
        """验证 app 启动后主页面（底部 Tab 栏）加载完成。"""
        with allure.step("处理首启弹窗（如有）"):
            app_page.handle_popups()

        with allure.step("等待主页面识别点（底部 Tab 栏）出现"):
            loaded = app_page.wait_for_page_loaded(timeout=30)

        assert loaded, f"[{platform}] app 启动后主页面未加载完成"

    @allure.title("主页面 Tab 可见性 [{platform}]")
    def test_main_tabs_visible(self, app_page, platform):
        """验证主页面核心 Tab（首页/设备/我的）均可见。"""
        tab_locators = {
            "首页": app_page.TAB_HOME,
            "设备": app_page.TAB_DEVICE,
            "我的": app_page.TAB_MY,
        }

        for tab_name, locator in tab_locators.items():
            with allure.step(f"检查 [{tab_name}] Tab 可见"):
                assert app_page.is_tab_visible(locator), \
                    f"[{platform}] 主页面缺少 [{tab_name}] Tab"

    @allure.title("切换到「我的」页面 [{platform}]")
    def test_open_my_page(self, app_page, platform):
        """验证从主页面切换到「我的」页面。"""
        with allure.step("点击「我的」Tab"):
            app_page.open_my_page()

        with allure.step("验证「我的」Tab 处于选中状态"):
            assert app_page.is_tab_visible(app_page.TAB_MY), \
                f"[{platform}] 切换「我的」页面失败"


@allure.epic("app 生命周期")
@allure.story("冷重启")
@allure.severity(allure.severity_level.NORMAL)
class TestAppRestart:
    """app 冷重启用例（通过 BasePage 的 restart_app 能力验证）。"""

    @allure.title("app 关闭后重新打开仍可加载主页面 [{platform}]")
    def test_restart_app(self, app_page, platform, device_info):
        """验证 app 冷重启后主页面可正常加载。"""
        with allure.step("关闭 app"):
            app_page.stop_app(device_info.app_package)

        with allure.step("重新启动 app"):
            app_page.start_app(device_info.app_package)

        with allure.step("处理弹窗并等待主页面加载"):
            app_page.handle_popups()
            loaded = app_page.wait_for_page_loaded(timeout=30)

        assert loaded, f"[{platform}] app 冷重启后主页面未加载完成"


# 平台页面类型一致性静态校验（防止双端页面接口漂移）
@pytest.mark.parametrize("page_cls,required_methods", [
    (CloudEdgeMainPage, ["handle_popups", "wait_for_page_loaded",
                         "is_tab_visible", "open_my_page"]),
    (YunjiMainPage, ["handle_popups", "wait_for_page_loaded",
                     "is_tab_visible", "open_my_page"]),
])
def test_page_interface_consistency(page_cls, required_methods):
    """验证双端页面类实现了同名业务方法（接口契约）。"""
    for method_name in required_methods:
        assert hasattr(page_cls, method_name), \
            f"{page_cls.__name__} 缺少业务方法 [{method_name}]，双端接口已漂移"
