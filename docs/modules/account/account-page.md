# 我的信息页面文档 — Android（CloudEdge）· 退出登录

本文档记录 **CloudEdge 安卓端「我的信息」页（MyInformationActivity）** 及其
**退出登录确认弹窗**的页面识别点、控件定位器与业务方法，供编写和维护页面对象、
用例时快速查阅。

> **范围说明**：本文档仅覆盖 Android（CloudEdge）端，iOS（云际）端对应页面待补齐。
>
> **数据来源**：定位器全部基于真机 poco dump 验证（udid=`cfed8c100822`，Redmi /
> MIUI，屏幕分辨率 1080×2400），并由用例 `testcases/android/test_logout.py`、
> `testcases/android/test_account_switch.py`（账号切换）真机验证通过。

---

## 页面对象与页面工厂注册表

| 页面名 | Android 页面类 | iOS 页面类 | 工厂 key |
|---|---|---|---|
| 我的信息页 | `CloudEdgeAccountPage` | _(待实现)_ | `(android, "account_page")` |

用例中通过 `PageFactory.create("android", "account_page", poco=..., udid=...)`
获取页面实例。

```python
from pages.page_factory import PageFactory

account_page = PageFactory.create("android", "account_page", poco=poco, udid=udid)
account_page.wait_for_page_loaded()
account_page.logout(confirm=True)
```

---

## 1. 页面职责

「我的信息」页（账号设置页）承担以下职责：

1. 展示与编辑账号资料：头像、账号（邮箱）、昵称、国家/地区
2. 账号安全入口：修改密码
3. 二维码入口：我的二维码
4. **退出登录**：底部按钮，点击后弹出确认弹窗

进入路径：**「我的」页 → 账号入口 `tv_account`（显示账号邮箱）**；
返回路径：左上角返回键 `iv_back`，或退出登录确认后自动回登录页。

页面元素概览（从上到下）：

```
┌─────────────────────────────┐
│ ←      我的信息              │  ← tool_bar / tv_title
│ 头像图片              头像名片 > │  ← profile_photo_layout
│ 账号        358632847@qq.com > │  ← layout_account / tv_account
│ 昵称              小小C     > │  ← nickname_layout / tv_nickname
│ 修改密码                    > │  ← reset_password_layout
│ 国家/地区           美国     > │  ← region_layout / tv_region
│ 我的二维码                  > │  ← qr_code_layout
│            ⋮                │
│        ┌──────────┐         │
│        │  退出登录  │         │  ← logout_layout（底部按钮）
│        └──────────┘         │
└─────────────────────────────┘
```

---

## 2. 页面识别点（用于 `wait_for_page_loaded` / `is_account_page`）

| 识别点 | Android 定位器（resource-id） |
|---|---|
| 页面标题「我的信息」 | `{"name": "com.cloudedge.smarteye:id/tv_title"}` |
| 退出登录按钮 | `{"name": "com.cloudedge.smarteye:id/logout_layout"}` |

**两个识别点必须同时存在**才判定为「我的信息」页。

选择依据：

- `tv_title` 为页面标题栏文本（「我的信息」），`logout_layout` 为本页独有的
  退出登录按钮，其他页面不会同时出现这两个元素，可唯一判定
- 建议叠加系统级判定：前台 Activity 为
  `com.ppstrong.weeye.view.activity.user.MyInformationActivity`

---

## 3. 控件定位器

### 3.1 工具栏 / 账号资料

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 工具栏 | `{"name": "com.cloudedge.smarteye:id/tool_bar"}` | 标题栏容器 |
| 返回键 | `{"name": "com.cloudedge.smarteye:id/iv_back"}` | 返回「我的」页 |
| 账号文本 | `{"name": "com.cloudedge.smarteye:id/tv_account"}` | 当前登录账号（如 `358632847@qq.com`）|
| 账号标签 | `{"name": "com.cloudedge.smarteye:id/tv_account_title"}` | 固定文案「账号」|
| 修改密码 | `{"name": "com.cloudedge.smarteye:id/reset_password_layout"}` | 跳转找回/修改密码流程 |
| 国家/地区行 | `{"name": "com.cloudedge.smarteye:id/region_layout"}` | 展示当前国家（如「美国」）|

### 3.2 退出登录按钮

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 退出登录 | `{"name": "com.cloudedge.smarteye:id/logout_layout"}` | 页面底部主按钮，`text` 为「退出登录」|

### 3.3 退出登录确认弹窗

点击「退出登录」后弹出的系统风格对话框：

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 弹窗标题 | `{"name": "com.cloudedge.smarteye:id/title"}` | 固定文案「提示」|
| 弹窗内容 | `{"name": "com.cloudedge.smarteye:id/message"}` | 文案：**退出后不会删除任何历史数据，下次登录仍然可以使用本账号** |
| 取消按钮 | `{"name": "com.cloudedge.smarteye:id/negativeButton"}` | 文案「取消」，关闭弹窗停留在本页 |
| 确定按钮 | `{"name": "com.cloudedge.smarteye:id/positiveButton"}` | 文案「确定」，退出登录回到登录页 |

> 按钮可点击 `negativeButton` / `positiveButton` 文本控件本身，
> 对应的 `_layout` 容器亦可点击。

---

## 4. 业务方法

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点（`tv_title` + `logout_layout`）轮询等待（默认 20s）|
| `is_account_page()` | 双识别点同时存在返回 True |
| `get_account()` | 读取账号文本（如 `358632847@qq.com`）|
| `click_logout()` | 点击底部「退出登录」按钮，唤起确认弹窗 |
| `is_logout_dialog_visible(timeout)` | 以 `message` 控件出现判定弹窗可见 |
| `cancel_logout()` | 点击弹窗「取消」，停留在「我的信息」页 |
| `confirm_logout()` | 点击弹窗「确定」，确认退出登录 |
| `wait_back_to_login(timeout)` | 等待前台 Activity 切回 `LoginActivity`（系统级判定）|
| `logout(confirm=True)` | **一站式入口**：点击退出登录 → 弹窗中选「确定 / 取消」并完成断言 |

`logout(confirm=False)` 断言弹窗已关闭且停留在本页；`logout(confirm=True)`
断言回到登录页（Activity 判定）。

### 「我的」页侧的入口方法

`CloudEdgeMyPage`（`pages/android/my_page.py`）提供：

| 方法 | 定位器 | 说明 |
|---|---|---|
| `open_account_page()` | `{"name": "com.cloudedge.smarteye:id/tv_account"}` | 从「我的」页点击账号入口，跳转「我的信息」页 |

---

## 5. Android 特有说明

- **入口点击时序**：登录成功后立即点击 `tv_account` 偶发不跳转（页面尚未完成
  渲染/Fragment 未就绪）。用例中采用 **Activity 判定 + 重试**（最多 3 次），
  详见 `testcases/android/test_logout.py` 的 `_wait_for_activity`。
- **退出成功判定**：确认退出后 app 结束 `MainActivity` 回到 `LoginActivity`，
  用 `BasePage.get_current_activity()` 判定比 Poco DOM 更稳定（部分机型
  Poco dump 与实际页面存在差异/延迟）。
- **弹窗按钮文案**：确定/取消按钮的 `text` 为「确定」「取消」，与 MIUI 系统
  权限弹窗的「始终允许 / 仅在使用中允许」不同，注意区分。
- **退出后登录页预填**：登录时勾选了「记住密码」，退出登录后账号/密码框会
  **预填上一账号的账号与密码明文**，国家/地区保持上次选择（如「美国」）。
  真机验证 poco `set_text` 为**替换行为**，直接输入新账号即可覆盖，无需清空
  （账号切换用例 `testcases/android/test_account_switch.py` 已验证）。

---

## 6. 用法示例

### 6.1 一站式退出登录（推荐）

```python
from pages.page_factory import PageFactory

def test_logout(poco, udid):
    my_page = PageFactory.create("android", "my_page", poco=poco, udid=udid)
    account_page = PageFactory.create("android", "account_page", poco=poco, udid=udid)

    my_page.open_account_page()               # 我的页 → 我的信息页
    assert account_page.wait_for_page_loaded(timeout=15)

    account_page.logout(confirm=True)         # 退出登录 → 确定 → 回登录页
```

完整可运行用例见 `testcases/android/test_logout.py`
（登录 → 我的页 → 我的信息页 → 取消退出 → 确认退出，含真机前置处理），运行方式：

```bash
python run.py --platform android -k test_login_then_logout
```

### 6.2 分步调用（自定义流程时）

```python
# 1. 点击「退出登录」
account_page.click_logout()

# 2. 断言弹窗出现
assert account_page.is_logout_dialog_visible()

# 3. 取消（停留本页）或确定（回登录页）
account_page.cancel_logout()
# account_page.confirm_logout()
# assert account_page.wait_back_to_login(timeout=30)
```

### 6.3 账号切换：退出登录 → 登录另一账号

退出登录后「记住密码」会预填上一账号，直接以新国家/新账号调用
`login_with_region` 即可完成切换（poco `set_text` 为替换行为，自动覆盖预填）：

```python
# 账号 A（美国区）登录
login_page.login_with_region("美国", "a@example.com", "pwdA", remember_password=True)

# 退出登录（我的页 → 账号入口 → 退出登录 → 确定）
my_page.open_account_page()
account_page.logout(confirm=True)
assert login_page.wait_for_page_loaded(timeout=20)

# 账号 B（中国区）登录：选国家「中国」+ 新账号（覆盖预填）
login_page.login_with_region("中国", "b@example.com", "pwdB", remember_password=True)

# 验证切换生效：「我的」页账号文本已变为 B 账号
main_page.open_my_page()
assert my_page.get_account() == "b@example.com"
```

完整可运行用例见 `testcases/android/test_account_switch.py`
（美国账号 `358632847@qq.com` 登录 → 退出 → 中国账号 `ceshi011@qq.com` 登录），
运行方式：

```bash
python run.py --platform android -k test_switch_account
```

---

## 文档导航

- 上一篇：[登录页 ←](./login-page.md)
- 下一篇：[选择设备类别页 →](../device_mgmt/add-device-category-page.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
