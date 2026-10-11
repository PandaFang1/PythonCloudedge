# 安装指引页（jingle_install_guide_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleInstallGuidePage`
（`pages/android/jingle_install_guide_page.py`）封装**3 页翻页流**：

| 页 | Activity | 标题 | 内容 |
|---|---|---|---|
| 1 | `GuideRightPlacePicActivity`（识别页） | '安装指引' | viewPager 轮播 + 指引文案 |
| 2 | `GuideRightPlaceActivity` | '安装指引' | 无线铃铛放置指引 |
| 3 | `NetworkDiagnosticActivity` | '网络诊断' | WiFi 信号诊断结论 |

## 2. 定位器（真机 dump + 行为验证 2026-10-11）

| 页 | resource-id | 文本/说明 |
|---|---|---|
| 1 | `viewPager` / `iv_guide` / `indicator` | 轮播容器/指引图/页指示器 |
| 1 | `tv_content` | 指引文案 |
| 1 | `tv_next_vp` | '下一步'（**仅第 1 页**） |
| 2/3 | `layout_next` / `next` | 下一步按钮（第 3 页文本='完成'） |
| 2 | `iv_install_guide` / `iv_sound_img` / `tv_des_title` | 指引图/文案 |
| 3 | `iv_wifi_strength` / `tv_desc_wifi_strength` | 信号图标/值（'强'） |
| 3 | `tv_des_title` / `tv_desc_content` | 'WIFI信号强度'/诊断结论 |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_guide_content()` | 当前页指引文案（自动适配 p1/p2-3 定位器） |
| `next_page()` | 翻页（第 1 页 `tv_next_vp`，第 2/3 页 `next`） |
| `is_last_page()` | 末页判断（按钮文本='完成'） |
| `get_wifi_strength()` | 第 3 页信号值（'强'） |
| `get_diagnostic_conclusion()` | 第 3 页诊断结论 |

## 4. 实现要点

- **末页保护**：第 3 页按钮文本为「完成」，点击会触发安装完成/
  后续流程——`next_page()` 在末页抛 `OperationFailedError` 拦截
  （真机验证拦截生效）
- **翻页按钮 id 变化**：第 1 页是 `tv_next_vp`，第 2/3 页是
  `next`，`next_page` 自动适配
- 第 3 页 Activity 与标题均变（'网络诊断'），页面识别只保证
  第 1 页（`GuideRightPlacePicActivity`）；翻页后靠按钮/文案
  定位器操作

## 5. 真机验证记录（2026-10-11，verify2）

- `open_install_guide_page` + 第 1 页文案
  （'将Chime Base安装在路由器和门铃…'）PASS
- 翻至第 2 页（'将无线铃铛和智能手机放在要安装…'）PASS
- 翻至第 3 页：`is_last_page`=True、信号='强'、结论=
  '当前位置不错，可以安装无线铃铛。' PASS
- 末页 `next_page()` 抛异常拦截「完成」PASS

## 6. 文档导航

- 上级：[通用设置页](./jingle-general-page.md)
