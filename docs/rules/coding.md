# 代码规范

> 本章是后续开发的**统一约定**，所有参与者必须遵守。违反约定的代码将被拒绝合入。

## 1.1 命名规范

| 对象 | 命名规则 | 示例 |
|---|---|---|
| **Android 页面类** | `CloudEdge` 前缀 + 业务名 | `CloudEdgeMainPage`、`CloudEdgeLoginPage` |
| **iOS 页面类** | `Yunji` 前缀 + 业务名 | `YunjiMainPage`、`YunjiLoginPage` |
| **页面文件** | 蛇形 + `_page.py` | `login_page.py` |
| **页面注册键** | 业务名小写 + `_page` | `("android", "login_page")` |
| **定位器常量** | 全大写 + 下划线 | `TAB_HOME`、`BTN_LOGIN`、`INPUT_USER` |
| **业务方法** | 小写蛇形、动词开头 | `login()`、`open_my_page()`、`is_tab_visible()` |
| **用例函数** | `test_` 开头 | `test_login_success` |
| **fixture** | 全小写蛇形 | `device_info`、`serial_manager` |
| **串口名** | 小写蛇形、含义清晰 | `camera_console`、`camera_log` |
| **日志 logger** | 模块名 | `logger = get_logger(__name__)` |

> **强约束**：同一业务的 Android 与 iOS 页面类，**业务方法名必须完全一致**，
> 这是「共用用例一次编写双端运行」的前提。

## 1.2 目录结构约定

- `pages/android/` 仅放 Android 端页面类（`CloudEdge*`）
- `pages/ios/` 仅放 iOS 端页面类（`Yunji*`）
- `pages/base_page.py`、`pages/page_factory.py` 为共用层，**禁止平台分支判断**
- `testcases/android/` 仅放 Android 端**特有**用例（如权限弹窗、系统返回键）
- `testcases/ios/` 仅放 iOS 端**特有**用例（如 iOS 键盘处理）
- 双端共用的用例**只能放**在 `testcases/` 根目录，**且必须声明 `platform` fixture**
- 串口用例放 `testcases/` 根目录（如 `test_serial.py`），不进入平台子目录
- 测试数据放 `test_datas/`，禁止硬编码到用例内

### 1.2.1 测试模块子目录约定（按业务模块聚合）

> 自 2026-10-10 起，**安卓端测试按业务模块分子目录**聚合，详见
> [账号模块文档](../guide/account-module.md) /
> [Jingle 添加模块文档](../guide/jingle-add-module.md) /
> [Jingle 删除模块文档](../guide/jingle-delete-module.md)。

```
testcases/android/
├── conftest.py              # 跨模块共享：常量、工具函数、跨模块 fixture
├── test_add_device.py       # 公共用例（按类别 / 蓝牙两种方式）— 基础设施
├── test_app_lifecycle.py    # 公共用例，app 生命周期
├── account/                 # 账号模块
│   ├── conftest.py          # 模块 fixture（android_my_page、android_account_page）
│   ├── test_login.py
│   ├── test_logout.py
│   └── test_switch.py
├── jingle_add/              # Jingle 添加模块
│   ├── conftest.py          # 模块 fixture（jingle_category_page）
│   ├── test_full.py
│   └── test_quick.py
└── jingle_delete/           # Jingle 删除模块
    ├── conftest.py          # 模块 fixture（jingle_main_with_target）
    └── test_delete.py
```

**强约束**：

1. **测试文件不得 import 其他 test_*.py 文件**（消除横向耦合）
2. 跨模块共享的工具/常量/fixture 放在 `testcases/android/conftest.py`
3. 单模块特有的 fixture 放在该模块自己的 `conftest.py`
4. **禁止反向依赖**：模块 conftest.py 可依赖共享 conftest，反之不允许

## 1.3 PO 页面编写规范

**强制要求**：

1. **必须继承 `BasePage`**，不允许多继承
2. **定位器必须是类属性**（不是实例属性），便于反射查找
3. **构造器签名固定**：`def __init__(self, poco, udid)`，通过 `super().__init__(poco, udid)`
4. **业务方法不直接调用 airtest/poco 原生 API**，必须通过 `BasePage` 封装的方法
5. **不允许在页面类中调用 `start_app/stop_app/restart_app`**（由 `app_page` fixture 统一管控）
6. **跨页面跳转封装为业务方法**，不允许在用例内跨多个页面类直接操作

```python
# ✅ 正确示例
class CloudEdgeLoginPage(BasePage):
    INPUT_USER = {"text": "用户名"}
    BTN_LOGIN = {"text": "登录"}

    def __init__(self, poco, udid):
        super().__init__(poco, udid)

    def login(self, user: str, pwd: str):
        with allure.step(f"账号密码登录：{user}"):
            self.input_text(self.INPUT_USER, user)
            self.click(self.BTN_LOGIN)

# ❌ 错误示例：定位器做实例属性、调用原生 API
class TestPage(BasePage):
    def __init__(self, poco, udid):
        self.btn = {"text": "登录"}  # 禁止
        super().__init__(poco, udid)

    def click_btn(self):
        self.poco(self.btn).click()  # 应使用 self.click(self.btn)
```

## 1.4 定位器规范

**优先级**（从高到低，违反优先级将被拒合并整改）：

1. **基本选择器**（`name` / `text` / `type`）— 首选
2. **相对选择器**（`parent` / `child` / `sibling`）— 复杂结构
3. **索引** — 列表/重复元素

**禁止**：

- 使用绝对坐标定位
- 使用 `xpath` / css selector（poco 不支持）
- 直接使用正则作为定位器
- 定位器中混写业务数据（如 `{"text": f"用户{user_id}"}`），业务数据应通过参数化传入

## 1.5 串口编写规范

1. **串口配置集中在 `config.yaml`** 的 `serial_ports` 节点，禁止在代码内硬编码端口
2. **每个串口必须配置 `name`**，用例通过 `@pytest.mark.parametrize("serial_name", [...])` 引用
3. **`SerialPort` 调用统一走 fixture**（`serial_port` / `serial_control_port` / `serial_log_port`），禁止在用例内 `import serial` 直连
4. **超时一律传入**，禁止依赖默认值；建议控制类 ≤ 10s，日志采集 ≤ 30s
5. **关键字与正则作为测试数据**，建议放入 `test_datas/`，便于维护
6. **串口日志**自动写入 `logs/serial_logs/`，禁止在用例内自行保存日志
7. **断言失败时**，在用例内显式 `attach` 最后一段串口输出，便于定位

## 1.6 风格约束

- **PEP-8**，行宽 **100**（已通过 pycodestyle 检查）
- `from xxx import yyy` 优先，禁止 `import xxx as` 仅因名字冲突
- 严禁 `import**`（`*` 引入）。**严禁** `import xxx as**`
- 严禁未使用 import、严禁 `print()` 调试（用 `logger.debug`）
- 类与公共方法必须有 docstring（中文或英文均可）
- 禁止单文件超过 **500 行**（超过则拆分）

## 1.7 模块化与链式调用约定

> 本节是 2026-10-10 模块化重构后的**核心约定**，所有新增测试 / 业务方法必须遵守。

### 1.7.1 Fixture 链式依赖

fixture 按"自底向上"分层复用，**高级 fixture 依赖低级 fixture**，通过 yield 传递结果：

```
# testcases/android/conftest.py — 跨模块共享层
android_test_env         # pm clear + 预授权 + 禁用 autofill
    ↓
android_logged_in        # 启动 app + 登录（账号模块使用，依赖 android_test_env）
android_preserved_app    # force-stop + 启动 + 按需登录（设备模块使用，不 pm clear）
    ↓
android_category_page    # 登录态主页 → 「选择设备类别」页（依赖 android_logged_in）

# account/conftest.py — 账号模块特有
android_my_page          # 登录态主页 → 「我的」Tab（依赖 android_logged_in）
    ↓
android_account_page     # 「我的」Tab → 「我的信息」页（依赖 android_my_page）

# jingle_add/conftest.py — Jingle 添加模块特有
jingle_category_page     # 登录态主页 → 「选择设备类别」页（依赖 android_preserved_app）

# jingle_delete/conftest.py — Jingle 删除模块特有
jingle_main_with_target  # 登录态主页 + jingle_delete_page（依赖 android_preserved_app）
```

**用例仅需声明依赖的最高级 fixture**：

```python
# ✅ 推荐：用例只声明所需的最外层 fixture，链式内部细节全在 conftest 中
def test_logout(android_account_page, platform, device_info):
    login_page, main_page, my_page, account_page = android_account_page
    account_page.logout(confirm=True)

# ❌ 反例：在用例内手动串联多个 fixture 调用
def test_logout(android_test_env, android_logged_in, ...):
    # 重复实现 fixture 已经封装好的样板代码
    ...
```

### 1.7.2 Fixture 命名规范

- **跨模块共享**：`android_` 前缀（如 `android_test_env`、`android_logged_in`）
- **模块特有**：`<模块名>_` 前缀（如 `android_my_page` 在 account 模块，但因属账号相关
  也可加 `account_` 前缀；`jingle_category_page` / `jingle_main_with_target` 显式带 jingle 前缀）
- **页面对象级**（PO）：`<页面类名小写>`（如 `login_page`、`main_page`）

### 1.7.3 Fixture 层级（自底向上）

| 层级 | 命名风格 | 位置 | 数量限制 |
|---|---|---|---|
| 0. 平台/驱动 | `poco_driver`、`airtest_device`、`device_info` | `testcases/conftest.py` | 现有不变 |
| 1. 跨模块共享环境 | `android_<name>` | `testcases/android/conftest.py` | ≤ 5 个 |
| 2. 跨模块共享导航 | `android_<page_name>` | `testcases/android/conftest.py` | ≤ 3 个 |
| 3. 模块特有 | `<module>_<name>` | `<module>/conftest.py` | ≤ 3 个/模块 |

### 1.7.4 业务方法链式返回（推荐，**新代码**遵守）

> 自 2026-10-10 起，**新增**的 Page Object 业务方法推荐**返回 `self`**，便于
> 「一站式」门面 PO 与外部脚本的链式调用。已存在的方法暂不强制改造。

```python
# ✅ 推荐：新代码支持链式调用
class CloudEdgeLoginPage(BasePage):
    def open_region_picker(self) -> "CloudEdgeLoginPage":
        self.click(self.LAYOUT_REGION)
        return self

    def input_account(self, account: str) -> "CloudEdgeLoginPage":
        self.input_text(self.ET_ACCOUNT, account)
        return self

# 链式调用（一站式）
login_page = PageFactory.create("android", "login_page", ...)
login_page.open_region_picker().input_account("13800138000")

# 一站式门面 PO 的内部复用
class JingleAddPage(BasePage):
    def add_jingle_device(self, ...) -> List[str]:
        # 内部门面 PO 仍按需调用各 page 方法
        ...
        devices = self.main_page.get_device_list()
        return devices

# ❌ 反例：旧风格（仍允许，但鼓励改造）
def open_region_picker(self) -> None:
    self.click(self.LAYOUT_REGION)
```

**返回 `self` 的方法需满足**：

1. 方法无重要返回值（如设备列表）时统一返回 `self`
2. 类型注解使用字符串形式（`"CloudEdgeLoginPage"`）以避免循环引用
3. docstring 需注明「支持链式调用」

### 1.7.5 跨模块共享工具下沉

跨多个测试文件复用的代码必须下沉到 `conftest.py`：

| 类型 | 命名 | 位置 |
|---|---|---|
| 跨模块常量 | `UPPER_SNAKE_CASE` | 共享 `conftest.py` |
| 跨模块工具函数 | `snake_case` | 共享 `conftest.py` |
| 跨模块 fixture | `android_<name>` | 共享 `conftest.py` |
| 模块内部 fixture | `<module>_<name>` | 模块 `conftest.py` |

**禁止**：

- 在测试函数内 inline 实现跨文件复用的工具函数
- 在测试文件顶层（模块级）定义跨文件复用的常量
- 在 `pages/` 下的页面类中实现测试样板（pm clear、权限授予等）

---

## 文档导航

- 上一篇：[串口测试 ←](../guide/serial.md)
- 下一篇：[用例编写规则 →](./testcase.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
