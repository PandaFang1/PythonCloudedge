"""云际 iOS 端主页面。

页面职责与 CloudEdgeMainPage 对齐：实现同名业务接口，
定位器基于云际 iOS 端 UI 结构维护（示例定位器需按实际 UI 调整）。
"""

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


class YunjiMainPage(BasePage):
    """云际主页面（iOS）。"""

    # ---------------- 元素定位器 ----------------
    # 主页面识别点（真机验证的可访问性标识）
    BTN_ADD_DEVICE = {"name": "nav home add"}
    BTN_MENU = {"name": "nav home menu"}

    # 底部 Tab 栏（真机验证：TabBar 内按钮，name 属性定位）
    TAB_HOME = {"name": "首页"}
    TAB_MESSAGE = {"name": "消息"}
    TAB_MY = {"name": "我的"}

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
        """等待主页面加载完成（以「添加设备」+「菜单」按钮同时出现为识别点）。

        轮询检查两个识别点是否同时可见，避免仅出现单一元素时误判。

        :param timeout: 等待超时时间（秒）
        :return: 主页面加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_home_page():
                logger.debug(f"主页面识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"主页面识别点在 {timeout}s 内未同时出现："
            f"BTN_ADD_DEVICE={self.exists(self.BTN_ADD_DEVICE)}，"
            f"BTN_MENU={self.exists(self.BTN_MENU)}"
        )
        return False

    def is_home_page(self) -> bool:
        """判断当前是否处于主页面（两个识别点同时存在）。

        :return: 「添加设备」与「菜单」按钮同时存在返回 True
        """
        return self.exists(self.BTN_ADD_DEVICE) and self.exists(self.BTN_MENU)

    def is_tab_visible(self, tab_locator: dict) -> bool:
        """判断指定 Tab 是否可见。

        :param tab_locator: Tab 定位器
        :return: 可见返回 True
        """
        return self.exists(tab_locator)

    def open_message_page(self) -> None:
        """切换到「消息」页面。"""
        self.click(self.TAB_MESSAGE)
        self.wait_for_element(self.TAB_MESSAGE)

    def open_my_page(self) -> None:
        """切换到「我的」页面。"""
        self.click(self.TAB_MY)
        self.wait_for_element(self.TAB_MY)

    def open_home_page(self) -> None:
        """切换回「首页」页面。"""
        self.click(self.TAB_HOME)
        self.wait_for_element(self.TAB_HOME)
