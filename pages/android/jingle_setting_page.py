"""智能门铃 Chime Base 设置页 PO — jingle_setting。

封装 jingle 设置页（CameraSettingNewActivity）的全部交互，定位器均经
真机 dump 验证（2026-10-10，Redmi Note 11 5G）：

    jingle 首页（JingleBaseActivity）--iv_submit--> 设置页
        ├── 顶部工具栏：iv_back（返回）/ tv_title（'设置'）/ iv_submit
        ├── 设备信息卡片（layout_device_info）--点击--> 设备信息页
        ├── 宫格（rv_top）：铃铛勿扰 / 铃声设置 / 接收报警推送 / 设备分享
        │       └── 接收报警推送为 switch_button 开关（点击弹确认框）
        ├── 列表（rv_main）：声音设置 / 存储管理 / 通用设置
        ├── btn_reset（重启设备，点击弹确认框）
        └── btn_delete（删除设备，删除流程见 JingleDeletePage）

弹框说明（两套 id，注意区分）：
- 报警推送/重启确认弹框：title / message / negativeButton / positiveButton
  （系统样式，与退出登录弹框同款）
- 删除确认弹框：tv_ai_search_title / tv_ai_search_des / tv_cancel /
  tv_confirm（详见 JingleDeletePage）

用例用法：
    setting_page = PageFactory.create(
        "android", "jingle_setting_page", poco=poco, udid=udid,
    )
    info_page = setting_page.open_device_info_page()      # 支持链式调用
    info_page.back_to_setting_page()
    setting_page.toggle_alarm_push(confirm=False)          # 弹框点「取消」
    setting_page.restart_device(confirm=True)              # 重启门铃
"""

from __future__ import annotations

from typing import Any

from pages.android.jingle_bell_dnd_page import JingleBellDndPage
from pages.android.jingle_device_info_page import JingleDeviceInfoPage
from pages.android.jingle_device_share_page import JingleDeviceSharePage
from pages.android.jingle_general_page import JingleGeneralPage
from pages.android.jingle_ringtone_page import JingleRingtonePage
from pages.android.jingle_sound_page import JingleSoundPage
from pages.android.jingle_storage_page import JingleStoragePage
from pages.android.jingle_sub_page_base import RID
from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleSettingPage(BasePage):
    """jingle 设置页（CameraSettingNewActivity，标题='设置'）。

    页面识别点：工具栏标题 tv_title 文本='设置'。
    各子页面入口方法返回对应子页面实例（支持链式调用）。
    """

    # ==================== 顶部工具栏 ====================
    TOOLBAR_BACK = {"name": RID + "iv_back"}      # 返回 jingle 首页
    TOOLBAR_TITLE = {"name": RID + "tv_title"}    # 页面标题（识别点）
    TITLE_TEXT = "设置"
    TOOLBAR_SUBMIT = {"name": RID + "iv_submit"}  # 右上角按钮（当前页无实际功能入口，保留备用）

    # ==================== 设备信息卡片（点击进设备信息页） ====================
    CARD_DEVICE_INFO = {"name": RID + "layout_device_info"}
    CARD_DEVICE_SN = {"name": RID + "tv_device_name_info"}
    CARD_WIFI = {"name": RID + "tv_wifi"}         # 文本形如 '信号强度：100%'
    CARD_TIME_ZONE = {"name": RID + "tv_time_zone"}  # 文本形如 '时区:GMT+08:00'

    # ==================== 宫格入口（rv_top，按 tv_title 文本定位） ====================
    ENTRY_BELL_DND = {"text": "铃铛勿扰"}
    ENTRY_RINGTONE = {"text": "铃声设置"}
    ENTRY_DEVICE_SHARE = {"text": "设备分享"}
    ENTRY_ALARM_PUSH = {"text": "接收报警推送"}
    SWITCH_ALARM_PUSH = {"name": RID + "switch_button"}  # 报警推送开关

    # ==================== 列表入口（rv_main，按 tv_title 文本定位） ====================
    ENTRY_SOUND = {"text": "声音设置"}
    ENTRY_STORAGE = {"text": "存储管理"}
    ENTRY_GENERAL = {"text": "通用设置"}

    # ==================== 底部操作按钮 ====================
    BTN_RESTART = {"name": RID + "btn_reset"}     # '重启设备'
    BTN_DELETE = {"name": RID + "btn_delete"}     # '删除设备'（删除流程见 JingleDeletePage）

    # ==================== 报警推送 / 重启确认弹框（系统样式） ====================
    DIALOG_TITLE = {"name": RID + "title"}
    PUSH_DIALOG_TITLE_TEXT = "是否关闭设备的消息通知？"
    DIALOG_MESSAGE = {"name": RID + "message"}
    RESTART_DIALOG_MESSAGE_TEXT = "你确定要重启设备吗？"
    DIALOG_BTN_CANCEL = {"name": RID + "negativeButton"}   # '取消'
    DIALOG_BTN_CONFIRM = {"name": RID + "positiveButton"}  # '确定'

    # jingle 首页 Activity 关键字（返回后验证用）
    JINGLE_HOME_ACTIVITY_KEYWORD = "JingleBaseActivity"

    def __init__(self, poco: Any, udid: str = "") -> None:
        super().__init__(poco, udid)

    # ==================== 页面识别 ====================

    def is_setting_page(self) -> bool:
        """判定当前是否在设置页（标题文本='设置'）。"""
        try:
            return (self.exists(self.TOOLBAR_TITLE)
                    and self.get_text(self.TOOLBAR_TITLE) == self.TITLE_TEXT)
        except Exception:  # noqa: BLE001 弹框遮挡 / 切换动画中按未就绪处理
            return False

    def wait_for_page_loaded(self, timeout: float = 15.0) -> bool:
        """等待设置页加载完成（标题文本='设置'）。

        :param timeout: 等待超时（秒）
        :return: 加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_setting_page():
                logger.debug("jingle 设置页已加载")
                return True
            time.sleep(0.5)
        logger.warning(
            f"jingle 设置页在 {timeout}s 内未加载完成"
            f"（当前 Activity={self.get_current_activity()}）"
        )
        return False

    # ==================== 顶部工具栏 ====================

    def back_to_jingle_home(self) -> "JingleSettingPage":
        """点击工具栏返回按钮，回到 jingle 首页。

        支持链式调用。
        :raises ElementNotFoundError: 点击后未离开设置页
        """
        self.click(self.TOOLBAR_BACK)
        import time

        deadline = time.time() + 10
        while time.time() < deadline:
            if self.JINGLE_HOME_ACTIVITY_KEYWORD in self.get_current_activity():
                logger.info("设置页：已返回 jingle 首页")
                return self
            time.sleep(0.5)
        raise ElementNotFoundError(
            f"点击返回后未回到 jingle 首页（当前 Activity="
            f"{self.get_current_activity()}）"
        )

    # ==================== 设备信息卡片 ====================

    def get_device_sn(self) -> str:
        """读取设备信息卡片中的设备 SN。"""
        return self.get_text(self.CARD_DEVICE_SN)

    def get_wifi_signal(self) -> str:
        """读取设备信息卡片中的 WiFi 信号文本（形如 '信号强度：100%'）。"""
        return self.get_text(self.CARD_WIFI)

    def get_time_zone(self) -> str:
        """读取设备信息卡片中的时区文本（形如 '时区:GMT+08:00'）。"""
        return self.get_text(self.CARD_TIME_ZONE)

    # ==================== 子页面入口（点击 → 验证 → 返回子页面实例） ====================

    def _open_sub_page(self, entry, sub_page, action_desc: str):
        """通用入口导航：点击入口 → 验证子页面加载 → 返回实例。

        :param entry: 入口元素定位器
        :param sub_page: 子页面实例（已创建）
        :param action_desc: 动作描述（日志用）
        :return: 加载完成的子页面实例（支持链式调用）
        :raises ElementNotFoundError: 点击后子页面未加载
        """
        self.click(entry)
        logger.info(f"设置页：已点击{action_desc}")
        if not sub_page.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError(
                f"点击{action_desc}后未进入对应页面"
                f"（当前 Activity={self.get_current_activity()}）"
            )
        return sub_page

    def open_device_info_page(self) -> JingleDeviceInfoPage:
        """点击设备信息卡片，进入设备信息页。支持链式调用。"""
        return self._open_sub_page(
            self.CARD_DEVICE_INFO,
            JingleDeviceInfoPage(self.poco, self.udid),
            "设备信息卡片",
        )

    def open_bell_dnd_page(self) -> JingleBellDndPage:
        """点击宫格「铃铛勿扰」，进入铃铛勿扰页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_BELL_DND,
            JingleBellDndPage(self.poco, self.udid),
            "「铃铛勿扰」",
        )

    def open_ringtone_page(self) -> JingleRingtonePage:
        """点击宫格「铃声设置」，进入铃声设置页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_RINGTONE,
            JingleRingtonePage(self.poco, self.udid),
            "「铃声设置」",
        )

    def open_device_share_page(self) -> JingleDeviceSharePage:
        """点击宫格「设备分享」，进入设备分享页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_DEVICE_SHARE,
            JingleDeviceSharePage(self.poco, self.udid),
            "「设备分享」",
        )

    def open_sound_page(self) -> JingleSoundPage:
        """点击列表「声音设置」，进入声音设置页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_SOUND,
            JingleSoundPage(self.poco, self.udid),
            "「声音设置」",
        )

    def open_storage_page(self) -> JingleStoragePage:
        """点击列表「存储管理」，进入存储管理页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_STORAGE,
            JingleStoragePage(self.poco, self.udid),
            "「存储管理」",
        )

    def open_general_page(self) -> JingleGeneralPage:
        """点击列表「通用设置」，进入通用设置页。支持链式调用。"""
        return self._open_sub_page(
            self.ENTRY_GENERAL,
            JingleGeneralPage(self.poco, self.udid),
            "「通用设置」",
        )

    # ==================== 报警推送开关 ====================

    def is_push_confirm_dialog_shown(self) -> bool:
        """判定「是否关闭设备的消息通知？」确认弹框是否在屏。"""
        try:
            return (self.exists(self.DIALOG_TITLE)
                    and self.get_text(self.DIALOG_TITLE)
                    == self.PUSH_DIALOG_TITLE_TEXT)
        except Exception:  # noqa: BLE001 弹框未出现时节点不可查
            return False

    def toggle_alarm_push(self, confirm: bool = True) -> "JingleSettingPage":
        """点击「接收报警推送」开关并处理确认弹框。

        真机验证（2026-10-10）：
        - 关闭方向：点击开关弹「是否关闭设备的消息通知？」确认框，
          「确定」生效、「取消」放弃
        - 开启方向：直接生效，不弹确认框

        ⚠️ 开关 checked 属性不可靠（真机 dump 恒为 false），
        不提供读取开关状态的方法，状态断言请以推送行为为准。

        :param confirm: 弹框出现时 True 点「确定」/ False 点「取消」
        :return: self（支持链式调用）
        """
        self.click(self.SWITCH_ALARM_PUSH)
        logger.info(f"设置页：已点击报警推送开关（confirm={confirm}）")
        if self.is_push_confirm_dialog_shown():
            btn = self.DIALOG_BTN_CONFIRM if confirm else self.DIALOG_BTN_CANCEL
            self.click(btn)
            logger.info(
                f"报警推送确认弹框：已点击「{'确定' if confirm else '取消'}」"
            )
        else:
            logger.info("报警推送开关：未弹确认框（开启方向直接生效）")
        return self

    # ==================== 重启设备 ====================

    def restart_device(self, confirm: bool = True) -> "JingleSettingPage":
        """点击「重启设备」并处理确认弹框。

        真机验证（2026-10-10）：
        - 「取消」：弹框消失，停留在设置页
        - 「确定」：门铃重启，稍后提示「设置成功」，停留在设置页
        （「设置成功」为系统 Toast，poco accessibility 树不可见，
        如需断言请用截图比对）

        :param confirm: True 点「确定」（重启硬件）/ False 点「取消」
        :return: self（支持链式调用）
        :raises ElementNotFoundError: 确认弹框未出现
        """
        self.click(self.BTN_RESTART)
        logger.info(f"设置页：已点击「重启设备」（confirm={confirm}）")

        # 弹框以 message 文本判定（与报警推送弹框共用按钮 id 但文案不同）
        import time

        deadline = time.time() + 10
        shown = False
        while time.time() < deadline:
            try:
                if (self.exists(self.DIALOG_MESSAGE)
                        and self.get_text(self.DIALOG_MESSAGE)
                        == self.RESTART_DIALOG_MESSAGE_TEXT):
                    shown = True
                    break
            except Exception:  # noqa: BLE001 弹框出现中节点可能瞬时不可查
                pass
            time.sleep(0.5)
        if not shown:
            raise ElementNotFoundError(
                f"点击「重启设备」后确认弹框（{self.RESTART_DIALOG_MESSAGE_TEXT!r}）"
                f"未出现"
            )

        btn = self.DIALOG_BTN_CONFIRM if confirm else self.DIALOG_BTN_CANCEL
        self.click(btn)
        logger.info(
            f"重启确认弹框：已点击「{'确定' if confirm else '取消'}」"
        )
        # 两条路径均停留在设置页，等待弹框消失后验证
        self.wait_for_element_disappear(self.DIALOG_MESSAGE, timeout=10)
        if not self.wait_for_page_loaded(timeout=15.0):
            raise ElementNotFoundError("重启确认后未停留在设置页")
        logger.info(f"重启设备：confirm={confirm}，已停留在设置页")
        return self
