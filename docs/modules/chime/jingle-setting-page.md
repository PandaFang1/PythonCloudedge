# 智能门铃 Chime Base 设置页（jingle_setting_page）

> 真机全流程验证：2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleSettingPage`（工厂页面名 `jingle_setting_page`，文件
`pages/android/jingle_setting_page.py`）是 jingle 设备设置模块的
**枢纽页**：7 个子页面入口 + 报警推送开关 + 重启/删除设备。

页面树（2026-10-11 全量补齐）：

```
JingleSettingPage（CameraSettingNewActivity，标题'设置'）
├── 设备信息卡片 → JingleDeviceInfoPage
├── 宫格（rv_top）：铃铛勿扰 / 铃声设置 / 接收报警推送(switch) / 设备分享
├── 列表（rv_main）：声音设置 / 存储管理 / 通用设置
├── btn_reset（重启设备，弹确认框）
└── btn_delete（删除设备 → 删除流程见 jingle-delete-page.md）
```

## 2. 定位器（真机 dump 验证）

| 区域 | resource-id | 文本/说明 |
|---|---|---|
| 工具栏返回 | `iv_back` | 返回 jingle 首页 |
| 标题（识别点） | `tv_title` | '设置' |
| 设备信息卡片 | `layout_device_info` | 点击进设备信息页 |
| 卡片 SN | `tv_device_name_info` | 设备昵称 |
| 卡片 WiFi | `tv_wifi` | '信号强度：100%' |
| 卡片时区 | `tv_time_zone` | '时区:GMT+08:00' |
| 宫格入口（4 项） | — | 按 tv_title 文本定位（铃铛勿扰/铃声设置/设备分享/接收报警推送） |
| 报警推送开关 | `switch_button` | 点击弹确认框（关闭方向） |
| 列表入口（3 项） | — | 按 tv_title 文本定位（声音设置/存储管理/通用设置） |
| 重启设备 | `btn_reset` | 弹系统样式确认框 |
| 删除设备 | `btn_delete` | 删除流程入口 |
| 确认弹框 | `title` / `message` / `negativeButton` / `positiveButton` | 推送/重启共用（文案不同） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `is_setting_page()` / `wait_for_page_loaded()` | 页面识别（标题='设置'） |
| `back_to_jingle_home()` | 返回 jingle 首页（Activity 断言） |
| `get_device_sn()` / `get_wifi_signal()` / `get_time_zone()` | 卡片信息 getter |
| `open_device_info_page()` … `open_general_page()` | 7 个子页面入口（点击→验证→返回实例，链式） |
| `toggle_alarm_push(confirm)` | 报警推送开关 + 确认框处理 |
| `restart_device(confirm)` | 重启设备 + 确认框处理 |

## 4. 实现要点

- **入口方法统一模式**（`_open_sub_page`）：点击 → 子页面
  `wait_for_page_loaded()`（标题 + Activity 双识别点）→ 返回实例；
  失败抛 `ElementNotFoundError`
- **宫格/列表入口按文本定位**：`{"text": "声音设置"}` 等，
  不依赖列表项 id（同一 id 复用）
- **开关 checked 不可靠**：推送开关 `attr("checked")` 恒 False
  （真机验证），不提供状态读取，状态断言以推送行为为准
- **「设置成功」Toast**：重启后提示为系统 Toast，poco accessibility
  树不可见，如需断言用截图比对
- **确认弹框双 id 体系**：推送/重启用系统样式
  （`negativeButton`/`positiveButton`），删除用自定义样式
  （`tv_cancel`/`tv_confirm`），勿混用

## 5. 真机验证记录（2026-10-11）

- 7 个 `open_xxx_page()` 全部导航成功（各子页文档有单独验证记录）
- `toggle_alarm_push`：关闭弹「是否关闭设备的消息通知？」，取消/确定
  两路径验证通过；开启不弹框直接生效
- `restart_device(confirm=False)`：弹框出现、点取消、停留设置页 ✓

## 6. 文档导航

- 子页面：[设备信息](./jingle-device-info-page.md) ·
  [铃铛勿扰](./jingle-bell-dnd-page.md) ·
  [铃声设置](./jingle-ringtone-page.md) ·
  [设备分享](./jingle-device-share-page.md) ·
  [声音设置](./jingle-sound-page.md) ·
  [存储管理](./jingle-storage-page.md) ·
  [通用设置](./jingle-general-page.md)
- 相关：[删除页面](./jingle-delete-page.md)
