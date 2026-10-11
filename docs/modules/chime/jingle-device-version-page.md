# 设备版本页（jingle_device_version_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceVersionPage`
（`pages/android/jingle_device_version_page.py`，Activity
`DeviceVersionActivity`，标题「设备版本」）为固件版本**只读信息页**
（固件升级类操作不在测试范围）。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `img_camera` / `tv_device_name` | 设备图标与名称 |
| `tv_current_version` | 当前固件版本（'6.2.0.20260921'） |
| `tv_latest_version` | 最新固件版本 |
| `ll_auto_update` / `switch_auto` | 固件自动升级开关（只读，不切换） |
| `tv_auto_upgrade_des` | 自动升级说明 |
| `tv_tips` | 升级提示（'您已是最新版本，无需更新'） |
| `btn_upgrade` | 底部按钮（无更新时文本='返回'） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_device_name()` / `get_current_version()` / `get_latest_version()` | 版本信息 getter |
| `get_upgrade_tip()` | 升级提示文案 |
| `get_upgrade_button_text()` | 底部按钮文本（'返回'/'检查更新'） |

## 4. 实现要点

- `switch_auto`（固件自动升级）checked 属性同样不可靠，且用户
  未要求切换，PO 只定义定位器不做操作
- `btn_upgrade` 文本随升级状态变化（当前 '返回'），getter 可用于
  升级态断言

## 5. 真机验证记录（2026-10-11，verify1）

5 个 getter 全 PASS：'131903227' / '6.2.0.20260921' /
'6.2.0.20260921' / '您已是最新版本，无需更新' / '返回'。

## 6. 文档导航

- 上级：[设备信息页](./jingle-device-info-page.md)
