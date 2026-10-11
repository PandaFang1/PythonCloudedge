# 存储管理页（jingle_storage_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleStoragePage`（`pages/android/jingle_storage_page.py`，
Activity `SdCardActivity`，标题「存储管理」）提供存储卡容量信息
getter 与格式化弹框（**只走取消路径**）。

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| resource-id | 文本/说明 |
|---|---|
| `tv_sdcard` | '存储卡容量' |
| `tv_progress_percent` | 占用百分比（'27%'） |
| `tv_capacity` | 容量大小（'59.464G'） |
| `tv_remaining_capacity` | 剩余容量（'43.549G'） |
| `tv_warning` | '警告：请备份所有重要数据。格式化将清除SD卡上的所有数据' |
| `btn_format` | '格式化'（页面下方，首屏可能需上滑） |
| 弹框 `title` | '提示' |
| 弹框 `message` | 警告文案 |
| 弹框 `negativeButton` | '取消' |
| 弹框 `positiveButton` | '确定'（**永不点击**） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_capacity_percent()` / `get_capacity_total()` / `get_capacity_remaining()` | 容量信息 getter |
| `is_sdcard_present()` | 存储卡信息在屏判断 |
| `click_format_and_cancel()` | 点格式化 → 确认弹框 → 点取消 |

## 4. 实现要点

- **安全红线**：格式化确认弹框的 `positiveButton`（'确定'）**永不
  点击**——会清除 SD 卡全部数据。PO 只提供 `click_format_and_cancel`
  一条路径；如未来需要真实格式化用例，必须人工评审后另行添加
- **格式化按钮可能屏外**：`btn_format` 在页面下方，首屏 dump 可能
  不可见；`_ensure_format_button_visible` 实现为「上滑最多 3 屏 →
  可见即点击」
- **弹框判定**：`title` 文本='提示' 且 `negativeButton` 在屏双条件，
  10s 内轮询；取消后等待弹框消失再返回

## 5. 真机验证记录（2026-10-11，verify2）

- `is_sdcard_present` PASS（有卡）
- 三个容量 getter：'27%' / '59.464G' / '43.549G' PASS
- `click_format_and_cancel`：弹框出现 → 取消 → 消失 PASS
  （`positiveButton` 全程未点击）

## 6. 文档导航

- 上级：[设置页](./jingle-setting-page.md)
