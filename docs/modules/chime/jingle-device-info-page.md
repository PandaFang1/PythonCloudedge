# 设备信息页（jingle_device_info_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleDeviceInfoPage`（`pages/android/jingle_device_info_page.py`，
Activity `DeviceInfoActivity`，标题「设备信息」）提供设备基础信息
**只读 getter** 与 4 个下级页面入口。

## 2. 定位器（真机 dump 验证 2026-10-11）

| 字段 | resource-id | 当前值示例 |
|---|---|---|
| 设备昵称 | `tv_device_name` | '131903227' |
| SN | `tv_sn` | 'ppsb0f8fd64b303b45d9' |
| 位置管理值 | `tv_room_name` | '方小C的家' |
| WiFi 名称 | `tv_wifi_name2` | 'xiaoMI-楼顶拷机IPC' |
| 信号强度 | `tv_signal_strength` | '100%' |
| IP | `tv_ip` | '192.168.50.237' |
| MAC 地址 | `tv_mac` | '1c:4e:a2:15:1a:c9' |
| 时区 | `tv_time_zone` | 'Asia/Shanghai' |
| 设备平台 | `tv_platform` | 'T411E' |
| WiFi 频段 | `tv_f` | '2.4G' |
| 设备版本 | `tv_version` | '6.2.0.20260921' |
| 入口-设备名称 | `layout_device_name` | → 设备名称页 |
| 入口-使用场景 | `layout_device_scene` | → 使用场景页 |
| 入口-位置管理 | `layout_location_manager` | → 位置管理页 |
| 入口-设备版本 | `layout_firmware_version` | → 设备版本页 |

## 3. 方法速查

- getter ×11：`get_device_name()` / `get_sn()` / `get_room_name()` /
  `get_wifi_name()` / `get_signal_strength()` / `get_ip()` / `get_mac()` /
  `get_time_zone()` / `get_platform()` / `get_wifi_band()` / `get_version()`
- 入口 ×4：`open_device_name_page()` / `open_device_scene_page()` /
  `open_location_manager_page()` / `open_device_version_page()`

## 4. 实现要点

- 字段标签多为**无 id 的 TextView**（如 'SN'/'信号强度'），值才有 id；
  getter 只依赖值节点
- 入口导航模式与设置页一致（`_open_next_page`：点击→双识别点验证→
  返回实例）
- `tv_wifi_name2` / `tv_f` 带 `2`/`f` 后缀，与其他页同名控件区分，
  勿与设置页卡片 `tv_wifi` / `tv_time_zone` 混淆

## 5. 真机验证记录（2026-10-11，verify1）

11 个 getter 全部 PASS（值见上表），4 个入口导航全部 PASS。

## 6. 文档导航

- 下级页面：[设备名称](./jingle-device-name-page.md) ·
  [使用场景](./jingle-device-scene-page.md) ·
  [位置管理](./jingle-device-location-page.md) ·
  [设备版本](./jingle-device-version-page.md)
- 上级：[设置页](./jingle-setting-page.md)
