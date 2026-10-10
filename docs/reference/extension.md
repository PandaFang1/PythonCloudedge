# 扩展指南

## 新增一个页面（3 步）

1. 在 `pages/android/` 与 `pages/ios/` 各实现一个页面类（继承 `BasePage`，
   定义定位器类属性 + 业务方法，**双端业务方法保持同名**）：

```python
# pages/android/login_page.py
from pages.base_page import BasePage

class CloudEdgeLoginPage(BasePage):
    INPUT_USER = {"text": "用户名"}
    BTN_LOGIN = {"text": "登录"}

    def login(self, user: str, pwd: str):
        self.input_text(self.INPUT_USER, user)
        self.click(self.BTN_LOGIN)
```

2. 在 `pages/android/__init__.py` / `pages/ios/__init__.py` 导出页面类；

3. 在 `pages/page_factory.py` 的 `REGISTRY` 中注册：

```python
REGISTRY = {
    ("android", "main_page"): CloudEdgeMainPage,
    ("android", "login_page"): CloudEdgeLoginPage,   # 新增
    ...
}
```

用例中通过工厂获取当前平台页面（`app_page` fixture 可扩展支持页面名参数）：

```python
page = PageFactory.create(platform, "login_page", poco=poco, udid=udid)
```

## 新增共用用例

```python
@allure.epic("登录")
@allure.story("账号密码登录")
def test_login(app_page, platform):
    """声明 platform fixture 即自动双端参数化。"""
    with allure.step("输入账号并登录"):
        app_page.login("user", "pwd")
```

平台特有用例放入 `testcases/android/` 或 `testcases/ios/` 目录。

---

## 门控方法 · dump_hierarchy

> 项目约定：**没有确定要求，不使用本方法**。本节为新增页面 / 维护现有 PO 时的强制阅读内容。

### 是什么

`BasePage.dump_hierarchy(reason: str) -> dict` 是项目唯一的 UI 层级树抓取收口入口，
返回当前页面完整 poco UI 树（raw dict）。

### 门控机制

调用时 **必须** 传入非空 `reason`（`None` / `""` / 纯空格均会抛 `OperationFailedError`）。

设计动机：UI dump 是高开销、易被滥用的调试操作（每次调用都抓整棵 UI 树），
强制要求理由可以让 reviewer / 审计者一眼看清「为什么这个用例要 dump」。

### 正确用法

```python
# ✓ 密码框被弹窗遮挡，绕过可见性过滤读取文本
hierarchy = self.dump_hierarchy(
    "ChimeWifiConfigPage 密码框被系统级弹窗遮挡，"
    "绕过可见性过滤直接读取密码框文本"
)
payload = hierarchy.get("payload", hierarchy) or {}
```

### 反例

```python
# ✗ reason 为空 → 抛 OperationFailedError
self.dump_hierarchy("")

# ✗ 绕开门控直接调 poco → 视为反模式
self.poco.agent.hierarchy.dump()
```

### 何时用 / 何时不用

- **用**：常规 `poco(...).get_text()` 拿不到数据时（被遮挡、可见性过滤、未渲染）
- **不用**：常规元素查找 / 文本读取能解决时（绝大多数场景）

### 为什么用 poco 而非 uiautomator dump

`adb shell uiautomator dump` 会与 `pocoservice` 抢占 accessibility 服务
（exit 137，2026-10-09 真机验证），dump 时建议一律走 poco。

### 跨文件引用

- 现有使用方：`pages/android/add_device_flow/pages/chime_device_pairing_pages.py`（密码框被弹窗遮挡）
- 源码 docstring：`pages/base_page.py:BasePage.dump_hierarchy`

---

## 文档导航

- 上一篇：[架构说明 ←](../architecture/overview.md)
- 下一篇：[页面识别文档 →](./page-identification.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
