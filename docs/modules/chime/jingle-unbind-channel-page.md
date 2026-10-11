# 解绑设备页（jingle_unbind_channel_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleUnbindChannelPage`
（`pages/android/jingle_unbind_channel_page.py`，Activity
`JingleUnbindChannelActivity`，标题「解绑设备」）为**纯识别页**：
仅提供页面加载识别与「删除设备」按钮可见性断言。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `layout_delete` | 删除按钮容器 |
| `btn_delete` | '删除设备'（**永不点击**） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `is_delete_button_visible()` | 断言「删除设备」按钮在屏且文本正确 |

## 4. 实现要点

- **安全红线**：`btn_delete` 是解绑/删除入口，点击后进入删除
  确认流程，会破坏被测设备的绑定关系。本 PO **永不提供点击
  方法**，只做可见性断言；解绑流程不在自动化测试范围
- 页面其余仅工具栏（返回走基类 `TV_BACK`）

## 5. 真机验证记录（2026-10-11，verify2）

- `open_unbind_page` 导航 PASS
- `is_delete_button_visible` = True（按钮在屏，全程未点击）PASS

## 6. 文档导航

- 上级：[通用设置页](./jingle-general-page.md)
- 相关：[删除页面](./jingle-delete-page.md)（账号级删除，非解绑）
