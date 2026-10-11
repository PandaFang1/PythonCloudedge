# 铃声设置页（jingle_ringtone_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleRingtonePage`（`pages/android/jingle_ringtone_page.py`，
Activity `SoundLightAlarmDingActivity`，标题「铃声设置」）提供默认
音频列表读取/选定、底部按住录制自定义铃声、录制完成弹框（命名/
取消/保存）、自定义铃声删除。

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| 区域 | resource-id | 文本/说明 |
|---|---|---|
| 音频列表 | `rv_sound_list` | 容器 |
| 音频名称 | `tv_sound_title` | '音频1'/'音频2'/'音频3'（+自定义项） |
| 播放按钮 | `iv_play` | 每项左侧 |
| 选中图标 | `iv_check` | 每项右侧（选中态无属性差异） |
| 删除按钮 | `iv_delete` | **仅自定义铃声项**有 |
| 说明 | `tv_setting_des` | '*所选音效用于Chime Base声音播放' |
| 录制容器 | `ll_record` / `iv_center` | 底部录制按钮 |
| 录制提示 | `tv_record_tips` | '按住按钮录制铃声' |
| 弹框-标题 | `title` | '提示' |
| 弹框-提示 | `message_tip` | '设置报警铃声的名称' |
| 弹框-输入 | `message` | 铃声名称输入区 |
| 弹框-取消 | `negativeButton` | '取消' |
| 弹框-保存 | `positiveButton` | '确定' |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_ringtone_list()` | 音频名称列表（如 ['音频1','音频2','音频3']） |
| `select_ringtone(name)` | 点击音频名选定 |
| `delete_ringtone(name)` | 删除自定义铃声（按行 y 对齐定位 iv_delete） |
| `record_ringtone(seconds, name, save)` | 按住录制 + 弹框处理 |
| `is_record_tip_shown()` | 录制提示文案在屏 |

## 4. 实现要点

- **长按录制**：poco 同点 `swipe` 模拟（`duration` 即按住时长，
  上限 6s）；`iv_center` 位置运行时读取，不硬编码
- **短按（<1s）**：app 提示「录音时间短，请重新录制」为系统
  Toast，poco accessibility 树**不可见**，无法自动断言（PO 在
  `seconds<1` 时跳过弹框等待并记录日志）
- **录制完成弹框**：`seconds>=1` 松手后出现；`save=True` 点
  `positiveButton` 真实保存（列表新增一项），`save=False` 点
  `negativeButton` 不保存
- **删除定位**：`iv_delete` 只在自定义项上存在且与默认项索引错位，
  `delete_ringtone` 按 `tv_sound_title` 与 `iv_delete` 的**行 y 坐标
  对齐**（±0.02）找到同项删除按钮
- **选中态限制**：`iv_check` 无属性差异（三节点恒 visible），
  选定效果断言依赖播放行为或人工

## 5. 真机验证记录（2026-10-11，verify2/3）

- `get_ringtone_list` = ['音频1','音频2','音频3'] PASS
- `select_ringtone('音频2')` 点击成功 PASS
- `record_ringtone(0.3)`：无弹框（短按路径）PASS
- `record_ringtone(3.0, 'PO取消路径', save=False)`：弹框出现→取消→
  列表不变 PASS
- `record_ringtone(3.0, 'PO测试铃声', save=True)`：列表新增
  'PO测试铃声'（4 项）PASS
- `delete_ringtone('PO测试铃声')`：删除后恢复 3 项 PASS

## 6. 文档导航

- 上级：[设置页](./jingle-setting-page.md)
