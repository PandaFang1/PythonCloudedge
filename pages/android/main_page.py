"""CloudEdge 安卓端主页面。

页面职责：
1. 维护主界面（MainActivity）的元素定位器
2. 提供主页面级业务方法，与 iOS 端云际主页面保持同名接口

定位器约定：
- 优先使用基本选择器（name/text/type），其次相对选择器，最后索引与正则
- 定位器统一为类属性常量，便于维护
- 主页面识别点（ivAddDevice / ivMenu）已通过真机验证
"""

import time

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class CloudEdgeMainPage(BasePage):
    """CloudEdge 主页面（Android）。"""

    # ---------------- 元素定位器 ----------------
    # 主页面识别点：右上角「添加设备」+「菜单」按钮（真机验证过的 resource-id）
    BTN_ADD_DEVICE = {"name": "com.cloudedge.smarteye:id/ivAddDevice"}
    BTN_MENU = {"name": "com.cloudedge.smarteye:id/ivMenu"}

    # 底部 Tab 栏（真机验证：首页 / 消息 / 我的）
    TAB_HOME = {"text": "首页"}
    TAB_MESSAGE = {"text": "消息"}
    TAB_MY = {"text": "我的"}

    # 欢迎页/登录页可能的跳过按钮（app 首启场景）
    BTN_SKIP = {"text": "跳过"}

    # 登录后新手引导浮层的按钮（文本匹配，引导可能多页，逐页点击直至消失）
    GUIDE_BTN_NEXT = {"text": "下一步"}
    GUIDE_BTN_DONE_CANDIDATES = (
        {"text": "知道了"},
        {"text": "完成"},
        {"text": "立即体验"},
        {"text": "开始使用"},
        {"text": "进入"},
    )

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

    def handle_guide(self, max_steps: int = 10, interval: float = 0.5) -> bool:
        """处理登录后的新手引导浮层（如有）。

        引导页可能有多页，每页点「下一步」推进；末页按钮可能为
        「完成」/「立即体验」/「开始使用」等，逐个尝试点击，
        直到无引导按钮残留或达到 max_steps 上限。

        :param max_steps: 最大点击次数（防死循环）
        :param interval: 每次点击后的等待时间（秒）
        :return: 处理过至少一个引导按钮返回 True，无引导返回 False
        """
        clicked_any = False
        for _ in range(max_steps):
            clicked = False
            if self.exists(self.GUIDE_BTN_NEXT):
                self.click(self.GUIDE_BTN_NEXT)
                clicked = True
            else:
                for btn in self.GUIDE_BTN_DONE_CANDIDATES:
                    if self.exists(btn):
                        self.click(btn)
                        clicked = True
                        break
            if clicked:
                clicked_any = True
                time.sleep(interval)
            else:
                break
        if clicked_any:
            logger.info("已处理登录后新手引导（无引导按钮残留）")
            time.sleep(0.5)
        else:
            logger.debug("未检测到新手引导浮层")
        return clicked_any

    def get_device_list(self) -> list:
        """获取首页设备列表中所有可见设备的 SN / 名称。

        真机验证（2026-10-09）：
        - 普通设备：`tvDeviceName`（如 '132003599'）
        - Chime Base：`tvJingleBaseName`（设备 SN 数字串），
          在线状态为 `tvJingleBaseOnline`（'在线' / '离线'）
        返回两者合集（仅设备名/SN）。

        :return: 设备 SN / 名称列表
        """
        TV_DEVICE_NAME = "com.cloudedge.smarteye:id/tvDeviceName"
        TV_JINGLE_BASE_NAME = "com.cloudedge.smarteye:id/tvJingleBaseName"
        result: list = []
        for rid in (TV_DEVICE_NAME, TV_JINGLE_BASE_NAME):
            for node in self.poco(rid):
                text = node.attr("text")
                if text:
                    result.append(text)
        logger.debug(f"首页设备列表：{result}")
        return result

    def is_device_online(self, sn: str) -> bool:
        """判断指定 SN 的 Chime Base 在主页是否为「在线」状态。

        :param sn: 设备 SN
        :return: 在线返回 True；未找到或离线返回 False
        """
        TV_JINGLE_BASE_NAME = "com.cloudedge.smarteye:id/tvJingleBaseName"
        TV_JINGLE_BASE_ONLINE = "com.cloudedge.smarteye:id/tvJingleBaseOnline"
        for node in self.poco(TV_JINGLE_BASE_NAME):
            if node.attr("text") == sn:
                row = node.parent()
                online_node = row.offspring(TV_JINGLE_BASE_ONLINE)
                if online_node.exists():
                    status = online_node.attr("text") or ""
                    return "在线" in status
        return False

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

    # ---------------- 添加设备弹窗（ivAddDevice 唤出）----------------

    # 弹窗条目（`tvName` 文本=「扫一扫」/「添加设备」）
    POPUP_ITEM_ADD_DEVICE = "添加设备"
    POPUP_ITEM_SCAN = "扫一扫"

    def open_add_device_menu(self, wait_seconds: float = 0.8) -> None:
        """点击右上「添加设备」按钮，唤出弹窗（扫一扫 / 添加设备）。

        弹窗元素约 0.5s 内渲染完成，默认等待 0.8s 后再操作。

        :param wait_seconds: 唤起弹窗后等待渲染时间（秒）
        """
        self.click(self.BTN_ADD_DEVICE)
        time.sleep(wait_seconds)
        logger.info("已唤起「添加设备」弹窗")

    def click_add_device_popup_item(self, item_text: str) -> None:
        """点击添加设备弹窗中的指定条目。

        :param item_text: 条目文本，如「扫一扫」/「添加设备」
        """
        target = self.poco("com.cloudedge.smarteye:id/tvName", text=item_text)
        if not target.exists():
            raise ElementNotFoundError(
                f"添加设备弹窗中未找到条目「{item_text}」，请确认弹窗已唤起"
            )
        target.click()
        logger.info(f"已点击弹窗条目「{item_text}」")

    def open_add_device_category_page(self) -> None:
        """从主页进入设备类别选择页（点击 ivAddDevice → 点击「添加设备」条目）。"""
        self.open_add_device_menu()
        self.click_add_device_popup_item(self.POPUP_ITEM_ADD_DEVICE)
