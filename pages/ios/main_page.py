"""云际 iOS 端主页面。

页面职责与 CloudEdgeMainPage 对齐：实现同名业务接口，
定位器基于云际 iOS 端 UI 结构维护（示例定位器需按实际 UI 调整）。
"""

from pages.base_page import BasePage


class YunjiMainPage(BasePage):
    """云际主页面（iOS）。"""

    # ---------------- 元素定位器 ----------------
    # 主页面识别点：底部 Tab 栏（iOS 控件类型为 TabBar 内的 Button）
    TAB_HOME = {"text": "首页"}
    TAB_DEVICE = {"text": "设备"}
    TAB_MY = {"text": "我的"}

    # 添加设备入口
    BTN_ADD_DEVICE = {"name": "ivAddDevice"}

    # 欢迎页/引导页跳过按钮
    BTN_SKIP = {"text": "跳过"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: IOSUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="ios")

    # ---------------- 业务方法（与 Android 端同名同义） ----------------

    def handle_popups(self) -> None:
        """处理首启弹窗（跳过欢迎页/隐私政策等），进入主界面。"""
        self.click_if_exists(self.BTN_SKIP)

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待主页面加载完成（以底部 Tab 栏出现为识别点）。

        :param timeout: 等待超时时间（秒）
        :return: 主页面加载完成返回 True
        """
        return self.wait_for_element(self.TAB_HOME, timeout=timeout)

    def is_tab_visible(self, tab_locator: dict) -> bool:
        """判断指定 Tab 是否可见。

        :param tab_locator: Tab 定位器
        :return: 可见返回 True
        """
        return self.exists(tab_locator)

    def open_my_page(self) -> None:
        """切换到「我的」页面。"""
        self.click(self.TAB_MY)
        self.wait_for_element(self.TAB_MY)
