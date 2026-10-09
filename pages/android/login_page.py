"""CloudEdge 安卓端「登录」页面。

页面职责：
1. 维护登录页（LoginActivity）的元素定位器
2. 提供页面级业务方法，与 iOS 端云际「登录」页面保持同名接口
3. 封装登录前的核心交互：选择国家/地区、输入账号密码、记住密码、
   跳转忘记密码、点击登录/注册/微信登录

定位器说明：
- 页面识别点选取「账号输入框 (et_account)」+「密码输入框 (et_password)」，
  两个 resource-id 来自真机 dump（adb shell uiautomator dump），稳定性高，
  且其他页面不会同时出现这两个控件，可唯一判定登录页
- 国家/地区容器 (layout_region) 与区号 (tv_region_code) 通过文本提取，
  支持后续展开国家列表前的断言
"""

from pages.base_page import BasePage, ElementNotFoundError, OperationFailedError
from utils.log_utils import get_logger

logger = get_logger()

# ADBKeyboard（senzhk/ADBKeyBoard）：通过 am broadcast 发送任意字符含中文。
# 设备需先安装 ADBKeyboard.apk 并启用 `com.android.adbkeyboard/.AdbIME`。
ADBKEYBOARD_IME_ID = "com.android.adbkeyboard/.AdbIME"
ADBKEYBOARD_BROADCAST_ACTION = "ADB_INPUT_TEXT"


class CloudEdgeLoginPage(BasePage):
    """CloudEdge「登录」页面（Android）。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点：「账号输入框」+「密码输入框」（真机验证过的 resource-id）
    ET_ACCOUNT = {"name": "com.cloudedge.smarteye:id/et_account"}
    ET_PASSWORD = {"name": "com.cloudedge.smarteye:id/et_password"}

    # 国家/地区选择
    LAYOUT_REGION = {"name": "com.cloudedge.smarteye:id/layout_region"}
    TV_REGION = {"name": "com.cloudedge.smarteye:id/tv_region"}
    TV_REGION_CODE = {"name": "com.cloudedge.smarteye:id/tv_region_code"}
    IV_REGION_ARROW = {"name": "com.cloudedge.smarteye:id/iv_arrow"}

    # 记住密码 / 忘记密码 / 登录
    CB_REMEMBER_PASSWORD = {"name": "com.cloudedge.smarteye:id/checkbox_pwd"}
    TV_FORGOT_PASSWORD = {"name": "com.cloudedge.smarteye:id/tv_forget_password"}
    BTN_LOGIN = {"name": "com.cloudedge.smarteye:id/tv_login"}

    # 第三方登录 / 注册入口
    BTN_WECHAT_LOGIN = {"name": "com.cloudedge.smarteye:id/iv_wechart"}
    BTN_REGISTER = {"name": "com.cloudedge.smarteye:id/tv_register"}

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: AndroidUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="android")

    # ---------------- 页面识别 ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「登录」页面加载完成（以「账号」+「密码」输入框同时出现为识别点）。

        轮询检查两个识别点是否同时可见，避免仅出现单一元素时误判。

        :param timeout: 等待超时时间（秒）
        :return: 登录页面加载完成返回 True
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_login_page():
                logger.debug(f"「登录」页面识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"「登录」页面识别点在 {timeout}s 内未同时出现："
            f"ET_ACCOUNT={self.exists(self.ET_ACCOUNT)}，"
            f"ET_PASSWORD={self.exists(self.ET_PASSWORD)}"
        )
        return False

    def is_login_page(self) -> bool:
        """判断当前是否处于「登录」页面（两个识别点同时存在）。

        :return: 「账号」与「密码」输入框同时存在返回 True
        """
        return self.exists(self.ET_ACCOUNT) and self.exists(self.ET_PASSWORD)

    # ---------------- 业务方法（与 iOS 端同名同义） ----------------

    def get_region(self) -> str:
        """获取当前选中的国家/地区名称。

        :return: 当前国家/地区文本（如「中国」），未渲染时返回空串
        """
        if not self.exists(self.TV_REGION):
            return ""
        return self.get_text(self.TV_REGION)

    def get_region_code(self) -> str:
        """获取当前选中的国家区号。

        :return: 当前区号文本（如「+86」），未渲染时返回空串
        """
        if not self.exists(self.TV_REGION_CODE):
            return ""
        return self.get_text(self.TV_REGION_CODE)

    def open_region_picker(self) -> None:
        """点击国家/地区容器，展开国家列表（具体列表项在后续页面处理）。"""
        self.click(self.LAYOUT_REGION)

    def input_account(self, account: str) -> None:
        """在「账号」输入框中输入内容。

        :param account: 待输入的账号文本
        """
        self.input_text(self.ET_ACCOUNT, account)

    def input_password(self, password: str) -> None:
        """在「密码」输入框中输入内容（密码框会以掩码显示）。

        :param password: 待输入的密码文本
        """
        self.input_text(self.ET_PASSWORD, password)

    def is_remember_password_checked(self) -> bool:
        """判断「记住密码」复选框当前是否已勾选。

        :return: 已勾选返回 True
        """
        if not self.exists(self.CB_REMEMBER_PASSWORD):
            return False
        element = self.find(self.CB_REMEMBER_PASSWORD)
        return bool(element.attr("checked"))

    def set_remember_password(self, checked: bool = True) -> None:
        """设置「记住密码」复选框的勾选状态。

        :param checked: True 表示勾选，False 表示取消勾选；当前状态与目标一致时跳过
        """
        if self.is_remember_password_checked() == checked:
            logger.debug(f"「记住密码」当前已是目标状态 checked={checked}，无需操作")
            return
        self.click(self.CB_REMEMBER_PASSWORD)
        logger.info(f"「记住密码」状态已切换为 checked={checked}")

    def click_forgot_password(self) -> None:
        """点击「忘记密码」入口。"""
        self.click(self.TV_FORGOT_PASSWORD)

    def click_login(self) -> None:
        """点击「登录」按钮。"""
        self.click(self.BTN_LOGIN)

    def click_wechat_login(self) -> None:
        """点击微信登录图标。"""
        self.click(self.BTN_WECHAT_LOGIN)

    def click_register(self) -> None:
        """点击「立即注册」入口。"""
        self.click(self.BTN_REGISTER)

    # ---------------- 组合业务方法 ----------------

    def login(self, account: str, password: str,
              remember_password: bool = True) -> None:
        """一站式登录：设置记住密码 → 输入账号 → 输入密码 → 点击登录。

        :param account: 账号文本
        :param password: 密码文本
        :param remember_password: 是否勾选记住密码，默认 True
        """
        self.set_remember_password(remember_password)
        self.input_account(account)
        self.input_password(password)
        self.click_login()
        logger.info(f"已提交登录：account=[{account}]，remember_password={remember_password}")

    # ==================== 国家/地区选择（ADBKeyboard 方案） ====================

    # 国家搜索输入框（进入国家选择页后可见）
    ET_REGION_SEARCH = {"name": "com.cloudedge.smarteye:id/et_region_search"}
    # 国家列表项（resource-id + 文本双定位，避免与重名国家混淆）
    TV_CITY = {"name": "com.cloudedge.smarteye:id/tv_city"}

    # ---------------- 内部工具：通过 adb 操作输入法 ----------------

    def _adb_get_current_ime(self) -> str:
        """获取设备当前默认输入法 ID（如 `com.android.adbkeyboard/.AdbIME`）。

        :return: 当前 IME ID；获取失败返回空字符串
        """
        if not self.udid:
            return ""
        args = ["adb", "-s", self.udid, "shell",
                "settings", "get", "secure", "default_input_method"]
        try:
            return self._run_device_command(args, timeout=5).strip()
        except OperationFailedError as exc:
            logger.warning(f"获取当前 IME 失败：{exc}")
            return ""

    def _adb_set_ime(self, ime_id: str) -> None:
        """将设备默认输入法切换为指定 IME。

        :param ime_id: 目标 IME ID，如 `com.android.adbkeyboard/.AdbIME`
        :raises OperationFailedError: 切换失败时抛出
        """
        args = ["adb", "-s", self.udid, "shell", "ime", "set", ime_id]
        self._run_device_command(args, timeout=5)
        logger.info(f"已切换输入法：[{ime_id}]")

    def _adb_broadcast_text(self, text: str) -> None:
        """通过 ADBKeyboard 广播向当前焦点 EditText 发送文本。

        命令：adb shell am broadcast -a ADB_INPUT_TEXT --es msg "..."
        支持任意字符（含中文、emoji、特殊符号），不依赖系统 IME 是否支持。

        :param text: 待发送文本
        :raises OperationFailedError: 广播失败时抛出
        """
        args = ["adb", "-s", self.udid, "shell",
                "am", "broadcast", "-a", ADBKEYBOARD_BROADCAST_ACTION,
                "--es", "msg", text]
        self._run_device_command(args, timeout=10)
        logger.info(f"ADBKeyboard 已发送：[{text}]")

    # ---------------- 业务方法 ----------------

    def search_region_via_adb_keyboard(self, china_text: str) -> None:
        """在国家/地区搜索框中通过 ADBKeyboard 输入**中文**关键词并触发过滤。

        流程：
        1. 切换输入法到 ADBKeyboard（保存原 IME 用于还原）
        2. 点击搜索框获取焦点
        3. 通过 am broadcast 发送中文文本
        4. 还原原输入法（避免后续真实输入仍走 ADBKeyboard）

        前置条件：
        - 设备已安装并启用 `com.android.adbkeyboard/.AdbIME`
        - 当前已处于国家/地区选择页（`et_region_search` 可见）

        :param china_text: 中文国家名，如「美国」「日本」
        :raises OperationFailedError: 切换输入法或广播失败时抛出
        :raises ElementNotFoundError: 搜索框未出现时抛出
        """
        if not self.udid:
            raise OperationFailedError(
                "ADBKeyboard 输入依赖设备 udid，请在 BasePage 构造时传入"
            )

        import time

        original_ime = self._adb_get_current_ime()
        logger.debug(f"当前 IME：[{original_ime}]")

        try:
            if original_ime != ADBKEYBOARD_IME_ID:
                self._adb_set_ime(ADBKEYBOARD_IME_ID)
                time.sleep(0.3)

            self.click(self.ET_REGION_SEARCH)
            time.sleep(0.3)
            self._adb_broadcast_text(china_text)
            time.sleep(0.8)
        finally:
            if original_ime and original_ime != ADBKEYBOARD_IME_ID:
                self._adb_set_ime(original_ime)
                logger.debug(f"已还原输入法：[{original_ime}]")

    def select_region(self, china_text: str) -> None:
        """在过滤后的国家列表中点击目标国家项，并等待返回登录页。

        列表项定位：`tv_city`（resource-id）+ `text=china_text` 双条件，
        避免误点到重名项（如「美国」与「美属维尔京群岛」）。

        :param china_text: 中文国家名
        :raises ElementNotFoundError: 目标项未出现或点击后未返回登录页时抛出
        """
        import time

        self.click({**self.TV_CITY, "text": china_text})
        time.sleep(0.5)

        if not self.wait_for_page_loaded(timeout=10):
            raise ElementNotFoundError(
                f"点击「{china_text}」后未返回登录页（et_account / et_password 未出现）"
            )
        logger.info(f"已选择国家「{china_text}」并返回登录页")

    # ---------------- 登录前弹窗处理 ----------------

    def handle_login_popups(self, max_attempts: int = 3) -> bool:
        """处理登录页前置弹窗（MIUI 自动填充等系统级遮挡）。

        当前实现策略：若「账号+密码」识别点尚未同时出现，
        尝试按下系统返回键关闭系统级弹窗，再次检测识别点；
        最多循环 max_attempts 次。

        :param max_attempts: 最大尝试次数
        :return: 任意一次识别点出现即返回 True
        """
        import time

        for attempt in range(1, max_attempts + 1):
            if self.is_login_page():
                return True
            logger.debug(
                f"[handle_login_popups] 第 {attempt}/{max_attempts} 次尝试："
                "账号/密码识别点尚未出现，按 BACK 关闭系统级弹窗"
            )
            self.press_back()
            time.sleep(0.6)

        return self.is_login_page()

    # ---------------- 一站式入口 ----------------

    def login_with_region(self, region_text: str, account: str, password: str,
                          remember_password: bool = True) -> None:
        """一站式：选择国家 → 输入账号密码 → 勾选记住密码 → 点击登录。

        完整流程：
        1. 点击国家/地区容器进入选择页
        2. 通过 ADBKeyboard 输入中文国家名并过滤列表
        3. 点击搜索结果中的目标国家项，回到登录页
        4. 勾选记住密码（若未勾选）
        5. 输入账号与密码
        6. 点击登录按钮

        :param region_text: 中文国家名，如「美国」
        :param account: 账号
        :param password: 密码
        :param remember_password: 是否勾选记住密码（默认 True）
        """
        import time

        # 先处理登录页前置弹窗（如 MIUI 自动填充选择器）
        self.handle_login_popups()

        if not self.wait_for_page_loaded(timeout=15):
            raise ElementNotFoundError(
                "当前未处于登录页，无法执行 login_with_region"
            )

        logger.info("[1/6] 点击国家/地区容器，进入选择页")
        self.open_region_picker()
        time.sleep(2.0)

        logger.info(f"[2/6] ADBKeyboard 输入「{region_text}」并过滤列表")
        self.search_region_via_adb_keyboard(region_text)

        logger.info(f"[3/6] 点击搜索结果中的「{region_text}」，返回登录页")
        self.select_region(region_text)

        logger.info("[4/6] 勾选记住密码（若未勾选）")
        self.set_remember_password(remember_password)

        logger.info("[5/6] 输入账号与密码")
        self.input_account(account)
        self.input_password(password)

        logger.info("[6/6] 点击登录按钮")
        self.click_login()
        logger.info(
            f"已提交登录：region=[{region_text}]，account=[{account}]，"
            f"remember_password={remember_password}"
        )