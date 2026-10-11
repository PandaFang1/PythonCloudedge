# 设备名称页（jingle_device_name_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceNamePage`（`pages/android/jingle_device_name_page.py`，
Activity `DeviceNameActivity`，标题「设备昵称」）提供设备昵称的
读取与修改（清空→输入→保存）。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `edt_device_name` | 名称输入框（当前昵称） |
| `img_delete` | 清空输入按钮 |
| `tv_right_text` | 右上角「保存」 |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_name()` | 读当前昵称 |
| `set_name(name, save=True)` | 清空 → 输入 → 保存（链式） |

## 4. 实现要点

- **真实写入**：`save=True` 点击右上角「保存」修改设备昵称；
  验证后须恢复原昵称（真机验证即「改→验证→改回」闭环）
- 验证模式：`set_name('新名')` → 返回重进 → `get_name()` 断言
- `img_delete` 一键清空输入框，避免逐字删除

## 5. 真机验证记录（2026-10-11，verify1）

- `get_name` = '131903227' PASS
- `set_name('PO验证昵称', save=True)` → 重进后 = 'PO验证昵称' PASS
- 恢复原昵称 → 重进后 = '131903227' PASS

## 6. 文档导航

- 上级：[设备信息页](./jingle-device-info-page.md)
