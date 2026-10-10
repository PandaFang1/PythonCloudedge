"""PO 模式页面基类。

职责：
1. 封装基于 poco 的基础元素操作：查找、等待、点击、输入、滑动等
2. 封装 app 生命周期控制：启动、关闭、重启（实现层）
3. 所有页面类均继承本基类，仅持有 poco 驱动，不关心驱动创建细节

执行时机说明：
    app 的打开/关闭/重启由 testcases/conftest.py 中的 fixture 调用本类方法控制，
    测试用例只负责业务操作。
"""

import re
import subprocess
from typing import Optional

from utils.log_utils import get_logger

logger = get_logger()

# 默认元素等待时间（秒）
DEFAULT_TIMEOUT = 10


class PageError(Exception):
    """页面操作异常基类。"""

    pass


class ElementNotFoundError(PageError):
    """元素未找到 / 等待超时异常。"""

    pass


class OperationFailedError(PageError):
    """元素操作（点击/输入等）失败异常。"""

    pass


class BasePage:
    """PO 模式页面基类，封装基础元素操作与 app 生命周期控制。

    所有页面类继承本类，通过构造函数注入 poco 驱动，
    页面子类只需定义各自的元素定位（locator）与业务方法。

    门控方法：
        :meth:`dump_hierarchy` 是项目唯一的 UI 层级树抓取收口，
        调用时 **必须** 传入非空 ``reason``。项目约定「没有确定
        要求，不使用本方法」——任何 inline 调用 ``poco.agent.
        hierarchy.dump()`` 都被视为绕过门控，应重构为调用本方法。
    """

    def __init__(self, poco, udid: str = "", platform: str = "android"):
        """
        :param poco: poco 驱动实例（AndroidUiautomationPoco / IOSUiautomationPoco 等）
        :param udid: 设备 UDID，用于 app 启动/关闭的底层命令（adb / xcrun）
        :param platform: 平台（android / ios，忽略大小写），用于选择 app 控制命令
        """
        self.poco = poco
        self.udid = udid
        self.platform = platform.lower()

    # ==================== app 生命周期控制 ====================

    def _run_device_command(self, args: list, timeout: float = 15.0) -> str:
        """执行设备控制命令（adb / xcrun）并返回标准输出。

        :param args: 完整命令参数列表，如 ["adb", "-s", udid, "shell", "..."]
        :param timeout: 命令超时时间（秒）
        :return: 命令标准输出
        :raises OperationFailedError: 命令执行失败或超时时抛出
        """
        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"设备命令执行超时（>{timeout}s）：{' '.join(args)}"
            logger.error(msg)
            raise OperationFailedError(msg) from exc

        if result.returncode != 0:
            msg = (f"设备命令执行失败 [{result.returncode}]：{' '.join(args)}，"
                   f"stderr：{result.stderr.strip()}")
            logger.error(msg)
            raise OperationFailedError(msg)
        return result.stdout

    def start_app(self, package_name: str) -> None:
        """启动指定 app。

        Android：adb shell monkey 拉起 LAUNCHER
        iOS：xcrun devicectl 启动指定 Bundle ID

        :param package_name: Android 包名或 iOS Bundle ID
        :raises OperationFailedError: 启动失败时抛出
        """
        if self.platform == "android":
            adb_args = ["adb"]
            if self.udid:
                adb_args += ["-s", self.udid]
            adb_args += [
                "shell", "monkey", "-p", package_name,
                "-c", "android.intent.category.LAUNCHER", "1",
            ]
            self._run_device_command(adb_args)
        else:
            self._run_device_command(
                ["xcrun", "devicectl", "device", "process", "launch",
                 "--device", self.udid, package_name]
            )
        logger.info(f"app 已启动：[{package_name}]（platform={self.platform}）")

    def _find_ios_pid(self, processes_output: str, package_name: str) -> str:
        """从 devicectl 进程列表输出中查找指定 app 的 PID。

        devicectl terminate 只支持 --pid，不支持 Bundle ID，
        因此需先按包名关键字匹配进程行（如 com.meari.smartcamera 匹配
        /.../Meari.app/Meari），再提取 PID。

        :param processes_output: `devicectl device info processes` 的输出
        :param package_name: iOS Bundle ID
        :return: 进程 PID 字符串
        :raises OperationFailedError: 未找到对应进程时抛出（app 可能未运行）
        """
        # 提取包名中的有效关键字（排除 com/org/net/io 等通用前缀）
        keywords = [part for part in package_name.lower().split(".")
                    if len(part) > 2 and part not in ("com", "org", "net", "io", "cn")]
        if not keywords:
            keywords = [package_name.lower()]

        for line in processes_output.splitlines():
            # 进程行格式：PID   /private/var/.../Xxx.app/Xxx（行尾可能有多余空格，需 strip）
            matched = re.match(r"^\s*(\d+)\s+(\S+)$", line.strip())
            if not matched:
                continue
            pid, exec_path = matched.groups()
            if any(keyword in exec_path.lower() for keyword in keywords):
                logger.debug(f"已定位 iOS 进程：PID={pid}，{exec_path}")
                return pid

        msg = f"iOS 进程列表中未找到 app [{package_name}] 的进程（可能未运行）"
        logger.error(msg)
        raise OperationFailedError(msg)

    def stop_app(self, package_name: str) -> None:
        """关闭指定 app。

        :param package_name: Android 包名或 iOS Bundle ID
        :raises OperationFailedError: 关闭失败时抛出
        """
        if self.platform == "android":
            adb_args = ["adb"]
            if self.udid:
                adb_args += ["-s", self.udid]
            adb_args += ["shell", "am", "force-stop", package_name]
            self._run_device_command(adb_args)
        else:
            # devicectl terminate 仅支持 --pid，需先查询进程列表定位 PID
            processes = self._run_device_command(
                ["xcrun", "devicectl", "device", "info", "processes",
                 "--device", self.udid]
            )
            try:
                pid = self._find_ios_pid(processes, package_name)
            except OperationFailedError:
                # 进程不存在视为已停止（幂等，与 am force-stop 行为对齐）
                logger.info(f"app [{package_name}] 未在运行，视为已关闭")
                return
            self._run_device_command(
                ["xcrun", "devicectl", "device", "process", "terminate",
                 "--device", self.udid, "--pid", pid]
            )
        logger.info(f"app 已关闭：[{package_name}]")

    def restart_app(self, package_name: str, wait_seconds: float = 3.0) -> None:
        """重启指定 app（先关闭再启动）。

        :param package_name: Android 包名或 iOS Bundle ID
        :param wait_seconds: 关闭后等待时间（秒），确保进程完全退出
        """
        import time

        logger.info(f"开始重启 app：[{package_name}] ...")
        self.stop_app(package_name)
        time.sleep(wait_seconds)
        self.start_app(package_name)
        logger.info(f"app 重启完成：[{package_name}]")

    # ==================== 基础元素操作 ====================

    def _resolve_locator(self, locator):
        """将定位器解析为 poco UI 对象。

        poco 的选择器 API 要求属性以关键字参数传入（如 poco(text="登录")），
        不支持 poco({"text": "登录"}) 的 dict 传参，因此此处统一转换。

        :param locator: 元素定位器（str 名称或 dict，如 {"text": "登录"}、
                        {"name": "com.xxx:id/btn"}）
        :return: UIObjectProxy 元素对象
        """
        if isinstance(locator, dict):
            return self.poco(**locator)
        return self.poco(locator)

    def find(self, locator, timeout: Optional[float] = None):
        """查找元素并返回 poco UI 对象。

        :param locator: 元素定位器（str 名称或 dict，如 {"text": "登录"}）
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :return: UIObjectProxy 元素对象
        :raises ElementNotFoundError: 元素超时未出现时抛出
        """
        timeout = timeout or DEFAULT_TIMEOUT
        element = self._resolve_locator(locator)

        if not element.wait(timeout=timeout):
            msg = f"元素 [{locator}] 在 {timeout}s 内未出现"
            logger.error(msg)
            raise ElementNotFoundError(msg)

        logger.debug(f"元素已找到：[{locator}]")
        return element

    def exists(self, locator) -> bool:
        """判断元素当前是否存在（不等待）。

        :param locator: 元素定位器
        :return: 存在返回 True
        """
        return self._resolve_locator(locator).exists()

    def wait_for_element(self, locator, timeout: Optional[float] = None) -> bool:
        """等待元素出现。

        :param locator: 元素定位器
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :return: 超时时间内出现返回 True，否则 False（不抛异常）
        """
        timeout = timeout or DEFAULT_TIMEOUT
        result = self._resolve_locator(locator).wait(timeout=timeout)
        if result:
            logger.debug(f"元素 [{locator}] 已出现（等待 <= {timeout}s）")
        else:
            logger.warning(f"元素 [{locator}] 在 {timeout}s 内未出现")
        return result

    def wait_for_element_disappear(self, locator, timeout: Optional[float] = None) -> bool:
        """等待元素消失。

        :param locator: 元素定位器
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :return: 超时时间内消失返回 True，否则 False
        """
        import time

        timeout = timeout or DEFAULT_TIMEOUT
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.exists(locator):
                logger.debug(f"元素 [{locator}] 已消失（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(f"元素 [{locator}] 在 {timeout}s 内未消失")
        return False

    def click(self, locator, timeout: Optional[float] = None) -> None:
        """等待元素出现并点击。

        :param locator: 元素定位器
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :raises ElementNotFoundError: 元素超时未出现时抛出
        :raises OperationFailedError: 点击失败时抛出
        """
        element = self.find(locator, timeout=timeout)
        try:
            element.click()
        except Exception as exc:
            msg = f"元素 [{locator}] 点击失败：{exc}"
            logger.error(msg)
            raise OperationFailedError(msg) from exc
        logger.debug(f"元素已点击：[{locator}]")

    def click_if_exists(self, locator) -> bool:
        """元素存在则点击（常用于弹窗处理），不存在则跳过。

        :param locator: 元素定位器
        :return: 实际执行了点击返回 True
        """
        if self.exists(locator):
            self.click(locator)
            logger.debug(f"元素存在，已点击：[{locator}]")
            return True
        logger.debug(f"元素不存在，跳过点击：[{locator}]")
        return False

    def input_text(self, locator, text: str, timeout: Optional[float] = None) -> None:
        """点击元素并输入文本。

        :param locator: 元素定位器
        :param text: 待输入文本
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :raises OperationFailedError: 输入失败时抛出
        """
        element = self.find(locator, timeout=timeout)
        try:
            element.click()
            element.set_text(text)
        except Exception as exc:
            msg = f"元素 [{locator}] 输入 [{text}] 失败：{exc}"
            logger.error(msg)
            raise OperationFailedError(msg) from exc
        logger.debug(f"元素已输入：[{locator}] <- [{text}]")

    def get_text(self, locator, timeout: Optional[float] = None) -> str:
        """获取元素文本。

        :param locator: 元素定位器
        :param timeout: 等待超时时间（秒），默认 DEFAULT_TIMEOUT
        :return: 元素文本内容
        """
        element = self.find(locator, timeout=timeout)
        return element.attr("text") or ""

    # ==================== 滑动操作 ====================

    def swipe_up(self, duration: float = 0.5) -> None:
        """向上滑动一屏。

        :param duration: 滑动持续时间（秒）
        """
        self.poco.swipe([0.5, 0.7], [0.5, 0.3], duration=duration)
        logger.debug("已向上滑动")

    def swipe_down(self, duration: float = 0.5) -> None:
        """向下滑动一屏。

        :param duration: 滑动持续时间（秒）
        """
        self.poco.swipe([0.5, 0.3], [0.5, 0.7], duration=duration)
        logger.debug("已向下滑动")

    def swipe_left(self, duration: float = 0.5) -> None:
        """向左滑动一屏。

        :param duration: 滑动持续时间（秒）
        """
        self.poco.swipe([0.8, 0.5], [0.2, 0.5], duration=duration)
        logger.debug("已向左滑动")

    def swipe_right(self, duration: float = 0.5) -> None:
        """向右滑动一屏。

        :param duration: 滑动持续时间（秒）
        """
        self.poco.swipe([0.2, 0.5], [0.8, 0.5], duration=duration)
        logger.debug("已向右滑动")

    # ==================== 系统按键 ====================

    def press_back(self) -> None:
        """按下系统返回键（KEYCODE_BACK = 4）。

        通过 adb shell input keyevent 实现，不依赖 poco 屏幕快照，
        适合处理 MIUI 自动填充等系统级弹窗。
        """
        if self.platform == "android":
            args = ["adb"]
            if self.udid:
                args += ["-s", self.udid]
            args += ["shell", "input", "keyevent", "4"]
            self._run_device_command(args, timeout=5)
        else:
            # iOS 端没有全局 BACK 键，由各页面单独实现 dismiss 逻辑
            logger.debug("iOS 端无系统返回键，请使用页面级 dismiss 方法")
        logger.debug("已按下系统返回键")

    def get_current_activity(self) -> str:
        """获取设备当前前台 Activity 全名（Android 专用）。

        通过 `dumpsys activity activities | grep topResumedActivity` 解析，
        返回形如 `com.pkg/.MainActivity` 的字符串。

        :return: Activity 全名；获取失败返回空字符串
        """
        if self.platform != "android":
            logger.debug("get_current_activity 仅支持 Android")
            return ""

        import re

        args = ["adb"]
        if self.udid:
            args += ["-s", self.udid]
        args += ["shell", "dumpsys", "activity", "activities"]
        try:
            output = self._run_device_command(args, timeout=10)
        except OperationFailedError as exc:
            logger.warning(f"获取当前 Activity 失败：{exc}")
            return ""

        matched = re.search(r"topResumedActivity=ActivityRecord\{\w+ \w+ (\S+)", output)
        if matched:
            activity = matched.group(1)
            logger.debug(f"当前前台 Activity：{activity}")
            return activity
        logger.warning(f"topResumedActivity 未匹配到，原始输出片段：{output[:200]}")
        return ""

    # ==================== 调试辅助（门控） ====================

    def dump_hierarchy(self, reason: str) -> dict:
        """抓取当前页面完整 UI 层级树（Android 专用，poco 方式）。

        ⚠️ **门控方法**：本方法**必须**传入非空 ``reason``，否则抛
        :class:`OperationFailedError`。项目约定「没有确定要求，不使用
        本方法」——调用方必须在 reason 中明确说明抓取 UI 树的诉求
        （如「密码框被弹框遮挡，绕过可见性过滤读取文本」），便于事后
        审计与重构追踪。

        **为什么用 poco 而不是 uiautomator dump**：
        ``adb shell uiautomator dump`` 会与 ``pocoservice`` 抢占
        accessibility 服务（exit 137，2026-10-09 真机验证）。本方法
        走 ``poco.agent.hierarchy.dump()`` 拿整棵 UI 树，绕过可见性
        限制拿任何控件的文本/属性。

        :param reason: 调用本方法的明确理由（必填，非空）
        :return: poco hierarchy 原始 dict（含 ``payload`` 字段）
        :raises OperationFailedError: reason 缺失 / poco 调用失败时
        """
        stripped = (reason or "").strip()
        if not stripped:
            msg = (
                "dump_hierarchy() 必须提供非空 reason。"
                "项目约定：没有确定要求，不允许调用本方法。"
                "请在 reason 中说明抓取 UI 树的诉求。"
            )
            logger.warning(msg)
            raise OperationFailedError(msg)

        logger.warning(f"dump_hierarchy called: reason={stripped}")
        try:
            return self.poco.agent.hierarchy.dump()
        except Exception as exc:  # noqa: BLE001
            msg = f"poco dump 失败（reason={stripped}）：{exc}"
            logger.error(msg)
            raise OperationFailedError(msg) from exc
