"""CloudEdge 安卓端「我的」页面。

页面职责：
1. 维护「我的」个人中心页的元素定位器
2. 提供页面级业务方法，与 iOS 端云际「我的」页面保持同名接口

定位器说明：
- iv_qr_code（二维码入口）与 feedback（意见反馈）已通过真机验证
- 功能入口（家庭管理/我的服务/共享/相册/设置）为文本定位
"""

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


class CloudEdgeMyPage(BasePage):
    """CloudEdge「我的」页面（Android）。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点：二维码入口 + 意见反馈（真机验证过的 resource-id）
    BTN_QR_CODE = {"name": "com.cloudedge.smarteye:id/iv_qr_code"}
    BTN_FEEDBACK = {"name": "com.cloudedge.smarteye:id/feedback"}

    # 功能入口（文本定位）
    ITEM_FAMILY_MANAGE = {"text": "家庭管理"}
    ITEM_MY_SERVICE = {"text": "我的服务"}
    ITEM_SHARE = {"text": "共享"}
    ITEM_ALBUM = {"text": "相册"}
    ITEM_SETTINGS = {"text": "设置"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: AndroidUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="android")

    # ---------------- 业务方法（与 iOS 端同名同义） ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「我的」页面加载完成（以「二维码入口」+「意见反馈」同时出现为识别点）。

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
            f"BTN_FEEDBACK={self.exists(self.BTN_FEEDBACK)}"
        )
        return False

    def is_my_page(self) -> bool:
        """判断当前是否处于「我的」页面（两个识别点同时存在）。

        :return: 「二维码入口」与「意见反馈」同时存在返回 True
        """
        return self.exists(self.BTN_QR_CODE) and self.exists(self.BTN_FEEDBACK)

    def is_item_visible(self, item_locator: dict) -> bool:
        """判断指定功能入口是否可见。

        :param item_locator: 功能入口定位器
        :return: 可见返回 True
        """
        return self.exists(item_locator)

    def open_settings(self) -> None:
        """点击「设置」入口。"""
        self.click(self.ITEM_SETTINGS)
