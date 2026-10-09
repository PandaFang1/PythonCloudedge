# 登录页面文档 — Android（CloudEdge）

本文档记录 **CloudEdge 安卓端登录页（LoginActivity）** 的页面识别点、控件定位器与业务方法，
供编写和维护页面对象、用例时快速查阅。

> **范围说明**：本文档仅覆盖 Android（CloudEdge）端，iOS（云际）端的登录页对象待补齐；
> 当 iOS 端 `YunjiLoginPage` 实现后，需在本文档"双端对比"小节补齐 iOS 端定位器。
>
> **数据来源**：定位器全部基于真机 `adb shell uiautomator dump` 输出（udid=`cfed8c100822`，
> 系统语言 zh_CN，屏幕分辨率 1080×2400，密度 440dpi）。

---

## 页面对象与页面工厂注册表

| 页面名 | Android 页面类 | iOS 页面类 | 工厂 key |
|---|---|---|---|
| 登录页 | `CloudEdgeLoginPage` | _(待实现)_ | `(android, "login_page")` |

用例中通过 `PageFactory.create("android", "login_page", poco=..., udid=...)` 获取登录页实例。

```python
from pages.page_factory import PageFactory

login_page = PageFactory.create("android", "login_page", poco=poco, udid=udid)
login_page.wait_for_page_loaded()
login_page.login(account="13800138000", password="xxx", remember_password=True)
```

---

## 1. 页面职责

CloudEdge 登录页承担以下职责：

1. 用户登录前的入口，提供账号/密码登录、第三方登录（微信）、注册入口
2. 登录前的国家/地区选择（影响区号 +86 等）
3. 登录偏好设置：是否记住密码
4. 账号异常的辅助入口：忘记密码

页面元素概览（从上到下）：

```
┌─────────────────────────────┐
│  很高兴见到你                │  ← 欢迎语
│  国家/地区：中国 (+86)   ▾   │  ← layout_region（点击展开国家列表）
│  账号                        │  ← et_account（AutoCompleteTextView）
│  密码                        │  ← et_password（EditText，掩码）
│  ☑ 记住密码        忘记密码 │  ← checkbox_pwd + tv_forget_password
│  ──── 登录 ────              │  ← tv_login（登录按钮）
│        (微信图标)            │  ← iv_wechart（第三方登录）
│   还没有账号？立即注册       │  ← tv_register（注册入口）
└─────────────────────────────┘
```

---

## 2. 页面识别点（用于 `wait_for_page_loaded` / `is_login_page`）

| 识别点 | Android 定位器（resource-id） |
|---|---|
| 账号输入框 | `{"name": "com.cloudedge.smarteye:id/et_account"}` |
| 密码输入框 | `{"name": "com.cloudedge.smarteye:id/et_password"}` |

**两个识别点必须同时存在**才判定为登录页，避免单一元素误判。

选择依据：

- 两个识别点均为真机 dump 出的 resource-id，稳定性优于 text
- 其他页面（如「我的」页）不会出现 `et_account` + `et_password` 同时存在的情况，
  可唯一判定登录页

---

## 3. 控件定位器

### 3.1 国家/地区选择

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 国家/地区容器 | `{"name": "com.cloudedge.smarteye:id/layout_region"}` | 整体可点击，触发国家列表弹窗 |
| 国家名称文本 | `{"name": "com.cloudedge.smarteye:id/tv_region"}` | 当前选中国家（如「中国」）|
| 区号文本 | `{"name": "com.cloudedge.smarteye:id/tv_region_code"}` | 当前区号（如「+86」）|
| 展开箭头 | `{"name": "com.cloudedge.smarteye:id/iv_arrow"}` | 仅作视觉指示，断言用 `layout_region` 即可 |

### 3.2 账号 / 密码输入框

| 控件 | 定位器（Android） | 类型 | 说明 |
|---|---|---|---|
| 账号输入框 | `{"name": "com.cloudedge.smarteye:id/et_account"}` | AutoCompleteTextView | 进入登录页默认聚焦，可输入账号 |
| 密码输入框 | `{"name": "com.cloudedge.smarteye:id/et_password"}` | EditText（`password="true"`） | 掩码显示，密文输入 |

### 3.3 记住密码 / 忘记密码 / 登录

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 记住密码复选框 | `{"name": "com.cloudedge.smarteye:id/checkbox_pwd"}` | `checkable="true"`，可勾选/取消 |
| 忘记密码 | `{"name": "com.cloudedge.smarteye:id/tv_forget_password"}` | 文本按钮，跳转找回密码流程 |
| 登录 | `{"name": "com.cloudedge.smarteye:id/tv_login"}` | 主操作入口，提交账号密码 |

### 3.4 第三方登录 / 注册

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 微信登录 | `{"name": "com.cloudedge.smarteye:id/iv_wechart"}` | ImageView，NAF（无文字描述）|
| 立即注册 | `{"name": "com.cloudedge.smarteye:id/tv_register"}` | 文本按钮，跳转注册流程 |

### 3.5 国家/区域选择页（RegionPicker，登录页内弹出页）

点击 `layout_region` 后弹出的国家/地区选择页（全屏），控件如下：

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 搜索输入框 | `{"name": "com.cloudedge.smarteye:id/et_region_search"}` | 输入关键词实时过滤列表 |
| 国家列表项 | `{"name": "com.cloudedge.smarteye:id/tv_city"}` | 列表项文本（如「美国」），需叠加 `text` 精确匹配 |
| 国家列表容器 | `{"name": "com.cloudedge.smarteye:id/recycler_region"}` | RecyclerView，可滑动 |
| 字母索引栏 | `{"name": "com.cloudedge.smarteye:id/select_region_view"}` | 右侧 A~Z 快速跳转（1080×2400 下每字母 ~67px）|

**页面判定**：`et_region_search` 可见即视为已进入国家/地区选择页；
**返回判定**：点击目标国家项后，登录页双识别点（`et_account` + `et_password`）
重新同时出现即视为已返回登录页（`select_region()` 内置该断言）。

> 国家/区域选择页**不单独注册页面工厂**（无独立 factory key），其全部操作
> 封装在 `CloudEdgeLoginPage` 中（见 §4 业务方法）。

---

## 4. 业务方法

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点轮询等待（默认 20s，0.5s 间隔）|
| `is_login_page()` | 「账号」+「密码」输入框同时存在返回 True |
| `get_region()` | 获取当前国家名称（如「中国」），未渲染时返回空串 |
| `get_region_code()` | 获取当前区号（如「+86」），未渲染时返回空串 |
| `open_region_picker()` | 点击国家/地区容器，展开国家列表 |
| `input_account(account)` | 在账号输入框输入文本 |
| `input_password(password)` | 在密码输入框输入文本 |
| `is_remember_password_checked()` | 判断「记住密码」是否已勾选 |
| `set_remember_password(checked)` | 设置「记住密码」状态，True 勾选 / False 取消；当前一致时跳过 |
| `click_forgot_password()` | 点击「忘记密码」入口 |
| `click_login()` | 点击「登录」按钮 |
| `click_wechat_login()` | 点击微信登录图标 |
| `click_register()` | 点击「立即注册」入口 |
| `login(account, password, remember_password=True)` | 一站式登录：设置记住密码 → 输入账号 → 输入密码 → 点击登录 |

### 4.1 国家/区域选择 + ADBKeyboard 输入（新增）

| 方法 | 说明 |
|---|---|
| `search_region_via_adb_keyboard(china_text)` | 在国家搜索框输入**中文**关键词：切换 IME → ADBKeyboard → 点击搜索框 → `am broadcast` 广播文本 → 还原原 IME（前置：已处于国家/地区选择页）|
| `select_region(china_text)` | 点击过滤后列表中的目标国家项（`tv_city` + `text` 双条件定位），并断言返回登录页 |
| `handle_login_popups(max_attempts=3)` | 登录前置弹窗处理：识别点未出现时按系统 BACK 关闭遮挡弹窗，最多重试 max_attempts 次 |
| `login_with_region(region_text, account, password, remember_password=True)` | **一站式入口**：选国家（ADBKeyboard）→ 勾选记住密码 → 输入账号密码 → 点击登录 |

内部辅助（`_` 前缀，供上述方法复用）：

| 方法 | 说明 |
|---|---|
| `_adb_get_current_ime()` | 读取 `settings get secure default_input_method`，返回当前 IME ID |
| `_adb_set_ime(ime_id)` | `adb shell ime set <ime_id>` 切换输入法 |
| `_adb_broadcast_text(text)` | `am broadcast -a ADB_INPUT_TEXT --es msg "..."` 发送任意字符（含中文）|

模块级常量：`ADBKEYBOARD_IME_ID = "com.android.adbkeyboard/.AdbIME"`、
`ADBKEYBOARD_BROADCAST_ACTION = "ADB_INPUT_TEXT"`（`pages/android/login_page.py` 顶部集中管理）。

> **iOS 端接口对齐**：所有方法命名与 iOS 端 `YunjiLoginPage` 保持一致，便于双端用例复用。

---

## 5. 中文搜索支持方案（国家/地区选择）

国家/地区选择页提供 `et_region_search` 搜索框（resource-id：
`com.cloudedge.smarteye:id/et_region_search`），支持按关键词检索后过滤 `recycler_region`。
本节说明在 adb 自动化场景下输入**中文**关键词的可行方案与限制。

### 5.1 已知限制

`adb shell input text "<中文>"` **不支持非 ASCII 字符**，直接调用会报
`java.lang.NullPointerException: Attempt to get length of null array`
（InputShellCommand.sendText 抛错）。

经 `adb shell ime list -s` / `adb shell pm list packages` 验证，当前真机（小米 / Android 14）
**仅安装了搜狗输入法（`com.sohu.inputmethod.sogou.xiaomi/.SogouIME`）**，
且未暴露任何对外的 ADB 输入 broadcast 通道，因此：

- ❌ `adb shell input text "美国"` —— 不支持中文
- ❌ 搜狗输入法未提供 `ADB_INPUT_TEXT` 之类的标准 broadcast —— 不支持
- ❌ 未安装 ADBKeyboard / Clipper 等第三方调试输入法 —— 不支持
- ❌ `cmd input`（Android 12+）同样基于同一路径，不支持中文

### 5.2 备选方案：滑动定位（零依赖、适合任何项目）

直接在国家列表中反复 swipe 向上滑动，配合 dump 校验，直到目标国家可见后点击。
无需安装额外 IME，适合 CI / 临时调试场景。

**思路**：
1. 滑动到底部/中间区域
2. 每次滑动后调用 `uiautomator dump`
3. 解析 XML 中 `tv_city` 节点的 `text` 属性
4. 命中目标后点击其中心坐标

**优点**：不要求输入法支持、不要求 root
**缺点**：效率较低，大列表需多次滑动

### 5.3 现行方案：ADBKeyboard（已实现 ✅）

> **状态**：本方案已落地到 `pages/android/login_page.py`，对应方法为
> `search_region_via_adb_keyboard()` / `select_region()` / `login_with_region()`，
> 并由用例 `testcases/android/test_login_region.py` 真机验证通过（Redmi / MIUI）。

[ADBKeyboard](https://github.com/senzhk/ADBKeyBoard) 是面向 adb 自动化的开源输入法，
安装后用 `am broadcast` 即可发送任意字符（含中文）：

```bash
# 一次性安装（需先下载 ADBKeyboard.apk）
adb install -r ADBKeyboard.apk
adb shell ime enable com.android.adbkeyboard/.AdbIME
adb shell ime set com.android.adbkeyboard/.AdbIME

# 发送中文
adb shell am broadcast -a ADB_INPUT_TEXT --es msg "美国"
```

**优点**：支持任意字符（含中文、emoji、特殊符号），稳定
**缺点**：需安装第三方 APK；需在使用后还原原输入法（代码已内置 `try/finally` 还原逻辑）

> 用 `poco` 驱动的项目里建议封装成 fixture：
>
> ```python
> import pytest
>
> @pytest.fixture
> def chinese_ime(poco):
>     import subprocess
>     subprocess.run(["adb", "shell", "ime", "set", "com.android.adbkeyboard/.AdbIME"], check=True)
>     yield
>     # 还原为原输入法
>     subprocess.run(["adb", "shell", "ime", "set", "com.sohu.inputmethod.sogou.xiaomi/.SogouIME"], check=True)
> ```

### 5.4 备选方案：字母索引快速跳转（适合滚动列表）

国家/地区页右侧的 `select_region_view`（bounds=`[997,514][1080,2246]`）是字母索引栏。
在屏幕分辨率 1080×2400 下，可估算 26 个字母每个占 ~67px 高度：

| 字母 | 估算 y 坐标 | 字母 | 估算 y 坐标 |
|---|---|---|---|
| A | 547 | N | 1419 |
| B | 614 | O | 1486 |
| C | 681 | P | 1553 |
| D | 748 | Q | 1620 |
| E | 815 | R | 1687 |
| F | 882 | S | 1754 |
| G | 949 | T | 1821 |
| H | 1016 | V | 741 |
| I | 1083 | U | 1888 |
| J | 1150 | W | 1955 |
| K | 1217 | X | 2022 |
| L | 1284 | Y | 2089 |
| **M** | **1351** | Z | 2156 |

点击 y ≈ 1351 即可跳转到 M 区，再滚动一屏内即可定位「美国」。

**优点**：比纯滑动快，无需 IME
**缺点**：依赖字母索引栏的精确布局；不同分辨率需要重新估算

### 5.5 推荐做法（结合项目代码组织）

> **注意**：以下为早期设计草稿（滑动回退方案）。当前项目实际采用 §5.3 ADBKeyboard
> 方案并已实现于 `pages/android/login_page.py`（方法见 §4.1 表格），本节仅作
> 不允许安装第三方 APK 场景的备选思路参考。

```python
"""pages/android/login_page.py 的扩展示例：中文搜索 + 选择国家。"""
import re
import subprocess
import time
from typing import Optional

from pages.base_page import BasePage
from utils.log_utils import get_logger

logger = get_logger()


class CloudEdgeLoginPage(BasePage):
    # ... 原有定位器与业务方法 ...

    ET_REGION_SEARCH = {"name": "com.cloudedge.smarteye:id/et_region_search"}
    RECYCLER_REGION = {"name": "com.cloudedge.smarteye:id/recycler_region"}

    def search_region(self, china_text: str, max_swipes: int = 20) -> None:
        """在国家/地区搜索框中输入**中文**关键词并触发过滤。

        实现策略：当设备不支持 ADBKeyboard 时，回退到「滑动定位 + 点击」，
        避免在 CI 环境中因输入法问题失败。

        :param china_text: 中文国家名，如「美国」「日本」
        :param max_swipes: 最多滑动次数，默认 20
        :raises ElementNotFoundError: 滑动 max_swipes 次后仍未找到目标
        """
        # 点击搜索框并尝试 adb input text（支持中文的设备上会成功）
        self.click(self.ET_REGION_SEARCH)
        try:
            self._adb_input_text(china_text)
            time.sleep(0.8)
            # 检查列表是否被过滤为只剩目标项（避免不必要的滑动）
            xml = self._dump_page_xml()
            cities = self._parse_cities(xml)
            if china_text in cities:
                logger.info(f"中文搜索生效：{china_text}")
                return
            logger.warning("adb input text 未生效（可能 IME 未支持中文），回退到滑动定位")
        except Exception as exc:
            logger.warning(f"中文直接输入失败：{exc}，回退到滑动定位")

        # 回退方案：滑动定位
        for attempt in range(1, max_swipes + 1):
            xml = self._dump_page_xml()
            cities = self._parse_cities(xml)
            if china_text in cities:
                logger.info(f"在第 {attempt} 次滑动后找到「{china_text}」")
                return
            self._swipe_up_in_region()
            time.sleep(0.3)
        raise ElementNotFoundError(f"滑动 {max_swipes} 次仍未找到「{china_text}」")

    def select_region_by_search(self, china_text: str) -> None:
        """一键选择目标国家/地区：搜索 → 点击 → 等待回到登录页。

        :param china_text: 中文国家名
        """
        self.search_region(china_text)
        cities = self._parse_cities(self._dump_page_xml())
        if china_text not in cities:
            raise ElementNotFoundError(f"列表中未匹配到「{china_text}」")
        bounds = cities[china_text]
        nums = list(map(int, re.findall(r"\d+", bounds)))
        x1, y1, x2, y2 = nums
        self.click({"name": "com.cloudedge.smarteye:id/tv_city", "text": china_text})
        time.sleep(1.0)

    # ----- 内部辅助方法 -----

    @staticmethod
    def _adb_input_text(text: str) -> None:
        """通过 adb shell input text 输入文本（不支持中文）。"""
        subprocess.run(
            ["adb", "-s", "<udid>", "shell", "input", "text", text],
            check=True, timeout=5,
        )

    @staticmethod
    def _dump_page_xml() -> str:
        """dump 当前页面并返回 XML 内容。"""
        subprocess.run(
            ["adb", "-s", "<udid>", "shell", "uiautomator", "dump", "/sdcard/_dump.xml"],
            check=True, timeout=10,
        )
        subprocess.run(
            ["adb", "-s", "<udid>", "pull", "/sdcard/_dump.xml", "_dump.xml"],
            check=True, timeout=5,
        )
        with open("_dump.xml", "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _parse_cities(xml: str) -> dict:
        """解析 XML，返回 {国家名: bounds}。"""
        cities = {}
        for m in re.finditer(
            r'<node[^>]*\bresource-id="com\.cloudedge\.smarteye:id/tv_city"[^>]*>',
            xml,
        ):
            node = m.group(0)
            text_m = re.search(r'\btext="([^"]*)"', node)
            bounds_m = re.search(r'\bbounds="([^"]*)"', node)
            if text_m and bounds_m and text_m.group(1):
                cities[text_m.group(1)] = bounds_m.group(1)
        return cities

    def _swipe_up_in_region(self) -> None:
        """在国家列表区域向上滑动一屏。"""
        # 国家列表区域 y=404~2356，取中段滑动
        self.poco.swipe([0.5, 0.85], [0.5, 0.25], duration=0.3)
```

### 5.6 选型决策表

| 场景 | 推荐方案 | 备注 |
|---|---|---|
| 正式项目 / CI | ADBKeyboard（5.3）✅ **本项目已采用** | 中文/特殊字符一劳永逸，已封装为页面方法 |
| 临时调试 / 单次脚本 | 滑动定位（5.2） | 零依赖 |
| 不允许安装第三方 APK | 字母索引（5.4） + 滑动 | 适合合规要求严的环境 |
| 已知目标国家（如 M 区美国） | 字母索引（5.4） | 一步到位 |

---

## 6. Android 特有说明

- **进入登录页默认焦点**：账号输入框 `et_account` 默认 `focused="true"`，脚本中如需先操作国家区
  别，应避免直接调用 `input_account()` 后被自动聚焦打乱后续输入。
- **国家/地区容器整体可点击**：`layout_region`（ViewGroup）才是真正的点击目标，点击
  `iv_arrow`（ImageView，clickable=false）无效。
- **「登录」按钮类型**：类名虽为 `android.widget.TextView`，但 `clickable="true"`，
  用 `{"name": "..."}` 定位即可正常点击。
- **微信登录为 NAF 元素**：`iv_wechart` 标注 `NAF="true"`，可访问性标签缺失，仍可通过
  resource-id 唯一定位。
- **资源 ID 与行为**：内存挡板上 `btn_change_server` 容器覆盖整个滚动区域（高度 1734），
  仅作服务切换入口，不属于登录页核心交互，暂不纳入定位器。

---

## 7. 用法示例

### 7.1 一站式：选国家 + 登录（推荐）

```python
from pages.page_factory import PageFactory

def test_login_with_region(poco, udid, app_package):
    login_page = PageFactory.create("android", "login_page", poco=poco, udid=udid)

    login_page.start_app(app_package)              # 启动 CloudEdge
    login_page.handle_login_popups()               # 关闭 MIUI 等系统级遮挡弹窗
    assert login_page.wait_for_page_loaded(timeout=30)

    # 一站式：ADBKeyboard 输入「美国」选国家 → 勾选记住密码 → 输入账号密码 → 登录
    login_page.login_with_region(
        region_text="美国",
        account="xxx@example.com",
        password="xxx",
        remember_password=True,
    )
```

完整可运行用例见 `testcases/android/test_login_region.py`（含 pm clear、权限预授权、
autofill 禁用等真机前置处理与 Activity 级登录成功断言），运行方式：

```bash
python run.py --platform android -k test_login_with_region
```

### 7.2 分步调用（自定义流程时）

```python
# 1. 打开国家/地区选择页
login_page.open_region_picker()

# 2. ADBKeyboard 输入中文关键词过滤列表
login_page.search_region_via_adb_keyboard("美国")

# 3. 点击列表中的「美国」并断言返回登录页
login_page.select_region("美国")

# 4. 后续登录步骤
login_page.set_remember_password(True)
login_page.input_account("xxx@example.com")
login_page.input_password("xxx")
login_page.click_login()
```

---

## 附：定位器采集方法（Android）

1. 连接设备：`adb -s <udid> shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml`
2. 在 `ui.xml` 中筛选 `package="com.cloudedge.smarteye"` 的节点，提取 `resource-id` /
   `text` / `class` / `bounds` / `content-desc`
4. 每个页面选取 **2 个稳定且页面特有的元素**作为识别点，写入页面对象与文档

---

## 文档导航

- 上一篇：[页面识别 ←](./page-identification.md)
- 下一篇：[我的信息页（退出登录）→](./account-page.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)