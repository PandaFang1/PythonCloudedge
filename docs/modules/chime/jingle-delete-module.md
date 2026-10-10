# Jingle 删除模块 — 智能门铃 Chime Base 端到端删除

> 真机全流程验证：2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK，SN 131805981）

## 1. 模块概述

**Jingle 删除模块**（`testcases/android/jingle_delete/`）聚合 CloudEdge 安卓端
智能门铃（Chime Base）删除的端到端测试。该模块依赖 `jingle_add` 模块的输出
（删除前需先有设备在账号中），二者构成「添加 → 删除」完整生命周期。

```
Jingle 删除模块的 1 条路径
└── test_delete.py  → 主页点 SN → 设置 → 删除设备 → 确认 → 主页断言无 SN
```

## 2. 包含的测试用例

| 测试函数 | allure 标签 | 验证内容 |
|---|---|---|
| `test_delete_doorbell_chime` | epic=设备, feature=删除设备, story=智能门铃 Chime Base 删除流程 | 主页前置断言含 SN → 一站式删除 → 主页断言不含 SN |

### 2.1 删除流程（5 个阶段，真机逐步验证）

| # | 阶段 | Activity | 操作 | 关键 resource-id |
|---|---|---|---|---|
| 1 | jingle 首页 | `JingleBaseActivity` | 主页**点击设备 SN**（Chime Base 条目名）进入；页面识别点=3 元素同时存在（`tv_title` 文本=SN **+** `iv_state_on` 设备状态图标 **+** `switch_btn_schedules` 日程开关） | `tvJingleNeutralName`（主页条目）/ `tv_title`（jingle 首页标题=SN）/ `iv_state_on` / `switch_btn_schedules` |
| 2 | 设置页 | `CameraSettingNewActivity` | 点击**右上角设置按钮**；页面识别点=标题「设置」 | `iv_submit`（右上角设置）/ `tv_title`（'设置'） |
| 3 | 设置页下滑 | 同上 | **向下滑动**直至「删除设备」按钮可见，点击 | `btn_delete`（'删除设备'） |
| 4 | 删除确认弹框 | 同上（Dialog） | 比对弹框描述 → 点击「**删除**」 | `tv_ai_search_title`（'温馨提示'）/ `tv_ai_search_des`（'确定要删除该设备和子设备及所关联的数据？'）/ `tv_confirm`（'删除'） |
| 5 | 主页断言 | `MainActivity` | 点「删除」后 app **自动返回主页**；断言设备列表**不含**该 SN | `tvJingleNeutralName` / `tvCameraName`（经 `get_device_list()` 轮询） |

## 3. 模块目录结构

```
testcases/android/jingle_delete/
├── __init__.py             # 子包标识 + 模块说明
├── conftest.py             # 模块 fixture：jingle_main_with_target
└── test_delete.py          # 端到端删除测试
```

## 4. 依赖的 Page Objects

| 页面类 | 工厂 key | 职责 |
|---|---|---|
| `CloudEdgeLoginPage` | `("android", "login_page")` | 启动/登录（如需兜底） |
| `CloudEdgeMainPage` | _(直接构造)_ | 主页（设备列表 + 设备点击） |
| `JingleDeletePage` | `("android", "jingle_delete_page")` | Jingle 一站式删除门面（`delete_jingle_device`） |

## 5. fixture 依赖链

```
android_preserved_app（testcases/android/conftest.py）
    ↓ force-stop + 启动 + 按需登录（不 pm clear）
jingle_main_with_target（jingle_delete/conftest.py）
    ↓ 仅实例化 jingle_delete_page，SN 断言在用例内完成
test_delete 用例
```

## 6. 前置条件与依赖

### 6.1 数据前置

`test_delete_doorbell_chime` 要求目标 SN 设备**已在账号中**（主页设备列表可见该 SN），
本测试**不会自动添加设备**，需由以下任一方式准备：

- 手动添加：在 jingle_add 模块跑一次 `test_full.py` 或 `test_quick.py`
- 真机手动：通过 app 真实添加

### 6.2 与 jingle_add 的协作

```
   ┌──────────────┐
   │  账号模块     │ 提供登录态
   │  (account)   │
   └──────┬───────┘
          ↓
┌──────────────────────┐
│  Jingle 添加模块     │ ① 添加设备 → 设备入账号
│  (jingle_add)        │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│  Jingle 删除模块     │ ← ② 删除该设备（本模块）
│  (jingle_delete)     │
└──────────────────────┘
```

完整生命周期：**账号登录 → jingle_add 添加 → jingle_delete 删除**。

## 7. 运行命令

```bash
# 整模块
pytest testcases/android/jingle_delete/ --platform android

# 单个测试
pytest testcases/android/jingle_delete/test_delete.py --platform android

# 通过环境变量注入目标 SN
export CLOUDEDGE_DEVICE_SN=131805981
pytest testcases/android/jingle_delete/test_delete.py --platform android
```

## 8. 与其他模块的关系

- **依赖账号模块**：`android_preserved_app` 需要 app 处于登录态
- **依赖 jingle_add 模块（数据）**：删除前需有 jingle_add 添加的设备
- **禁止反向依赖**：jingle_delete 不被 jingle_add / 账号模块依赖

## 9. 真机验证记录

| 用例 | 真机 | 验证时间 | SN | 备注 |
|---|---|---|---|---|
| `test_delete` | Redmi Note 11 5G | 2026-10-10 | 131805981 | 5 阶段全流程验证 |

## 10. 相关页面文档

- [智能门铃 Chime Base 一站式删除页（jingle_delete_page）](./jingle-delete-page.md)
- [主页文档](../reference/page-identification.md)

---

## 文档导航

- 上一篇：[Jingle 添加模块文档 ←](./jingle-add-module.md)
- 下一篇：[代码规范 →](../rules/coding.md)
- [返回文档中心](../README.md) · [返回项目首页](../../README.md)
