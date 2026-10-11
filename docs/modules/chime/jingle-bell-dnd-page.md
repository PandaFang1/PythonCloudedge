# 铃铛勿扰页（jingle_bell_dnd_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleBellDndPage`（`pages/android/jingle_bell_dnd_page.py`，
Activity `SleepTimeListActivity`，标题「铃铛勿扰」）管理勿扰时间段
列表：空态判断 + 添加入口 + 点击列表项进编辑模式。

## 2. 定位器（真机 dump 验证 2026-10-11）

| resource-id | 文本/说明 |
|---|---|
| `tv_jingle_des` | '开启勿扰模式后，中继铃铛及其子设备将停止推送事件消息…' |
| `layout_time_list` | 时间段列表容器 |
| `empty_view` | 空态容器（配无 id 文本 '当前暂无时间段'） |
| `layout_bottom_view` / `btn_add` | 底部「添加时间段」 |
| 列表项 | 无 id，按时间文本定位（如 '01:00 ~ 02:00'） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_description()` | 读勿扰说明文案 |
| `is_time_list_empty()` | 空态判断（empty_view + 空态文本） |
| `open_sleep_time_add_page()` | 进添加时间段页（添加模式） |
| `open_sleep_time_edit_page(item_text)` | 点击列表项进编辑模式（删除入口） |

## 4. 实现要点

- 列表项无 resource-id，按时间文本定位
  （如 `open_sleep_time_edit_page("01:00 ~ 02:00")`）
- **验证勿扰时间段闭环**：添加页保存 → 列表出现项 →
  点击项进编辑模式 → 「删除计划」恢复空态（见
  [添加时间段页](./jingle-sleep-time-add-page.md)）

## 5. 真机验证记录（2026-10-11，verify1/4/6）

- `get_description` / `is_time_list_empty`（空态 True）PASS
- `open_sleep_time_add_page` PASS
- 保存时间段后列表显示 '01:00 ~ 02:00' + '星期一'，非空 PASS
- 编辑模式删除后列表恢复空态 PASS

## 6. 文档导航

- 下级：[添加时间段页](./jingle-sleep-time-add-page.md)
- 上级：[设置页](./jingle-setting-page.md)
