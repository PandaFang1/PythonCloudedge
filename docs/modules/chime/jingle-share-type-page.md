# 分享方式页（jingle_share_type_page）

> 真机全流程验证：2026-10-11（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 概述

`JingleShareTypePage`（`pages/android/jingle_share_type_page.py`，
Activity `ShareTypeActivity`，标题「设备分享」——与父页同标题，
靠 Activity 关键字区分）提供两种分享方式的识别与读取。

## 2. 定位器（真机 dump 验证）

| resource-id | 文本/说明 |
|---|---|
| `tv_qr_code_share` | 方式一容器（`iv_icon` + `tv_title` + `iv_pro_check`） |
| `tv_title` | 方式一标题 '扫描二维码'（**与工具栏标题撞 id**） |
| `tv_account_share` | 方式二容器（`iv_icon_2` + `tv_title_2`） |
| `tv_title_2` | 方式二标题 '输入账号' |
| `swipe_refresh_layout` / `ll_empty` | 最近联系人区（空态 '暂无联系人'） |

## 3. 方法速查

| 方法 | 说明 |
|---|---|
| `get_share_types()` | 分享方式标题列表（['扫描二维码','输入账号']） |
| `is_recent_contact_empty()` | 最近联系人空态判断 |

## 4. 实现要点

- **`tv_title` 撞 id 坑**（真机验证发现）：方式一标题 id 与工具栏
  标题同为 `tv_title`，poco 按 name 匹配先命中工具栏（返回
  '设备分享'）。`get_share_types` 中方式一改用**文本匹配**断言
- 点击两种方式会进入更深层页面（二维码页/账号输入页），该层级
  未探测分类，PO 暂不提供进入方法
- 双识别点：标题「设备分享」+ `ShareTypeActivity`（标题与父页
  相同，Activity 是唯一区分）

## 5. 真机验证记录（2026-10-11，verify2）

- `get_share_types` = ['扫描二维码', '输入账号'] PASS（撞 id 修复后）
- `is_recent_contact_empty` = True PASS

## 6. 文档导航

- 上级：[设备分享页](./jingle-device-share-page.md)
