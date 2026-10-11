# 位置管理页（jingle_device_location_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceLocationPage`
（`pages/android/jingle_device_location_page.py`，Activity
`DeviceAssignmentActivity`，标题「设备分配管理」）提供家庭列表
读取、选择与确定。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `tv_right_text` | 右上角「确定」 |
| `tv_family_title` | 分组标题（'我的家庭'） |
| `tvRoomName` | 家庭名（列表项，同 id 复用） |
| `tvDeviceNumber` | 设备数（'1个设备'） |
| `iv_select` | 选择圈 |
| `layoutCreateFamily` | 底部「新建家庭」（下级页面未探测） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_family_list()` | 家庭列表 `[(名称, 设备数), ...]` |
| `select_family(name)` | 点击家庭勾选（不提交） |
| `confirm()` | 点右上角「确定」（真实写入） |

## 4. 实现要点

- 列表项 id 复用（`tvRoomName`/`tvDeviceNumber`），getter 按
  索引配对读取
- `select_family` 按文本点击；**提交需 `confirm()`**（真实写入
  设备位置分配，验证注意恢复）
- `layoutCreateFamily`（新建家庭）下级页面未探测分类，PO 暂不
  提供进入方法（常量保留）

## 5. 真机验证记录（2026-10-11，verify1）

- `get_family_list` = [('方小C的家', '1个设备')] PASS
- `select_family('方小C的家')` 点击成功（不确认）PASS

## 6. 文档导航

- 上级：[设备信息页](./jingle-device-info-page.md)
