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
    """「连接设备」页面（RouterWiFiActivity 的 BottomSheet 设备列表）。

    页面职责：扫描并展示搜到的 Chime Base 设备列表（SN 数字串），
    用户点击目标 SN 行的整行（行内含 tv_model 文本）即视为「添加」。
    """

    # 真机 dump 提取的资源 id（PAGE 4 dump - RouterWiFiActivity BottomSheet）
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}  # activity title
    IV_CLOSE = {"name": "com.cloudedge.smarteye:id/iv_close"}  # BottomSheet 关闭
    RECYCLER_VIEW = {"name": "com.cloudedge.smarteye:id/recyclerView"}  # 设备列表
    IV_PIC = {"name": "com.cloudedge.smarteye:id/iv_pic"}  # 设备图标
    TV_MODEL = {"name": "com.cloudedge.smarteye:id/tv_model"}  # 设备 SN 文本
    DESIGN_BOTTOM_SHEET = {
        "name": "com.cloudedge.smarteye:id/design_bottom_sheet",
    }  # BottomSheet 容器
    TOUCH_OUTSIDE = {"name": "com.cloudedge.smarteye:id/touch_outside"}  # 外部点击

    EXPECTED_TITLE_KEYWORDS = ("连接设备", "选择设备", "添加设备", "Chime")

    def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
        """等待 BottomSheet 加载完成（recyclerView + design_bottom_sheet 同时出现）。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.exists(self.DESIGN_BOTTOM_SHEET) and self.exists(self.RECYCLER_VIEW):
                logger.debug("Chime 选择设备页 BottomSheet 已加载")
                return True
            time.sleep(0.5)
        logger.warning(f"Chime 选择设备页在 {timeout}s 内未加载")
        return False

    def get_visible_devices(self) -> List[str]:
        """获取当前可见的设备 SN / 型号列表。"""
        if not self.exists(self.RECYCLER_VIEW):
            return []
        result: List[str] = []
        for item in self.poco(**self.RECYCLER_VIEW).children():
            name_node = item.offspring(self.TV_MODEL["name"])
            if name_node.exists():
                text = name_node.attr("text")
                if text:
                    result.append(text)
        return result

    def click_add_button_by_sn(self, sn: str, timeout: float = 30.0) -> None:
        """在设备列表中点击指定 SN 所在行（整行 clickable）。

        :param sn: 设备 SN / 型号
        :raises ElementNotFoundError: 未找到该 SN 时抛出
        """
        if not self.wait_for_page_loaded(timeout=timeout):
            raise ElementNotFoundError(
                f"选择设备页 BottomSheet 在 {timeout}s 内未加载"
            )
        target_item = None
        for item in self.poco(**self.RECYCLER_VIEW).children():
            name_node = item.offspring(self.TV_MODEL["name"])
            if name_node.exists() and name_node.attr("text") == sn:
                target_item = item
                break

        if target_item is None:
            available = self.get_visible_devices()
            raise ElementNotFoundError(
                f"设备列表中未找到 SN={sn!r}（可见：{available}）"
            )
        target_item.click()
        logger.info(f"已点击设备「{sn}」所在行（BottomSheet 整行 clickable）")

    def wait_scanning_finished(self, timeout: float = 60.0) -> bool:
        """等待扫描完成（占位符，BottomSheet 加载即视为完成）。

        实际真机可能无 loading 节点，recyclerView 出现即可。
        """
        return self.wait_for_page_loaded(timeout=timeout)


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

    # 弹框元素（WiFi 信息确认，PAGE 6 待真机 dump 后替换）
    DIALOG_TITLE = {"name": "com.cloudedge.smarteye:id/tv_dialog_title"}
    TV_DIALOG_SSID = {"name": "com.cloudedge.smarteye:id/tv_dialog_ssid"}
    TV_DIALOG_PASSWORD = {"name": "com.cloudedge.smarteye:id/tv_dialog_password"}
    BTN_DETERMINE = {"name": "com.cloudedge.smarteye:id/btn_determine", "text": TEXT_DETERMINE}

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
        """在 SSID 输入框填入 WiFi 名称（清空后输入）。"""
        et = self.poco(**self.WIFI_NAME_ET)
        et.click()
        time.sleep(0.3)
        # 全选 + 删除
        et.set_text("")
        time.sleep(0.3)
        self.input_text(self.WIFI_NAME_ET, ssid, timeout=timeout)
        logger.info(f"已输入 SSID：{ssid!r}")

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

        弹框 resource-id 仍为占位符，需在 PAGE 6 dump 后替换：
        DIALOG_TITLE / TV_DIALOG_SSID / TV_DIALOG_PASSWORD / BTN_DETERMINE

        :param expected_ssid: 期望的 SSID
        :param expected_password: 期望的密码
        :raises ElementNotFoundError: 弹框元素缺失或内容不符
        """
        if not self.wait_for_element(self.DIALOG_TITLE, timeout=timeout):
            raise ElementNotFoundError(
                f"WiFi 信息确认弹框在 {timeout}s 内未出现（resource-id 待 PAGE 6 dump 替换）"
            )

        actual_ssid = self.get_text(self.TV_DIALOG_SSID, timeout=timeout)
        actual_password = self.get_text(self.TV_DIALOG_PASSWORD, timeout=timeout)
        if actual_ssid != expected_ssid:
            raise ElementNotFoundError(
                f"弹框 SSID 不一致：实际={actual_ssid!r}，"
                f"期望={expected_ssid!r}"
            )
        if actual_password != expected_password:
            raise ElementNotFoundError(
                f"弹框密码不一致：实际={actual_password!r}，"
                f"期望={expected_password!r}"
            )
        logger.info(
            f"弹框比对一致：SSID={actual_ssid!r}，password=******"
        )
        self.click(self.BTN_DETERMINE)
        logger.info("已点击弹框「确定」")
