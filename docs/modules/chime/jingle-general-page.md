# 通用设置页（jingle_general_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleGeneralPage`（`pages/android/jingle_general_page.py`，
Activity `GeneralSettingActivity`，标题「通用设置」）提供工作
指示灯/12 小时制开关与安装指引、解绑子设备两个下级页面入口。

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| resource-id | 文本/说明 |
|---|---|
| `layout_led` / `switch_led` | 工作指示灯行 + 开关 |
| `layout_install_guide` | 「安装指引」入口 |
| `layout_jingle_unbind` | 「解绑子设备」入口 |
| `layout_time_settings` / `layout_time_setting` | 时间设置分组/行 |
| `switch_time_format` | 12 小时制开关 |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `toggle_work_led()` | 点击工作指示灯开关 |
| `toggle_time_format()` | 点击 12 小时制开关 |
| `open_install_guide_page()` | 进安装指引页（3 页翻页流） |
| `open_unbind_page()` | 进解绑设备页（仅识别，永不点删除） |

## 4. 实现要点

- **开关状态断言限制**（真机验证）：`switch_led` /
  `switch_time_format` 的 `attr("checked")` 恒 False，与模块内
  其他开关一致，PO 不提供状态读取；状态断言用截图比对
- **「设置成功」Toast**：LED 切换后的提示为系统 Toast，poco
  accessibility 树不可见，无法自动断言（切换生效以设备 LED 物理态
  或截图为准）
- 开关验证模式：**切换两次恢复原状**（真机验证均如此执行）

## 5. 真机验证记录（2026-10-11，verify2）

- `toggle_work_led` ×2、`toggle_time_format` ×2（各切换两次恢复）
  PASS
- `open_install_guide_page` + 3 页翻页全 PASS（见
  [安装指引页](./jingle-install-guide-page.md)）
- `open_unbind_page` + 删除按钮可见性断言 PASS（见
  [解绑设备页](./jingle-unbind-channel-page.md)）

## 6. 文档导航

- 下级：[安装指引页](./jingle-install-guide-page.md) ·
  [解绑设备页](./jingle-unbind-channel-page.md)
- 上级：[设置页](./jingle-setting-page.md)
