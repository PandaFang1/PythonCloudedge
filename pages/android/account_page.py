"""CloudEdge 安卓端「我的信息」页面（账号设置 / 退出登录）。

页面职责：
1. 维护「我的信息」页（MyInformationActivity）及退出登录确认弹窗的元素定位器
2. 提供退出登录业务方法：点击退出 → 弹窗确认/取消 → 等待回到登录页

进入路径：「我的」页点击账号入口 tv_account → MyInformationActivity
定位器说明（真机 poco dump 验证，udid=cfed8c100822，1080×2400）：
- 页面识别点：tv_title（「我的信息」标题）+ logout_layout（底部「退出登录」按钮）
- 退出弹窗：title「提示」/ message「退出后不会删除任何历史数据…」/
  negativeButton「取消」/ positiveButton「确定」
"""

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class CloudEdgeAccountPage(BasePage):
    """CloudEdge「我的信息」页面（Android）：账号信息 + 退出登录。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点：标题「我的信息」+ 底部「退出登录」按钮
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    LOGOUT_LAYOUT = {"name": "com.cloudedge.smarteye:id/logout_layout"}

    # 其他控件
    TOOL_BAR = {"name": "com.cloudedge.smarteye:id/tool_bar"}
    IV_BACK = {"name": "com.cloudedge.smarteye:id/iv_back"}
    TV_ACCOUNT = {"name": "com.cloudedge.smarteye:id/tv_account"}
    TV_ACCOUNT_TITLE = {"name": "com.cloudedge.smarteye:id/tv_account_title"}
    RESET_PASSWORD_LAYOUT = {"name": "com.cloudedge.smarteye:id/reset_password_layout"}
    REGION_LAYOUT = {"name": "com.cloudedge.smarteye:id/region_layout"}

    # 退出登录确认弹窗
    DIALOG_TITLE = {"name": "com.cloudedge.smarteye:id/title"}
    DIALOG_MESSAGE = {"name": "com.cloudedge.smarteye:id/message"}
    DIALOG_BTN_CANCEL = {"name": "com.cloudedge.smarteye:id/negativeButton"}
    DIALOG_BTN_CONFIRM = {"name": "com.cloudedge.smarteye:id/positiveButton"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: AndroidUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="android")

    # ---------------- 业务方法 ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「我的信息」页加载完成（标题 + 退出登录按钮同时出现）。

        轮询检查两个识别点是否同时可见，避免仅出现单一元素时误判。

        :param timeout: 等待超时时间（秒）
        :return: 页面加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_account_page():
                logger.debug(f"「我的信息」页识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"「我的信息」页识别点在 {timeout}s 内未同时出现："
            f"TV_TITLE={self.exists(self.TV_TITLE)}，"
            f"LOGOUT_LAYOUT={self.exists(self.LOGOUT_LAYOUT)}"
        )
        return False

    def is_account_page(self) -> bool:
        """判断当前是否处于「我的信息」页（两个识别点同时存在）。

        :return: 标题「我的信息」与「退出登录」按钮同时存在返回 True
        """
        return self.exists(self.TV_TITLE) and self.exists(self.LOGOUT_LAYOUT)

    def get_account(self) -> str:
        """获取当前登录账号文本（如 `358632847@qq.com`）。

        :return: 账号文本；未渲染时返回空串
        """
        return self.get_text(self.TV_ACCOUNT)

    def click_logout(self) -> None:
        """点击底部「退出登录」按钮，唤起确认弹窗。"""
        self.click(self.LOGOUT_LAYOUT)
        logger.info("已点击「退出登录」按钮")

    def is_logout_dialog_visible(self, timeout: float = 5.0) -> bool:
        """判断退出登录确认弹窗是否可见（以 message 文本控件出现为准）。

        :param timeout: 等待超时时间（秒）
        :return: 弹窗可见返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.DIALOG_MESSAGE):
                return True
            time.sleep(0.3)
        return False

    def cancel_logout(self) -> None:
        """在确认弹窗中点击「取消」，关闭弹窗并停留在「我的信息」页。"""
        self.click(self.DIALOG_BTN_CANCEL)
        logger.info("已点击弹窗「取消」，取消退出登录")

    def confirm_logout(self) -> None:
        """在确认弹窗中点击「确定」，确认退出登录。"""
        self.click(self.DIALOG_BTN_CONFIRM)
        logger.info("已点击弹窗「确定」，确认退出登录")

    def wait_back_to_login(self, timeout: float = 30.0) -> bool:
        """等待退出登录后回到登录页（以前台 Activity 切回 LoginActivity 为准）。

        依据：确认退出后 app 会结束 MainActivity 并回到 LoginActivity。
        与登录用例一致，采用系统级 Activity 判定（比 Poco DOM 更稳定）。

        :param timeout: 等待超时时间（秒）
        :return: 已回到登录页返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            activity = self.get_current_activity()
            if "LoginActivity" in activity:
                logger.info(f"已退出登录并回到登录页（Activity={activity.strip()}）")
                return True
            time.sleep(1.0)

        logger.warning(f"退出登录后 {timeout}s 内未回到 LoginActivity"
                       f"（当前 Activity={self.get_current_activity().strip()}）")
        return False

    def logout(self, confirm: bool = True) -> None:
        """一站式退出登录：点击「退出登录」→ 弹窗中选择「确定 / 取消」。

        confirm=True 时等待回到登录页（Activity 判定）；confirm=False 时
        仅断言弹窗已关闭且停留在「我的信息」页。

        :param confirm: True 确认退出，False 取消退出
        :raises ElementNotFoundError: 弹窗未出现或后续断言失败时抛出
        """
        import time

        self.click_logout()

        if not self.is_logout_dialog_visible(timeout=5):
            raise ElementNotFoundError("点击「退出登录」后确认弹窗未出现")

        if not confirm:
            self.cancel_logout()
            time.sleep(0.5)
            if self.is_logout_dialog_visible(timeout=1.0) or not self.is_account_page():
                raise ElementNotFoundError(
                    "点击弹窗「取消」后未停留在「我的信息」页（弹窗可能未关闭）"
                )
            logger.info("已取消退出登录，停留在「我的信息」页")
            return

        self.confirm_logout()
        if not self.wait_back_to_login(timeout=30):
            raise ElementNotFoundError(
                "确认退出登录后未回到登录页（LoginActivity 未出现）"
            )
