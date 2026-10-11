# 设备分享页（jingle_device_share_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceSharePage`（`pages/android/jingle_device_share_page.py`，
Activity `DeviceSettingShareActivity`，标题「设备分享」）提供分享
添加入口，进入分享方式页。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `layoutAdd` | 「添加」入口 → 分享方式页 |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `is_add_entry_visible()` | 断言「添加」入口在屏 |
| `open_share_type_page()` | 点击进入分享方式页（链式） |

## 4. 实现要点

- 页面含未分享提示 / 分享视频引导静态文案（骨架期验证），
  分享列表数据依赖账号分享操作，暂无 getter
- 入口导航模式与设置页一致（点击→双识别点验证→返回实例）

## 5. 真机验证记录（2026-10-11，verify1/2）

- `is_add_entry_visible` PASS；`open_share_type_page` PASS
- 分享方式标题 = ['扫描二维码', '输入账号'] PASS（见
  [分享方式页](./jingle-share-type-page.md)）

## 6. 文档导航

- 下级：[分享方式页](./jingle-share-type-page.md)
- 上级：[设置页](./jingle-setting-page.md)
