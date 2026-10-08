# 用例编写规则

> 本章是后续编写用例的**统一约定**，所有参与者必须遵守。

## 2.1 共用用例 vs 平台特有用例

| 类型 | 放置位置 | 写法要求 | 触发条件 |
|---|---|---|---|
| **共用用例** | `testcases/` 根目录 | 函数签名含 `platform` fixture | `--platform` 自动参数化 |
| **Android 特有** | `testcases/android/` | 可不含 `platform` | 仅 `--platform android` |
| **iOS 特有** | `testcases/ios/` | 可不含 `platform` | 仅 `--platform ios` |
| **串口用例** | `testcases/` 根目录（如 `test_serial.py`） | 必须 `@pytest.mark.serial` | 任意平台参数 |

> **判定标准**：能在 Android 与 iOS 上跑出相同业务结果，就写共用用例；
> 否则拆分为平台特有用例。**严禁** 在共用用例内写 `if platform == "android"` 分支。

## 2.2 函数签名规范

共用用例**必须**声明以下 fixture（顺序按依赖层级）：

```python
def test_xxx(app_page, platform):
    ...
```

平台特有用例：

```python
# Android
def test_xxx_android(app_page):
    ...

# iOS
def test_xxx_ios(app_page):
    ...
```

串口用例：

```python
@pytest.mark.parametrize("serial_name", ["camera_console"])
def test_xxx(serial_name, serial_port):
    ...
```

## 2.3 marker 使用规则

| marker | 测试代码 / 业务 / 用途 |
|---|---|
| `@pytest.mark.android` | Android 端特有用例 |
| `@pytest.mark.ios` | iOS 端特有用例 |
| `@pytest.mark.smoke` | 冒烟用例（核心路径） |
| `@pytest.mark.regression` | 回归用例 |
| `@pytest.mark.serial` | 串口用例 |

**强制规则**：

1. 平台特有用例**必须**打 `@pytest.mark.android` 或 `@pytest.mark.ios`
2. 共用用例**不强制**打平台 marker（已被 `--platform` 参数化）
3. 冒烟用例**必须**叠加 `@pytest.mark.smoke`，回归用例叠加 `@pytest.mark.regression`
4. **串口用例必须**打 `@pytest.mark.serial`，便于单独跑

## 2.4 参数化使用规范

1. **平台参数化由 conftest 自动完成**（通过 `--platform`），共用用例**禁止**自行 `@pytest.mark.parametrize("platform", [...])`
2. 串口用例必须使用 `@pytest.mark.parametrize("serial_name", [...])` 指定串口
3. 多组数据驱动（如不同账号登录）使用 `@pytest.mark.parametrize`，每组数据要清晰命名
4. 参数名采用小写蛇形，禁止使用中文字段名作为参数值

## 2.5 allure 标准写法

每个用例必须包含 `epic` + `feature` + `title`，可选 `story` + `severity`：

```python
@allure.epic("登录")                           # 一级：业务模块
@allure.feature("账号密码登录")                # 二级：功能点
@allure.story("正常登录")                      # 三级：场景（可选）
@allure.severity(allure.severity_level.CRITICAL)  # 严重级别（可选）
@allure.title("账号密码登录_成功")  # 用例标题
def test_login_success(app_page, platform):
    with allure.step("步骤1：输入账号"):
        ...
    with allure.step("步骤2：点击登录"):
        ...
```

## 2.6 断言规则

1. **每条用例至少 1 条断言**，禁止「用例无断言」（`pytest.skip` / `pytest.xfail` 除外）
2. **优先使用 `assert` 表达式**（pytest 友好），禁止 `unittest.assertEqual`
3. **失败信息必须可读**：`assert x == y, f"期望 {y}, 实际 {x}"`
4. **软断言**：对非核心校验使用 `pytest.assume`；核心校验用 `assert`
5. **断言失败时自动附加上下文**：失败截图由 `pytest_runtest_makereport` 钩子自动附加

## 2.7 串口用例编写

控制类：

```python
import allure
import pytest

@pytest.mark.serial
@allure.epic("串口")
@allure.feature("控制命令")
@pytest.mark.parametrize("serial_name", ["camera_console"])
def test_send_and_wait_keyword(serial_name, serial_port):
    with allure.step("发送 version 命令"):
        serial_port.send("version")
    with allure.step("等待关键字响应"):
        line = serial_port.wait_for_keyword("version", timeout=10)
    assert line, "未收到 version 关键字响应"
```

日志采集类：

```python
@pytest.mark.serial
@allure.epic("串口")
@allure.feature("日志采集")
def test_log_extract_kinfo(serial_log_port):
    with allure.step("提取启动耗时"):
        serial.log_port.extract_info(r"boot cost (\d+)ms", group=1, timeout=30)
```

**失败自动化**（`conftest.py` 已统一处理，无需用例手动）：

- 串口用例失败时，`pytest_runtest_makereport` 钩子**自动** `allure.attach` 当前用例所使用串口的历史最后 200 行输出（TEXT 类型）
- 因此用例内**无需**为失败分支单独处理串口证据，conftest 已自动完成
- 用例仍可在成功路径显式 `allure.attach` 关键数据，便于报告阅读

## 2.8 用例隔离与清理

- 每个用例结束后，`app_page` fixture 自动关闭 app
- 每个用例重建 `poco_driver`，避免状态污染
- 用例**不**自行调用 `stop_app`/`restart_app`（由 fixture 管控）
- 串口用例**不**自行关闭串口（`serial_manager` 在 session 结束时统一关闭）

---

## 文档导航

- 上一篇：[代码规范 ←](./coding.md)
- 下一篇：[执行规则 →](./execution.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
