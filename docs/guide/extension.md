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

## 文档导航

- 上一篇：[架构说明 ←](../architecture/overview.md)
- 下一篇：[串口测试 →](./serial.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
