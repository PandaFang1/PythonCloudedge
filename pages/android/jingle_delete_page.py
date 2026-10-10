"""智能门铃（Chime Base）一站式删除页面 PO — jingle_delete。

封装从主页开始到「删除完成（主页断言设备列表无 SN）」的完整删除流程：

    主页（MainActivity）
        → 点击设备 SN（Chime Base 条目 tvJingleNeutralName）
        → jingle 首页（JingleBaseActivity，标题=SN）
        → 点击右上角设置按钮（iv_submit）
        → 设置页（CameraSettingNewActivity，标题='设置'）
        → 向下滑动找到「删除设备」（btn_delete）并点击
        → 确认弹框（'确定要删除该设备和子设备及所关联的数据？'）
          → 点击「删除」（tv_confirm）
        → app 自动返回主页
        → 断言主页设备列表不含该 SN（删除成功）

内部组合复用既有模块，不重复实现：
- `CloudEdgeMainPage` — 主页设备点击 / 设备列表断言
- 各页面定位器均经真机 dump 验证（2026-10-10，Redmi Note 11 5G）

用例用法：
    jingle_delete_page = PageFactory.create(
        "android", "jingle_delete_page", poco=poco, udid=udid,
    )
    jingle_delete_page.delete_jingle_device()          # 全默认参数
    jingle_delete_page.delete_jingle_device(sn="...")  # 指定 SN
"""

from __future__ import annotations

import time
from typing import Any, List, Optional

from pages.android.add_device_flow import DEFAULT_DEVICE_SN
from pages.android.main_page import CloudEdgeMainPage
from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class JingleDeletePage(BasePage):
    """智能门铃 Chime Base 一站式删除页面（从主页到删除完成）。

    作为门面（Facade）PO：定位器维护 + 删除链路串联，
    对用例暴露单一入口 `delete_jingle_device()`。
    """

    # 默认目标 SN（与添加流程共用同一常量，模块级导入 DEFAULT_DEVICE_SN）

    # ==================== 主页（复用 CloudEdgeMainPage）====================

    # ==================== jingle 首页（JingleBaseActivity）====================
    # 页面识别点：工具栏标题 = 设备 SN
    JINGLE_TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    # 右上角设置按钮
    JINGLE_BTN_SETTING = {"name": "com.cloudedge.smarteye:id/iv_submit"}

    # ==================== jingle 首页识别点（补充，2026-10-10 增）====================
    # 在工具栏标题=SN 之外再叠加 2 个稳定控件，3 元素同时存在才判定进入
    # jingle 首页，进一步降低点击落空 / 标题文本与设备 SN 撞名导致的误判。
    JINGLE_IV_STATE_ON = {
        "name": "com.cloudedge.smarteye:id/iv_state_on",
    }  # 设备状态图标（在线/离线指示）
    JINGLE_SWITCH_BTN_SCHEDULES = {
        "name": "com.cloudedge.smarteye:id/switch_btn_schedules",
    }  # 「日程」开关按钮

    # ==================== 设置页（CameraSettingNewActivity）====================
    SETTING_TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    SETTING_TITLE_TEXT = "设置"
    # 底部「删除设备」按钮（rv_main 列表末尾，可能需下滑才可见）
    SETTING_BTN_DELETE = {"name": "com.cloudedge.smarteye:id/btn_delete"}
    DELETE_BUTTON_TEXT = "删除设备"

    # ==================== 删除确认弹框 ====================
    DIALOG_TITLE = {"name": "com.cloudedge.smarteye:id/tv_ai_search_title"}
    DIALOG_TITLE_TEXT = "温馨提示"
    DIALOG_DESC = {"name": "com.cloudedge.smarteye:id/tv_ai_search_des"}
    DIALOG_BTN_CANCEL = {"name": "com.cloudedge.smarteye:id/tv_cancel"}
    DIALOG_BTN_CONFIRM = {"name": "com.cloudedge.smarteye:id/tv_confirm"}
    DIALOG_CONFIRM_TEXT = "删除"

    def __init__(self, poco: Any, udid: str = "") -> None:
        super().__init__(poco, udid)
        self.main_page = CloudEdgeMainPage(poco, udid)

    # ==================== 页面等待 ====================

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待主页加载完成（本流程的起点页面）。"""
        return self.main_page.wait_for_page_loaded(timeout=timeout)

    # ==================== 各步骤方法 ====================

    def open_jingle_home_by_sn(
        self, sn: str, timeout: float = 30.0, retries: int = 3,
    ) -> None:
        """步骤 1：主页点击设备 SN，进入 jingle 首页（JingleBaseActivity）。

        点击后验证工具栏标题是否变为设备 SN；未生效（页面加载动画中
        poco 坐标不准导致点击落空）则重新点击，最多 retries 次。

        :param sn: 设备 SN（主页 Chime Base 条目名，`tvJingleNeutralName`）
        :param timeout: 主页加载 + 每次点击后等待的超时（秒）
        :param retries: 点击落空时的最大重试次数
        :raises ElementNotFoundError: 主页未见该设备或重试后仍未进入
        """
        if not self.main_page.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(f"主页在 {timeout}s 内未加载")

        # Chime Base 条目名候选（不同布局状态可能用不同 id）
        name_rids = (
            "com.cloudedge.smarteye:id/tvJingleNeutralName",
            "com.cloudedge.smarteye:id/tvJingleBaseName",
        )
        target = None
        for rid in name_rids:
            node = self.poco(rid, text=sn)
            if node.exists():
                target = node
                break
        if target is None:
            devices = self.main_page.get_device_list()
            raise ElementNotFoundError(
                f"主页未见设备 SN={sn!r}（当前设备列表：{devices}）"
            )

        for attempt in range(1, retries + 1):
            target.click()
            logger.info(f"主页：已点击设备「{sn}」（第 {attempt}/{retries} 次）")

            deadline = time.time() + 12
            while time.time() < deadline:
                # 2026-10-10 起：jingle 首页采用 3 元素组合识别点
                # (tv_title==SN) AND iv_state_on AND switch_btn_schedules
                if (self.exists(self.JINGLE_TV_TITLE)
                        and (self.get_text(self.JINGLE_TV_TITLE) == sn)
                        and self.exists(self.JINGLE_IV_STATE_ON)
                        and self.exists(self.JINGLE_SWITCH_BTN_SCHEDULES)):
                    logger.info(
                        f"已进入 jingle 首页（标题=SN={sn!r}，"
                        f"iv_state_on + switch_btn_schedules 均已出现）"
                    )
                    return
                time.sleep(0.5)
            logger.warning(
                f"第 {attempt}/{retries} 次点击设备「{sn}」未进入 jingle 首页"
                f"（当前 Activity={self.get_current_activity().strip()}），重试"
            )
        raise ElementNotFoundError(
            f"点击设备「{sn}」重试 {retries} 次后仍未进入 jingle 首页"
        )

    def open_setting_page(
        self, timeout: float = 15.0, retries: int = 3,
    ) -> None:
        """步骤 2：jingle 首页点右上角设置按钮，进入设置页。

        点击后验证设置页标题是否为「设置」；未生效（点击落空）则在
        确认仍在 jingle 首页后重新点击，最多 retries 次。

        :param timeout: 设置按钮等待 + 每次点击后等待的超时（秒）
        :param retries: 点击落空时的最大重试次数
        :raises ElementNotFoundError: 重试后仍未进入设置页
        """
        if not self.wait_for_element(self.JINGLE_BTN_SETTING, timeout=timeout):
            raise ElementNotFoundError(
                f"jingle 首页右上角设置按钮（iv_submit）{timeout}s 内未出现"
            )

        for attempt in range(1, retries + 1):
            self.click(self.JINGLE_BTN_SETTING)
            logger.info(f"jingle 首页：已点击右上角设置按钮（第 {attempt}/{retries} 次）")

            deadline = time.time() + 10
            while time.time() < deadline:
                if self.exists(self.SETTING_TV_TITLE) and \
                        (self.get_text(self.SETTING_TV_TITLE) == self.SETTING_TITLE_TEXT):
                    logger.info("已进入设置页（标题='设置'）")
                    return
                time.sleep(0.5)

            # 未进入设置页：若仍在 jingle 首页（标题=SN）则等待按钮可点后重试
            if self.exists(self.JINGLE_TV_TITLE):
                logger.warning(
                    f"第 {attempt}/{retries} 次点击设置按钮未进入设置页"
                    f"（当前 Activity={self.get_current_activity().strip()}），重试"
                )
                self.wait_for_element(self.JINGLE_BTN_SETTING, timeout=timeout)
            else:
                # 已离开 jingle 首页但也不是设置页，交由外层重试判定
                logger.warning(
                    f"第 {attempt}/{retries} 次点击后离开 jingle 首页但未到设置页，"
                    f"Activity={self.get_current_activity().strip()}"
                )

        if not (self.exists(self.SETTING_TV_TITLE) and
                (self.get_text(self.SETTING_TV_TITLE) == self.SETTING_TITLE_TEXT)):
            raise ElementNotFoundError(
                f"点击设置按钮重试 {retries} 次后仍未进入设置页"
                f"（标题应为 {self.SETTING_TITLE_TEXT!r}，当前 Activity="
                f"{self.get_current_activity().strip()}）"
            )

    def _is_delete_btn_visible(self) -> bool:
        """判断「删除设备」按钮当前是否可见（在屏内）。"""
        node = self.poco(self.SETTING_BTN_DELETE["name"])
        if not node.exists():
            return False
        try:
            return bool(node.attr("visible"))
        except Exception:  # noqa: BLE001 节点失效按不可见处理
            return False

    def click_delete_button(
        self, timeout: float = 15.0, max_swipes: int = 8,
    ) -> None:
        """步骤 3：设置页下滑找到「删除设备」按钮并点击。

        「删除设备」位于设置列表（sv_setting）最底部，进入设置页时
        通常在屏幕外，需逐屏上滑直至按钮可见再点击。

        :param timeout: 等待按钮节点出现的时间（秒）
        :param max_swipes: 最大上滑屏数（防死循环）
        :raises ElementNotFoundError: 按钮未找到/滑到底仍不可见
        """
        if not self.wait_for_element(self.SETTING_BTN_DELETE, timeout=timeout):
            raise ElementNotFoundError(
                f"设置页在 {timeout}s 内未出现「{self.DELETE_BUTTON_TEXT}」按钮"
            )
        for _ in range(max_swipes + 1):
            if self._is_delete_btn_visible():
                self.click(self.SETTING_BTN_DELETE)
                logger.info("设置页：已点击「删除设备」")
                return
            self.swipe_up()
            time.sleep(0.8)
        raise ElementNotFoundError(
            f"设置页滑动 {max_swipes} 屏后「{self.DELETE_BUTTON_TEXT}」仍不可见"
        )

    def confirm_delete_dialog(self, timeout: float = 10.0) -> None:
        """步骤 4：确认删除弹框，点击「删除」。

        弹框内容（真机 dump 2026-10-10）：
        - 标题「温馨提示」（tv_ai_search_title）
        - 描述「确定要删除该设备和子设备及所关联的数据？」（tv_ai_search_des）
        - 按钮「取消」（tv_cancel）/「删除」（tv_confirm）

        :raises ElementNotFoundError: 弹框或确认按钮未出现
        """
        if not self.wait_for_element(self.DIALOG_TITLE, timeout=timeout):
            raise ElementNotFoundError(
                f"点击「删除设备」后 {timeout}s 内未出现确认弹框"
            )
        desc = self.get_text(self.DIALOG_DESC) or ""
        logger.info(f"删除确认弹框：{desc!r}")
        if not self.wait_for_element(self.DIALOG_BTN_CONFIRM, timeout=timeout):
            raise ElementNotFoundError(
                f"确认弹框中「{self.DIALOG_CONFIRM_TEXT}」按钮未出现"
            )
        self.click(self.DIALOG_BTN_CONFIRM)
        logger.info(f"删除确认弹框：已点击「{self.DIALOG_CONFIRM_TEXT}」")

    def assert_device_deleted(
        self, sn: str, timeout: float = 30.0,
    ) -> List[str]:
        """步骤 5：断言 app 自动返回主页且设备列表不含该 SN。

        点「删除」后 app 自动返回主页；主页设备列表需渲染时间，
        在 timeout 内轮询直至列表稳定且不含 SN。

        :param sn: 应已删除的设备 SN
        :return: 删除后的主页设备列表
        :raises ElementNotFoundError: 超时未回主页或列表仍含该 SN
        """
        if not self.main_page.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"点「删除」后 {timeout}s 内未自动返回主页"
            )
        deadline = time.time() + timeout
        last_devices: list = []
        while time.time() < deadline:
            try:
                last_devices = self.main_page.get_device_list()
            except Exception as exc:  # noqa: BLE001 列表渲染中暂不可查
                logger.debug(f"设备列表暂不可查（渲染中）：{exc}")
                last_devices = []
            if sn not in last_devices:
                logger.info(
                    f"主页设备列表断言通过：已无 SN={sn!r}（当前：{last_devices}）"
                )
                return last_devices
            time.sleep(2.0)
        raise ElementNotFoundError(
            f"删除超时：主页设备列表仍含 SN={sn!r}，实际：{last_devices}"
        )

    # ==================== 一站式入口 ====================

    def delete_jingle_device(
        self,
        sn: Optional[str] = None,
        timeout: float = 30.0,
    ) -> List[str]:
        """一站式删除智能门铃 Chime Base：主页点击 SN → 主页断言无 SN。

        完整链路（真机 2026-10-10 验证）：
        1. 主页点击设备 SN（tvJingleNeutralName）→ jingle 首页
        2. 右上角设置按钮（iv_submit）→ 设置页
        3. 下滑找到「删除设备」（btn_delete）→ 点击
        4. 确认弹框点「删除」（tv_confirm）
        5. app 自动返回主页 → 断言设备列表不含 SN

        调用前提：app 已处于登录态主页。

        :param sn: 设备 SN（默认取 `DEFAULT_DEVICE_SN`）
        :param timeout: 各步骤通用超时（秒）
        :return: 删除后的主页设备列表（不含 SN 视为成功）
        :raises ElementNotFoundError: 任一步骤失败时抛出
        """
        sn = sn or self.DEFAULT_DEVICE_SN
        logger.info(f"[JingleDeletePage] 开始一站式删除：SN={sn!r}")

        # 1. 主页点击设备 SN → jingle 首页
        self.open_jingle_home_by_sn(sn, timeout=timeout)
        # 2. 右上角设置 → 设置页
        self.open_setting_page(timeout=timeout)
        # 3. 下滑点「删除设备」
        self.click_delete_button(timeout=timeout)
        # 4. 确认弹框点「删除」
        self.confirm_delete_dialog(timeout=timeout)
        # 5. 等待自动返回主页 + 断言无 SN
        devices = self.assert_device_deleted(sn, timeout=timeout)
        logger.info(f"[JingleDeletePage] 一站式删除完成：主页设备列表 {devices}")
        return devices
