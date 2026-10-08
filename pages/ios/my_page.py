"""云际 iOS 端「我的」页面。

页面职责与 CloudEdgeMyPage 对齐：实现同名业务接口，
定位器基于云际 iOS 端 UI 结构维护（占位定位器，待 iOS 真机补充真实识别数据）。
"""

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


class YunjiMyPage(BasePage):
    """云际「我的」页面（iOS）。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点（真机验证）：顶部「二维码」+「扫一扫」按钮
    # 注：iOS 端我的页无独立 feedback 入口，以扫一扫按钮作为第二识别点
    BTN_QR_CODE = {"name": "img me qrcode"}
    BTN_SCAN = {"name": "img me scan"}

    # 功能入口（真机验证的可访问性标识）
    ITEM_FAMILY_MANAGE = {"name": "家庭管理"}
    ITEM_MY_SERVICE = {"name": "我的服务"}
    ITEM_SHARE = {"name": "共享"}
    ITEM_ALBUM = {"name": "相册"}
    # 「设置」入口未在首屏 dump 中出现，可能在列表更下方，保持待验证
    ITEM_SETTINGS = {"name": "设置"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: IOSUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="ios")

    # ---------------- 业务方法（与 Android 端同名同义） ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「我的」页面加载完成（以「二维码」+「扫一扫」按钮同时出现为识别点）。

        轮询检查两个识别点是否同时可见，避免仅出现单一元素时误判。

        :param timeout: 等待超时时间（秒）
        :return: 页面加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_my_page():
                logger.debug(f"「我的」页面识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"「我的」页面识别点在 {timeout}s 内未同时出现："
            f"BTN_QR_CODE={self.exists(self.BTN_QR_CODE)}，"
            f"BTN_SCAN={self.exists(self.BTN_SCAN)}"
        )
        return False

    def is_my_page(self) -> bool:
        """判断当前是否处于「我的」页面（两个识别点同时存在）。

        :return: 「二维码」与「扫一扫」按钮同时存在返回 True
        """
        return self.exists(self.BTN_QR_CODE) and self.exists(self.BTN_SCAN)

    def is_item_visible(self, item_locator: dict) -> bool:
        """判断指定功能入口是否可见。

        :param item_locator: 功能入口定位器
        :return: 可见返回 True
        """
        return self.exists(item_locator)

    def open_settings(self) -> None:
        """点击「设置」入口。"""
        self.click(self.ITEM_SETTINGS)
