"""CloudEdge 安卓端「选择设备类别」页面（AddSeriesTypeActivity）。

页面职责：
1. 维护「选择设备类别」页（`com.dctrain.module_add_device.view.AddSeriesTypeActivity`）
   及其顶部「添加设备」弹窗的元素定位器
2. 提供两种添加设备方式的业务方法：
   - **方式 A（按类别）**：从左侧分类列表选择设备类别（如「电池摄像机」），
     再从右侧类型列表选择具体类型（如「电池摄像机 (2.4G Wi-Fi)」），
     进入下一步配网流程（`PowerOnActivity`）
   - **方式 B（蓝牙）**：从顶部蓝牙区域选择已搜索到的设备；
     当搜索结果超过显示数量时，第 6 个槽位显示「查看更多」按钮，
     点击可展开其余设备

进入路径：首页 → 右上「添加设备」(`ivAddDevice`) → 弹窗「添加设备」条目
定位器说明（真机 poco dump 验证，udid=cfed8c100822，1080×2400）：
- 页面识别点：tv_title「选择设备类别」+ recyclerview_main（左侧分类列表）
- 分类项：recyclerview_main 下 framelayout 容器（clickable），文本 tv_category_name
- 类型项：recyclerview_detail 下 RelativeLayout 容器（clickable），
  含 tv_device_name + tv_des（描述，如 2.4G Wi-Fi / WIFI+蓝牙）
- 蓝牙区域 ll_bt 附近有 BT 设备时显示（含 rv_devices 与「查看更多」槽位）
"""

import time
from typing import List, Optional, Tuple

from pages.base_page import BasePage, ElementNotFoundError
from utils.log_utils import get_logger

logger = get_logger()


class CloudEdgeAddDeviceCategoryPage(BasePage):
    """CloudEdge「选择设备类别」页面（Android）：按类别添加 + 蓝牙添加。"""

    # ---------------- 元素定位器 ----------------
    # 页面识别点：标题「选择设备类别」+ 左侧分类列表
    TV_TITLE = {"name": "com.cloudedge.smarteye:id/tv_title"}
    RV_CATEGORY = {"name": "com.cloudedge.smarteye:id/recyclerview_main"}
    RV_DEVICE_TYPE = {"name": "com.cloudedge.smarteye:id/recyclerview_detail"}

    # 顶部工具栏
    IV_BACK = {"name": "com.cloudedge.smarteye:id/iv_back"}
    IV_MULTI = {"name": "com.cloudedge.smarteye:id/iv_multi"}  # 多选模式入口
    IV_SUBMIT = {"name": "com.cloudedge.smarteye:id/iv_submit"}  # 顶部提交按钮

    # 蓝牙区域（ll_bt 容器，附近有 BT 设备时显示）
    LL_BT = {"name": "com.cloudedge.smarteye:id/ll_bt"}
    IV_SEARCH = {"name": "com.cloudedge.smarteye:id/iv_search"}
    TV_SEARCH = {"name": "com.cloudedge.smarteye:id/tv_search"}  # 「搜索到的设备...」
    TV_BE_SURE_STATUS = {"name": "com.cloudedge.smarteye:id/tv_be_sure_status"}  # 「请确保设备处于配网状态」
    RV_BT_DEVICES = {"name": "com.cloudedge.smarteye:id/rv_devices"}
    BT_ITEM_MODEL = {"name": "com.cloudedge.smarteye:id/tv_model"}  # 设备型号 or 「查看更多」
    BT_ITEM_PIC = {"name": "com.cloudedge.smarteye:id/iv_pic"}
    TV_ADD_MANUAL = {"name": "com.cloudedge.smarteye:id/tv_add_manual_add"}  # 「手动添加」

    # 蓝牙设备「查看更多」底部抽屉（点击「查看更多」后弹出）
    BT_SHEET_CONTAINER = {"name": "com.cloudedge.smarteye:id/design_bottom_sheet"}
    BT_SHEET_CLOSE = {"name": "com.cloudedge.smarteye:id/iv_close"}
    BT_SHEET_RECYCLER = {"name": "com.cloudedge.smarteye:id/recyclerView"}

    # 左侧分类项（文本定位：tv_category_name，文本=类别名）
    # 右侧类型项（文本定位：tv_device_name，文本=类型名）
    CATEGORY_NAME = {"name": "com.cloudedge.smarteye:id/tv_category_name"}
    DEVICE_TYPE_NAME = {"name": "com.cloudedge.smarteye:id/tv_device_name"}
    DEVICE_TYPE_DES = {"name": "com.cloudedge.smarteye:id/tv_des"}
    DEVICE_TYPE_FEATURES = {"name": "com.cloudedge.smarteye:id/iv_device_features"}

    # 「查看更多」按钮文本（蓝牙设备超量时第 6 个槽位显示）
    MORE_BT_DEVICES_TEXT = "查看更多"

    def __init__(self, poco, udid: str = ""):
        """
        :param poco: AndroidUiautomationPoco 驱动实例
        :param udid: 设备 UDID，用于 app 生命周期控制
        """
        super().__init__(poco=poco, udid=udid, platform="android")

    # ---------------- 业务方法 ----------------

    def wait_for_page_loaded(self, timeout: float = 20.0) -> bool:
        """等待「选择设备类别」页加载完成（标题 + 左侧分类列表同时出现）。

        :param timeout: 等待超时时间（秒）
        :return: 页面加载完成返回 True
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_page():
                logger.debug(f"「选择设备类别」页识别点均已出现（等待 <= {timeout}s）")
                return True
            time.sleep(0.5)

        logger.warning(
            f"「选择设备类别」页识别点在 {timeout}s 内未同时出现："
            f"TV_TITLE={self.exists(self.TV_TITLE)}，"
            f"RV_CATEGORY={self.exists(self.RV_CATEGORY)}"
        )
        return False

    def is_page(self) -> bool:
        """判断当前是否处于「选择设备类别」页。

        :return: 标题为「选择设备类别」且左侧分类列表可见返回 True
        """
        if not self.exists(self.TV_TITLE):
            return False
        title = self.get_text(self.TV_TITLE)
        return title == "选择设备类别" and self.exists(self.RV_CATEGORY)

    def get_page_title(self) -> str:
        """获取页面标题文本（通常为「选择设备类别」）。"""
        return self.get_text(self.TV_TITLE)

    def click_back(self) -> None:
        """点击左上返回键，返回主页。"""
        self.click(self.IV_BACK)
        logger.info("已点击返回键，返回主页")

    # ---------------- 方式 A：按类别添加 ----------------

    def get_categories(self) -> List[str]:
        """获取左侧分类列表的所有可见类别名（递归子项内 text 节点）。

        :return: 类别名列表（如 ["电池摄像机", "智能门铃", ...]）
        """
        if not self.exists(self.RV_CATEGORY):
            return []
        result: List[str] = []
        for item in self.poco(**self.RV_CATEGORY).children():
            text_node = item.child(self.CATEGORY_NAME["name"])
            if text_node.exists():
                text = text_node.attr("text")
                if text:
                    result.append(text)
        return result

    def select_category(self, category_name: str) -> None:
        """从左侧分类列表选择指定类别，并等待右侧类型列表刷新。

        :param category_name: 类别名（如「电池摄像机」）
        :raises ElementNotFoundError: 类别未在列表中或未渲染
        """
        target = self.poco(self.CATEGORY_NAME["name"], text=category_name)
        if not target.exists():
            available = self.get_categories()
            raise ElementNotFoundError(
                f"分类「{category_name}」未在列表中（可见分类：{available}）；"
                f"可通过左右滑动左侧分类列表加载更多"
            )
        target.click()
        # 等待右侧类型列表完成切换（不同分类的项数 / 名称 / 描述均不同）
        time.sleep(0.6)
        logger.info(f"已选择分类「{category_name}」，等待右侧类型列表刷新")

    def get_device_types(self) -> List[Tuple[str, str]]:
        """获取右侧类型列表的所有可见类型（名称, 描述）。

        :return: [(名称, 描述), ...]，如 [("电池摄像机", "(2.4G Wi-Fi)"), ...]
        """
        if not self.exists(self.RV_DEVICE_TYPE):
            return []
        types: List[Tuple[str, str]] = []
        # 跳过第一层 LinearLayout（与 rv_devices 一致为行容器），再深入 RelativeLayout
        for outer in self.poco(**self.RV_DEVICE_TYPE).children():
            for item in outer.children():
                name_node = item.offspring(self.DEVICE_TYPE_NAME["name"])
                des_node = item.offspring(self.DEVICE_TYPE_DES["name"])
                if name_node.exists():
                    name = name_node.attr("text") or ""
                    des = des_node.attr("text") if des_node.exists() else ""
                    if name:
                        types.append((name, des))
        return types

    def select_device_type(self, type_name: str, type_des: Optional[str] = None) -> None:
        """从右侧类型列表选择指定类型，进入下一步配网流程（PowerOnActivity）。

        **重要前提**：调用前必须先调用 `select_category(name)` 选好大类别，
        否则可能误点其他大类别下同名类型。本方法只校验**当前右侧已渲染**
        的类型列表中是否含目标项，不主动切换大类别。

        :param type_name: 类型名（如「电池摄像机」）
        :param type_des: 类型描述（如「(2.4G Wi-Fi)」）。同一大类别下类型名可能
            重复（如「电池摄像机」下有 2.4G Wi-Fi / WIFI+蓝牙 两个同名项），
            推荐传 `type_des` 用 (名称, 描述) 双条件唯一定位
        :raises ElementNotFoundError: 类型未在右侧当前可见列表中
        """
        target_item = None
        if type_des is not None:
            # 双条件定位：遍历 item，匹配 (名称 + 描述) 同时满足
            for outer in self.poco(**self.RV_DEVICE_TYPE).children():
                for item in outer.children():
                    name_node = item.offspring(self.DEVICE_TYPE_NAME["name"])
                    des_node = item.offspring(self.DEVICE_TYPE_DES["name"])
                    if (
                        name_node.exists()
                        and name_node.attr("text") == type_name
                        and des_node.exists()
                        and des_node.attr("text") == type_des
                    ):
                        target_item = item
                        break
                if target_item is not None:
                    break
        else:
            # 单条件定位：仅匹配类型名
            target_node = self.poco(
                self.DEVICE_TYPE_NAME["name"], text=type_name
            )
            if target_node.exists():
                # .parent() 回到 item 容器（RelativeLayout）
                target_item = target_node.parent()

        if target_item is None:
            available = self.get_device_types()
            hint = (
                "；同名类型较多时建议传 type_des 双条件定位"
                if type_des is None else ""
            )
            raise ElementNotFoundError(
                f"设备类型「{type_name}"
                f"{f' ({type_des})' if type_des else ''}」"
                f"未在右侧当前列表中（可见类型：{available}）{hint}"
            )
        target_item.click()
        logger.info(
            f"已选择设备类型「{type_name}"
            f"{f' ({type_des})' if type_des else ''}」"
        )

    def add_device_by_category(
        self, category_name: str, type_name: str, type_des: Optional[str] = None,
    ) -> None:
        """一站式按类别添加设备：先选大类别，等右侧刷新，再选小类别。

        该方法是**推荐**的标准方式，强制按"大类别→小类别"顺序执行，
        避免 `select_device_type` 在错误大类别下误点同名类型。

        :param category_name: 大类别名（如「电池摄像机」）
        :param type_name: 小类别名（如「电池摄像机」）
        :param type_des: 小类别描述（如「(2.4G Wi-Fi)」），用于唯一定位同名项
        :raises ElementNotFoundError: 类别或类型未找到时抛出
        """
        # 1. 选大类别（内部含 0.6s 等待右侧刷新）
        self.select_category(category_name)
        # 2. 二次断言：右侧类型列表中存在目标项（防止大类别切换异常）
        current = self.get_device_types()
        exists = any(
            n == type_name and (type_des is None or d == type_des)
            for n, d in current
        )
        if not exists:
            raise ElementNotFoundError(
                f"大类别「{category_name}」已选，但右侧类型列表中无目标项"
                f"「{type_name}{f' ({type_des})' if type_des else ''}」"
                f"（当前可见类型：{current}）"
            )
        # 3. 选小类别
        self.select_device_type(type_name, type_des=type_des)

    def start_flow(
        self, category_name: str, type_name: str, type_des: Optional[str] = None,
    ) -> "BaseAddDeviceFlow":
        """一站式按类别添加设备 + 返回对应 Flow 实例。

        等价于：
            self.add_device_by_category(category, type, type_des)
            return DeviceFlowFactory.create(category, type, type_des, self.poco, self.udid)

        业务用例拿到 Flow 实例后，调用 `flow.run(...)` 触发端到端配网流程。
        延迟导入 `add_device_flow` 避免循环依赖。

        :param category_name: 大类别名（如「智能门铃」）
        :param type_name: 小类别名（如「Chime Base」）
        :param type_des: 小类别描述（可选，用于消歧同名 type）
        :return: 对应设备类型的 Flow 子类实例
        :raises UnsupportedDeviceTypeError: (category, type_name) 未在工厂注册
        """
        # 延迟导入避免循环依赖（add_device_flow 可能引用本 PO）
        from pages.android.add_device_flow.factory import DeviceFlowFactory

        # 1. 选类别 + 类型 + 跳转 PowerOnActivity
        self.add_device_by_category(category_name, type_name, type_des)
        # 2. 工厂分发返回 Flow 实例（poco/udid 透传）
        return DeviceFlowFactory.create(
            category=category_name,
            type_name=type_name,
            type_des=type_des,
            poco=self.poco,
            udid=self.udid,
        )

    # ---------------- 方式 B：蓝牙添加 ----------------

    def is_bluetooth_area_visible(self) -> bool:
        """判断顶部蓝牙区域是否可见（仅附近有 BT 设备时显示）。

        :return: 蓝牙区域可见返回 True
        """
        return self.exists(self.LL_BT)

    def get_bluetooth_devices(self) -> List[str]:
        """获取蓝牙设备列表。

        优先读取「查看更多」底部抽屉中的完整设备列表（已展开场景）；
        若未展开，则回退到蓝牙区域原始 RecyclerView 列表（含「查看更多」占位）。

        :return: 设备型号文本列表（如 ["124207252", ...] 或含 "查看更多"）
        """
        # 优先：底部抽屉已展开时读取完整列表
        if self.exists(self.BT_SHEET_CONTAINER):
            recycler = self.poco(**self.BT_SHEET_RECYCLER)
            if recycler.exists():
                result: List[str] = []
                for item in recycler.children():
                    model_node = item.offspring(self.BT_ITEM_MODEL["name"])
                    if model_node.exists():
                        text = model_node.attr("text")
                        if text:
                            result.append(text)
                if result:
                    return result
        # 回退：蓝牙区域原始 RecyclerView
        if not self.exists(self.RV_BT_DEVICES):
            return []
        result: List[str] = []
        for item in self.poco(**self.RV_BT_DEVICES).children():
            model_node = item.offspring(self.BT_ITEM_MODEL["name"])
            if model_node.exists():
                text = model_node.attr("text")
                if text:
                    result.append(text)
        return result

    def is_more_devices_sheet_visible(self) -> bool:
        """判断「查看更多」底部抽屉是否已弹出。"""
        return self.exists(self.BT_SHEET_CONTAINER)

    def close_more_devices_sheet(self) -> None:
        """关闭「查看更多」底部抽屉（点击右上角关闭按钮）。"""
        if not self.is_more_devices_sheet_visible():
            return
        self.click(self.BT_SHEET_CLOSE)
        logger.info("已关闭「查看更多」底部抽屉")

    def has_more_bt_devices_button(self) -> bool:
        """判断是否出现「查看更多」按钮（蓝牙设备超量时第 6 个槽位显示）。

        :return: 「查看更多」按钮可见返回 True
        """
        return self.exists({"text": self.MORE_BT_DEVICES_TEXT})

    def click_more_bt_devices(self) -> None:
        """点击蓝牙区域「查看更多」按钮，展开其余搜索结果。

        :raises ElementNotFoundError: 当前未显示「查看更多」按钮时抛出
        """
        target = self.poco(text=self.MORE_BT_DEVICES_TEXT)
        if not target.exists():
            raise ElementNotFoundError(
                "蓝牙区域未显示「查看更多」按钮（设备未超量或已展开）"
            )
        target.click()
        logger.info("已点击「查看更多」展开蓝牙设备列表")

    def select_bluetooth_device(self, model: str) -> None:
        """从蓝牙列表选择指定型号的设备。

        自动适配两种来源：
        - 「查看更多」底部抽屉已展开时，从 `recyclerView` 中选择
        - 未展开时，从蓝牙区域原始 RecyclerView 中选择

        :param model: 设备型号文本
        :raises ElementNotFoundError: 未找到该型号的设备时抛出
        """
        target = self.poco(self.BT_ITEM_MODEL["name"], text=model)
        if not target.exists():
            available = self.get_bluetooth_devices()
            raise ElementNotFoundError(
                f"蓝牙设备「{model}」未在列表中（可见：{available}）"
            )
        target.click()
        logger.info(f"已选择蓝牙设备「{model}」")

    def click_manual_add(self) -> None:
        """点击蓝牙区域底部「手动添加」按钮（按 SN/序列号添加）。"""
        self.click(self.TV_ADD_MANUAL)
        logger.info("已点击「手动添加」")
