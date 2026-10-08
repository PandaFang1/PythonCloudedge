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

---

## 文档导航

- 上一篇：[串口测试 ←](../guide/serial.md)
- 下一篇：[用例编写规则 →](./testcase.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
