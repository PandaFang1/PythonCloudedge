"""云际 iOS 端「消息」页面。

页面职责与 CloudEdgeMessagePage 对齐：实现同名业务接口，
定位器基于云际 iOS 端 UI 结构维护（占位定位器，待 iOS 真机补充真实识别数据）。
"""

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


class YunjiMessagePage(BasePage):
    """云际「消息」页面（iOS）。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点：顶部「报警」「分享」Tab（真机验证，name 属性定位）
    TAB_ALARM = {"name": "报警"}
    TAB_SHARE = {"name": "分享"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: IOSUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="ios")

    # ---------------- 业务方法（与 Android 端同名同义） ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「消息」页面加载完成（以顶部「报警」+「分享」Tab 同时出现为识别点）。

        轮询检查两个识别点是否同时可见，避免仅出现单一元素时误判。

        :param timeout: 等待超时时间（秒）
        :return: 页面加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_message_page():
                logger.debug(f"「消息」页面识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"「消息」页面识别点在 {timeout}s 内未同时出现："
            f"TAB_ALARM={self.exists(self.TAB_ALARM)}，"
            f"TAB_SHARE={self.exists(self.TAB_SHARE)}"
        )
        return False

    def is_message_page(self) -> bool:
        """判断当前是否处于「消息」页面（两个识别点同时存在）。

        :return: 「报警」与「分享」Tab 同时存在返回 True
        """
        return self.exists(self.TAB_ALARM) and self.exists(self.TAB_SHARE)

    def switch_to_alarm(self) -> None:
        """切换到「报警」Tab。"""
        self.click(self.TAB_ALARM)

    def switch_to_share(self) -> None:
        """切换到「分享」Tab。"""
        self.click(self.TAB_SHARE)
