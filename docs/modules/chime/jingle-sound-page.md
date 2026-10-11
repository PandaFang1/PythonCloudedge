# 声音设置页（jingle_sound_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleSoundPage`（`pages/android/jingle_sound_page.py`，
Activity `SoundSettingActivity`，标题「声音设置」）提供扬声器
开/关与音量滑条设置（1-100）。

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| resource-id | 文本/说明 |
|---|---|
| `layout_sound_speaker` | 扬声器行 |
| `switch_sound_speaker` | 扬声器开关（checked 属性不可靠） |
| `layout_speaker_volume` | 音量行 |
| `sb_volume` | 音量滑条（扬声器关时隐藏） |
| `tv_volume` | 音量数值（1-100，如 '62'） |
| `tv_2` | '双向音频，录制声音和声音报警也将被禁用' |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `is_speaker_on()` | 扬声器状态（音量条可见 = 开） |
| `toggle_speaker()` / `turn_on_speaker()` / `turn_off_speaker()` | 开关操作（带状态收敛等待） |
| `get_volume()` | 读音量数值 |
| `set_volume(value, steps=15)` | 事件序列拖动音量滑条（1-100） |

## 4. 实现要点（本页为全模块自动化难度最高，细节务必阅读）

- **扬声器状态判断**：`switch_sound_speaker` 的
  `attr("checked")` 恒 False（真机验证，与推送/LED 开关一致），
  改用 **`sb_volume` 可见性**：开 = 音量条在屏；关 = 音量条整体
  隐藏（poco 查询 `Cannot find`）
- **音量拖动方案**（多方案对比后确定）：
  - `poco.swipe` / `adb input swipe`：表现为「文本不变」——实际
    生效但无法当场确认（见下条），且稳定性存疑
  - **最终方案：airtest 底层触摸事件序列**
    `DownEvent → 15+ 个 MoveEvent → UpEvent`，从当前音量对应的
    thumb 位置拖到目标位置（坐标由 `sb_volume` 运行时几何 +
    `get_current_resolution()` 换算像素，不硬编码）
- **`tv_volume` 不实时刷新**（重要坑）：拖动后文本不变，需
  **退出重进页面**才能读到新值。用例验证模式：
  `set_volume(40)` → `back_to_setting_page()` → 重新
  `open_sound_page()` → `get_volume()`
- **精度误差 ±2**：目标 60 实际 62、目标 40 实际 39（像素取整 +
  thumb 命中偏移），断言用区间（±2）
- **前置约束**：`set_volume` 要求扬声器为开（关则滑条不存在，
  抛 `OperationFailedError`）；`turn_off` 后双向音频/声音报警
  同时禁用（`tv_2` 文案）

## 5. 真机验证记录（2026-10-11，verify2）

- `is_speaker_on`（初始开）→ `turn_off_speaker`（False）→
  `turn_on_speaker`（True）全 PASS
- `get_volume` = 62 PASS
- `set_volume(40)` → 重进 → 实际 39（38~42 区间内）PASS
- 恢复原音量：重进后 63（62±2）PASS

## 6. 文档导航

- 上级：[设置页](./jingle-setting-page.md)
