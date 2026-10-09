"""Chime Base 添加流程 — 设备配对阶段 PO。

包含 2 个页面：
1. `ChimeSelectDevicePage` — 「连接设备」页面（搜到的设备列表）
2. `ChimeWifiConfigPage` — 「无线连接」页面（输 SSID + 密码 + 弹框确认）

定位器为占位符，真机 poco dump 后需替换。
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


TEXT_NEXT = "下一步"
TEXT_DETERMINE = "确定"


class ChimeSelectDevicePage(BasePage):
    """「连接设备」页面（BleSearchDeviceActivity 整页设备列表）。

    页面职责：蓝牙扫描附近的 Chime Base 设备并展示 SN 列表，
    点击目标 SN 行右侧的「添加」按钮（`tv_next`）。

    真机验证（2026-10-09）：步骤 2「接入电源」点「下一步」后直接进入
    本页（非 BottomSheet）。
    """

    # 真机 dump 提取的资源 id（BleSearchDeviceActivity）
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # '连接设备'
    TV_SEARCHING = {"name": "com.cloudedge.smarteye:id/tv1"}  # '搜索附近的设备...'
    TV_TIP = {"name": "com.cloudedge.smarteye:id/tv_tip"}  # '搜索到的设备'
    TV_DEVICE_NAME = {"name": "com.cloudedge.smarteye:id/tv_device_name"}  # 设备 SN
    TV_TIME = {"name": "com.cloudedge.smarteye:id/tv_time"}  # 倒计时
    TV_ADD = {"name": "com.cloudedge.smarteye:id/tv_next"}  # 行右侧「添加」按钮

    EXPECTED_TITLE_KEYWORDS = ("连接设备", "选择设备", "添加设备", "Chime")

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待页面加载完成（标题含「连接设备」+ 至少一个 SN 出现）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TITLE):
                title = self.get_text(self.TV_TITLE)
                if any(kw in title for kw in self.EXPECTED_TITLE_KEYWORDS):
                    logger.debug(f"Chime 选择设备页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 选择设备页在 {timeout}s 内未加载")
        return False

    def get_visible_devices(self) -> List[str]:
        """获取当前可见的设备 SN 列表。"""
        result: List[str] = []
        for node in self.poco(self.TV_DEVICE_NAME["name"]):
            text = node.attr("text")
            if text:
                result.append(text)
        return result

    def click_add_button_by_sn(self, sn: str, timeout: float = 30.0) -> None:
        """在设备列表中点击指定 SN 行右侧的「添加」按钮。

        :param sn: 设备 SN
        :raises ElementNotFoundError: 未找到该 SN 或该行无「添加」按钮
        """
        if not self.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"选择设备页在 {timeout}s 内未加载（Chime Base 是否处于配对态？）"
            )
        target_row = None
        for node in self.poco(self.TV_DEVICE_NAME["name"]):
            if node.attr("text") == sn:
                target_row = node.parent()
                break

        if target_row is None:
            available = self.get_visible_devices()
            raise ElementNotFoundError(
                f"设备列表中未找到 SN={sn!r}（可见：{available}）；"
                f"请确认 Chime Base 已上电并处于配对态"
            )
        add_btn = target_row.offspring(self.TV_ADD["name"])
        if not add_btn.exists():
            raise ElementNotFoundError(
                f"SN={sn!r} 所在行未找到「添加」按钮（tv_next）"
            )
        add_btn.click()
        logger.info(f"已点击设备「{sn}」行右侧的「添加」按钮")

    def wait_scanning_finished(self, timeout: float = 60.0) -> bool:
        """等待扫描出至少一台设备（tv_device_name 出现即视为完成）。"""
        return self.wait_for_element(self.TV_DEVICE_NAME, timeout=timeout)


class ChimeWifiConfigPage(BasePage):
    """「无线连接」页面（AddDeviceGetWifiListActivity）。

    页面职责：选择/输入 WiFi 名称与密码，确认后点击「下一步」。
    真实 PAGE 5 dump 资源 id 已替换。
    """

    # 真机 dump 提取的资源 id（PAGE 5 dump）
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    TV_TOP_TITLE = {"name": "com.cloudedge.smarteye:id/tv_top_title"}  # "无线连接"
    TV_ALERT = {"name": "com.cloudedge.smarteye:id/tv_alert"}  # 提示语
    RL_WIFI_NAME = {"name": "com.cloudedge.smarteye:id/rl_wifi_name"}  # WiFi 名容器
    WIFI_NAME_ET = {"name": "com.cloudedge.smarteye:id/wifi_name_et"}  # SSID 输入框
    TV_CHANGE_WIFI = {"name": "com.cloudedge.smarteye:id/tv_change_wifi"}  # 切换 WiFi
    LL_WIFI_LIST = {"name": "com.cloudedge.smarteye:id/ll_wifi_list"}  # WiFi 列表容器
    RV_WIFI_LIST = {"name": "com.cloudedge.smarteye:id/rv_wifi_list"}  # WiFi 列表
    TV_WIFI_NAME = {"name": "com.cloudedge.smarteye:id/tv_wifi_name"}  # 列表中 WiFi 名
    PWD_ET = {"name": "com.cloudedge.smarteye:id/pwd_et"}  # 密码输入框
    TV_PWD_CHK = {"name": "com.cloudedge.smarteye:id/tv_pwd_chk"}  # 显示/隐藏密码
    TV_TIP = {"name": "com.cloudedge.smarteye:id/tv_tip"}  # 提示
    IV_SUBMIT = {"name": "com.cloudedge.smarteye:id/iv_submit"}  # 提交
    IV_BACK = {"name": "com.cloudedge.smarteye:id/iv_back"}
    LAYOUT_NEXT = {"name": "com.cloudedge.smarteye:id/layout_next"}
    TV_NEXT = {"name": "com.cloudedge.smarteye:id/tv_next", "text": TEXT_NEXT}

    EXPECTED_TOP_TITLE_KEYWORDS = ("无线连接", "WiFi", "wifi", "配网")

    # 弹框元素（WiFi 信息确认，真机 PAGE 6 dump 已验证）
    DIALOG_TITLE = {"name": "com.cloudedge.smarteye:id/title"}  # '提示'
    DIALOG_MESSAGE = {"name": "com.cloudedge.smarteye:id/message"}  # 含 SSID+密码 的比对文本
    BTN_CANCEL = {"name": "com.cloudedge.smarteye:id/negativeButton", "text": "取消"}
    BTN_DETERMINE = {"name": "com.cloudedge.smarteye:id/positiveButton", "text": TEXT_DETERMINE}

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待页面加载完成（tv_top_title 含「无线连接」 + rv_wifi_list 出现）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.TV_TOP_TITLE) and self.exists(self.RV_WIFI_LIST):
                title = self.get_text(self.TV_TOP_TITLE)
                if any(kw in title for kw in self.EXPECTED_TOP_TITLE_KEYWORDS):
                    logger.debug(f"Chime 无线连接页已加载：{title!r}")
                    return True
            time.sleep(0.5)
        logger.warning(f"Chime 无线连接页在 {timeout}s 内未加载")
        return False

    def wait_wifi_search_finished(self, timeout: float = 30.0) -> bool:
        """等待 WiFi 列表渲染完成。

        按用户确认：**忽略「WiFi 搜索中」等提示文案**（真机 PAGE 5 dump
        也未发现该文案），直接以 `rv_wifi_list` 渲染出现为准。
        WiFi 2.4G / 5G 均支持，不按频段过滤。
        """
        return self.wait_for_element(self.RV_WIFI_LIST, timeout=timeout)

    def select_wifi(self, ssid: str, timeout: float = 15.0) -> bool:
        """在 WiFi 列表中点击目标 SSID。

        :param ssid: WiFi SSID
        :return: True=找到并点击，False=未找到
        """
        if not self.wait_for_page_loaded(timeout=timeout):
            return False
        for item in self.poco(**self.RV_WIFI_LIST).children():
            name_node = item.offspring(self.TV_WIFI_NAME["name"])
            if name_node.exists() and name_node.attr("text") == ssid:
                item.click()
                logger.info(f"已选择 WiFi：{ssid!r}")
                return True
        return False

    def input_ssid(self, ssid: str, timeout: float = 10.0) -> None:
        """在 SSID 输入框填入 WiFi 名称（清空后输入）。

        注意（真机验证）：输入后 `attr("text")` 可能短暂返回旧值，
        校验在 `collapse_wifi_list()` 之后由弹框比对兜底。
        """
        et = self.poco(**self.WIFI_NAME_ET)
        et.click()
        time.sleep(0.5)
        et.set_text("")
        time.sleep(0.5)
        et.set_text(ssid)
        time.sleep(1.0)
        logger.info(f"已输入 SSID：{ssid!r}")

    def collapse_wifi_list(self, timeout: float = 10.0) -> None:
        """点击 SSID 输入框最右侧的箭头（tv_change_wifi）收起 WiFi 列表。

        真机验证：WiFi 列表会把密码输入框（pwd_et）盖住，必须先点该箭头
        收起列表，密码框才会渲染出来。
        """
        if not self.wait_for_element(self.TV_CHANGE_WIFI, timeout=timeout):
            raise ElementNotFoundError("SSID 输入框右侧箭头（tv_change_wifi）未出现")
        self.click(self.TV_CHANGE_WIFI)
        # 等密码框出现（收起列表的标志）
        if not self.wait_for_element(self.PWD_ET, timeout=timeout):
            raise ElementNotFoundError(
                "点击箭头收起列表后，密码输入框（pwd_et）仍未出现"
            )
        logger.info("已点击箭头收起 WiFi 列表，密码输入框已露出")

    def input_password(self, password: str, timeout: float = 10.0) -> None:
        """在密码输入框填入 WiFi 密码。"""
        self.input_text(self.PWD_ET, password, timeout=timeout)
        logger.info("已输入 WiFi 密码（长度={}）".format(len(password)))

    def click_next(self) -> None:
        """点击「下一步」（触发弹框或跳转）。"""
        self.click(self.TV_NEXT)
        logger.info("无线连接页：已点击「下一步」")

    def assert_and_confirm_popup(
        self,
        expected_ssid: str,
        expected_password: str,
        timeout: float = 15.0,
    ) -> None:
        """等待 WiFi 信息确认弹框出现，比对后点「确定」。

        真机验证（2026-10-09）：弹框为 title='提示' + message 合并文本，格式：
            '请再次确认您的WIFI账号和密码是否正确！\\nWIFI名称：xxx\\nWIFI密码：yyy'
        从 message 解析「WIFI名称：」「WIFI密码：」后与期望值比对。

        :param expected_ssid: 期望的 SSID
        :param expected_password: 期望的密码
        :raises ElementNotFoundError: 弹框元素缺失或内容不符
        """
        if not self.wait_for_element(self.DIALOG_MESSAGE, timeout=timeout):
            raise ElementNotFoundError(
                f"WiFi 信息确认弹框在 {timeout}s 内未出现"
            )

        message = self.get_text(self.DIALOG_MESSAGE, timeout=timeout)
        actual_ssid = self._parse_field(message, "WIFI名称：")
        actual_password = self._parse_field(message, "WIFI密码：")
        if actual_ssid != expected_ssid:
            raise ElementNotFoundError(
                f"弹框 SSID 不一致：实际={actual_ssid!r}，"
                f"期望={expected_ssid!r}（message={message!r}）"
            )
        if actual_password != expected_password:
            raise ElementNotFoundError(
                f"弹框密码不一致：实际={actual_password!r}，"
                f"期望={expected_password!r}（message={message!r}）"
            )
        logger.info(
            f"弹框比对一致：SSID={actual_ssid!r}，password=******"
        )
        self.click(self.BTN_DETERMINE)
        logger.info("已点击弹框「确定」")

    @staticmethod
    def _parse_field(message: str, prefix: str) -> str:
        """从弹框 message 中解析「WIFI名称：xxx」「WIFI密码：yyy」字段。"""
        idx = message.find(prefix)
        if idx < 0:
            return ""
        rest = message[idx + len(prefix):]
        # 截到下一个换行或结尾
        end = rest.find("\n")
        return rest if end < 0 else rest[:end]
