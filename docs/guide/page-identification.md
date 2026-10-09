# 页面识别文档 — 三大核心页面定位器速查

本文档记录 **首页 / 消息页 / 我的页** 三个核心页面在双端的页面识别点与定位器，
全部数据均来自真机验证（Android: CloudEdge / iOS: 云际），供编写和维护页面对象、用例时快速查阅。

> **双端定位器关键差异**：Android 端文本元素用 `{"text": "xxx"}` 定位、控件 ID 用
> `{"name": "com.cloudedge.smarteye:id/xxx"}` 定位；iOS 端文本挂在可访问性标签上，
> 统一用 `{"name": "xxx"}` 定位（iOS dump 中 `text` 属性为空）。

## 页面对象与页面工厂注册表

| 页面名 | Android 页面类 | iOS 页面类 | 工厂 key |
|---|---|---|---|
| 首页 | `CloudEdgeMainPage` | `YunjiMainPage` | `(platform, "main_page")` |
| 消息页 | `CloudEdgeMessagePage` | `YunjiMessagePage` | `(platform, "message_page")` |
| 我的页 | `CloudEdgeMyPage` | `YunjiMyPage` | `(platform, "my_page")` |

用例中通过 `PageFactory.create(platform, "页面名", poco=..., udid=...)` 获取对应平台页面实例。

---

## 1. 首页（main_page）

页面职责：app 启动后的主入口，提供底部 Tab 导航（首页 / 消息 / 我的）。

### 页面识别点（用于 `wait_for_page_loaded` / `is_home_page`）

| 平台 | 识别点 1（添加设备） | 识别点 2（菜单） |
|---|---|---|
| Android | `{"name": "com.cloudedge.smarteye:id/ivAddDevice"}` | `{"name": "com.cloudedge.smarteye:id/ivMenu"}` |
| iOS | `{"name": "nav home add"}` | `{"name": "nav home menu"}` |

两个识别点必须**同时存在**才判定为首页，避免单一元素误判。

### 底部 Tab 栏

| Tab | Android（text） | iOS（name） |
|---|---|---|
| 首页 | `{"text": "首页"}` | `{"name": "首页"}` |
| 消息 | `{"text": "消息"}` | `{"name": "消息"}` |
| 我的 | `{"text": "我的"}` | `{"name": "我的"}` |

### 业务方法（双端同名同义）

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点轮询等待（默认 20s，0.5s 间隔） |
| `is_home_page()` | 双识别点同时存在返回 True |
| `is_tab_visible(locator)` | 判断指定 Tab 是否可见 |
| `open_home_page()` / `open_message_page()` / `open_my_page()` | 底部 Tab 导航切换 |

### iOS 特有说明

- 首页可能出现「重要通知权限受限」弹窗（含「立即修复」按钮），不影响识别点可见性，
  如需处理可在 `handle_popups` 中扩展。
- iOS 顶部导航按钮的可访问性标识：`nav home add`（添加）、`nav home menu`（菜单）、
  `nav home feedback`（反馈）。

---

## 2. 消息页（message_page）

页面职责：消息中心，顶部以 Tab 切换「报警」/「分享」两类消息。

### 页面识别点（用于 `wait_for_page_loaded` / `is_message_page`）

| Tab | Android（text） | iOS（name） |
|---|---|---|
| 报警 | `{"text": "报警"}` | `{"name": "报警"}` |
| 分享 | `{"text": "分享"}` | `{"name": "分享"}` |

两个 Tab 同时存在即判定为消息页。

### 进入方式

从首页底部点击「消息」Tab（`main_page.open_message_page()`）。

### 业务方法（双端同名同义）

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点轮询等待 |
| `is_message_page()` | 「报警」+「分享」同时存在返回 True |
| `switch_to_alarm()` | 切换到「报警」Tab |
| `switch_to_share()` | 切换到「分享」Tab |

### iOS 特有说明

- iOS 端消息页顶部还有编辑入口：`device settiing nav edit norma`。
- 空消息列表时显示 `empty set background image` / `empty set title` 占位元素。

---

## 3. 我的页（my_page）

页面职责：个人中心，含二维码入口、功能入口列表（家庭管理 / 我的服务 / 共享 / 相册 / 设置）。

### 页面识别点（用于 `wait_for_page_loaded` / `is_my_page`）

| 平台 | 识别点 1（二维码） | 识别点 2 |
|---|---|---|
| Android | `{"name": "com.cloudedge.smarteye:id/iv_qr_code"}` | `{"name": "com.cloudedge.smarteye:id/feedback"}`（意见反馈） |
| iOS | `{"name": "img me qrcode"}` | `{"name": "img me scan"}`（扫一扫） |

> iOS 端我的页**无独立 feedback 入口**，以顶部「扫一扫」按钮作为第二识别点，
> 双端识别点数量保持一致（各 2 个）。

### 功能入口

| 入口 | Android（text） | iOS（name） |
|---|---|---|
| 家庭管理 | `{"text": "家庭管理"}` | `{"name": "家庭管理"}` |
| 我的服务 | `{"text": "我的服务"}` | `{"name": "我的服务"}` |
| 共享 | `{"text": "共享"}` | `{"name": "共享"}` |
| 相册 | `{"text": "相册"}` | `{"name": "相册"}` |
| 设置 | `{"text": "设置"}` | `{"name": "设置"}`（iOS 未在首屏 dump 中出现，待验证） |

### 进入方式

从首页底部点击「我的」Tab（`main_page.open_my_page()`）。

### 业务方法（双端同名同义）

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点轮询等待 |
| `is_my_page()` | 双识别点同时存在返回 True |
| `is_item_visible(locator)` | 判断指定功能入口是否可见 |
| `open_settings()` | 点击「设置」入口 |

### iOS 特有说明

- iOS 端我的页顶部还有扫一扫按钮 `img me scan`、头像昵称 / 邮箱（账号信息）等元素。
- iOS 端「设置」入口未在首屏 dump 中出现，可能在列表更下方，定位器标记为待验证。

---

## 附：导航链路（已双端真机验证）

```
首页 ──Tab「消息」──> 消息页（报警/分享）
  ↑                      │
  │                   Tab「首页」
  └──────────────────────┘
首页 ──Tab「我的」───> 我的页（二维码/反馈 或 二维码/扫一扫）
  ↑                      │
  │                   Tab「首页」
  └──────────────────────┘
```

对应用例：`testcases/test_app_lifecycle.py` 中的 `TestTabNavigation`
（`test_switch_to_message_and_back` / `test_switch_to_my_and_back`），
双端真机验证结果：8/8 通过（Android 4 + iOS 4）。

## 附：新增页面时的定位器采集方法

1. **Android**：连接设备后通过 `poco.dump()` 或 `adb shell uiautomator dump` 获取控件树，
   取 `resource-id`（写入 `{"name": "..."}`）或文本（写入 `{"text": "..."}`）。
2. **iOS**：连接 WDA 后通过 `poco.dump()` 获取控件树，取可访问性标签 `name`
   （写入 `{"name": "..."}`）；注意 iOS 的 `text` 属性通常为空。
3. 每个页面选取 **2 个稳定且页面特有的元素**作为识别点，更新到本文档与对应页面对象。

---

## 文档导航

- 上一篇：[扩展指南 ←](./extension.md)
- 下一篇：[串口测试 →](./serial.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
