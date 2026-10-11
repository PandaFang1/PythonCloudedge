# 设备使用场景页（jingle_device_scene_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceScenePage`（`pages/android/jingle_device_scene_page.py`，
Activity `DeviceSceneActivity`，标题「设备使用场景」）提供 11 个
场景标签的读取与选定（两列宫格）。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `recyclerView` | 宫格容器 |
| `tvName` | 场景标签（11 个，同 id 复用，按文本定位） |
| `tvSave` | 底部「保存」 |

全部场景（模块常量 `ALL_SCENES`）：
厨房安防 / 客厅安防 / 卧室安防 / 看老人 / 看宠物 / 看小孩 /
门口安防 / 庭院安防 / 车库安防 / 农场安防 / 门店安防

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_available_scenes()` | 可见场景标签列表 |
| `select_scene(scene)` | 点击场景（校验在 ALL_SCENES 内） |
| `save()` | 点击「保存」（真实写入） |

## 4. 实现要点

- **选中态限制**（真机验证）：`tvName` 的 `selected` 属性恒
  False，无 UI 断言依据；保存后可通过重进页面/设备信息页间接
  验证
- `select_scene` 只点击不保存；`save` 才真实写入（保存后当前
  场景变更，原场景无 UI 可读，验证时注意）
- 保存后停留在场景页（真机验证 Activity 不变），需手动返回

## 5. 真机验证记录（2026-10-11，verify1/2）

- `get_available_scenes` = 11 个场景（与 ALL_SCENES 一致）PASS
- `select_scene('看宠物')`（不保存）点击成功 PASS
- `select_scene('看宠物') + save()` 保存成功（保存后停留场景页）PASS
  （保存前原场景无 UI 可读，未恢复；测试设备保持'看宠物'）

## 6. 文档导航

- 上级：[设备信息页](./jingle-device-info-page.md)
