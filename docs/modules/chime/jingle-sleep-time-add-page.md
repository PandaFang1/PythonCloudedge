# 添加/编辑时间段页（jingle_sleep_time_add_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleSleepTimeAddPage`
（`pages/android/jingle_sleep_time_add_page.py`，Activity
`SleepTimeAddActivity`）有两种模式：

- **添加模式**（标题「添加时间段」）：铃铛勿扰页点「添加时间段」
- **编辑模式**（标题「编辑时间段」）：点击勿扰列表项进入，多出
  右上「保存」与底部「删除计划」

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| resource-id | 文本/说明 |
|---|---|
| `tv_des` | '设置勿扰时间，设备在该时间段内不会触发响铃' |
| `start_layout` / `text_start_time` / `iv_arrow_start` | 开启时间行（'00:00'） |
| `end_layout` / `text_end_time` / `iv_arrow_end` | 结束时间行 |
| `text_week` | '重复' |
| `layout_sun_2` … `layout_sta_2` | 7 个星期项（配 `text_*_check_2`） |
| `btn_add` | 添加模式底部「保存」 |
| `tv_right_text` | 编辑模式右上「保存」 |
| `btn_delete` | 编辑模式底部「删除计划」 |
| `optionspicker` / `options_hour` / `options_min` | 时间选择器滚轮（时/分） |
| `btnCancel` / `btnSubmit` | 选择器「取消」/「确定」 |

星期定位器常量 `WEEKDAY_LOCATORS`：'日'~'六' → `layout_sun_2`~`layout_sta_2`。

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_start_time()` / `get_end_time()` | 起止时间文本 |
| `select_weekday(day)` | 勾选星期 |
| `open_start_time_picker()` / `open_end_time_picker()` | 打开时间选择器 |
| `is_time_picker_shown()` / `cancel_time_picker()` | 选择器状态/取消 |
| `scroll_picker_hour_up(times)` | 时轮向上滚动（值增加） |
| `submit_time_picker()` | 选择器「确定」 |
| `save()` | 保存（按模式选底部/右上按钮） |
| `is_edit_mode()` | 编辑模式判断 |
| `delete_plan()` | 编辑模式「删除计划」 |

## 4. 实现要点

- **滚轮限制**（重要）：滚轮数字不在 accessibility 树（自绘 View），
  只能手势滚动；**单次滚动步长不稳定**（+1 或 +2 小时）。可靠策略：
  **end 同向多滑一次，保证 end > start**
- **保存校验**：同日内 start >= end 的时段被 app 拒绝（保存后
  停留本页不返回列表）；以「是否返回勿扰列表」作为保存成功判据
- **勿扰时间段验证闭环**（真机实操）：
  1. 添加页：`select_weekday('一')` → start 滑 1 次 → end 同向滑
     2 次 → `submit_time_picker()` → `save()`
  2. 勿扰列表出现 `'01:00 ~ 02:00'` + `'星期一'`
  3. 点击列表项进编辑模式 → `delete_plan()` → 列表恢复空态
- 添加/编辑模式共用 Activity，`wait_for_page_loaded` 兼容两种标题
  （`ACCEPT_TITLES`）

## 5. 真机验证记录（2026-10-11，verify1/4/5/6）

- 起止时间读取、星期点击、选择器开/关 PASS
- 滚轮：start 滑 1 次 = 01:00，end 滑 2 次 = 02:00（同向策略）PASS
- `save()` 有效时段 → 返回勿扰列表，列表项 '01:00 ~ 02:00' PASS
- 编辑模式进入（`is_edit_mode` 标题='编辑时间段'）PASS
- `delete_plan()` → 返回列表 → 恢复空态 PASS

## 6. 文档导航

- 上级：[铃铛勿扰页](./jingle-bell-dnd-page.md)
