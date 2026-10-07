"""CloudEdge 安卓端主页面。

页面职责：
1. 维护主界面（MainActivity）的元素定位器
2. 提供主页面级业务方法，与 iOS 端云际主页面保持同名接口

定位器约定：
- 优先使用基本选择器（name/text/type），其次相对选择器，最后索引与正则
- 定位器统一为类属性常量，便于维护
- 示例定位器需按 CloudEdge 实际 UI 结构调整
"""

from pages.base_page import BasePage


class CloudEdgeMainPage(BasePage):
    """CloudEdge 主页面（Android）。"""

    # ---------------- 元素定位器 ----------------
    # 主页面识别点：底部 Tab 栏（用于判断主页面加载完成）
    TAB_HOME = {"text": "首页"}
    TAB_DEVICE = {"text": "设备"}
    TAB_MY = {"text": "我的"}

    # 添加设备入口
    BTN_ADD_DEVICE = {"name": "com.cloudedge.smarteye:id/ivAddDevice"}

    # 欢迎页/登录页可能的跳过按钮（app 首启场景）
    BTN_SKIP = {"text": "跳过"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: AndroidUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="android")

    # ---------------- 业务方法（与 iOS 端同名同义） ----------------

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
