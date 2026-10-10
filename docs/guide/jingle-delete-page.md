# 智能门铃 Chime Base 一站式删除页面（jingle_delete_page）

> 真机全流程验证：2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK，SN 131805981）

## 1. 概述

`JingleDeletePage`（工厂页面名 `jingle_delete_page`，文件
`pages/android/jingle_delete_page.py`）是智能门铃 Chime Base 删除的
**一站式门面 PO**：封装从主页点击设备 SN 开始，到「删除完成
（主页断言设备列表无 SN）」的完整流程。

对用例暴露单一入口 `delete_jingle_device()`，一行代码完成整个删除链路：

```python
jingle_delete_page = PageFactory.create(
    "android", "jingle_delete_page", poco=poco, udid=udid,
)
# SN 默认取 DEFAULT_DEVICE_SN（与添加流程共用，如 131805981）
remain = jingle_delete_page.delete_jingle_device()
# 或直接指定
remain = jingle_delete_page.delete_jingle_device(sn="131805981")
# 返回删除后的主页设备列表（不含 SN 视为成功）
```

## 2. 删除流程记录（5 个阶段，真机逐步验证）

前置：app 已处于登录态主页（`MainActivity`）。

| # | 阶段 | Activity | 操作 | 关键 resource-id |
|---|---|---|---|---|
| 1 | jingle 首页 | `JingleBaseActivity` | 主页**点击设备 SN**（Chime Base 条目名）进入；页面识别点=3 元素同时存在（`tv_title` 文本=SN **+** `iv_state_on` 设备状态图标 **+** `switch_btn_schedules` 日程开关） | `tvJingleNeutralName`（主页条目）/ `tv_title`（jingle 首页标题=SN）/ `iv_state_on`（设备状态图标）/ `switch_btn_schedules`（日程开关） |
| 2 | 设置页 | `CameraSettingNewActivity` | 点击**右上角设置按钮**；页面识别点=标题「设置」 | `iv_submit`（右上角设置）/ `tv_title`（'设置'） |
| 3 | 设置页下滑 | 同上 | **向下滑动**直至「删除设备」按钮可见，点击（按钮位于 `sv_setting` 列表最底部，进入时通常在屏外） | `btn_delete`（'删除设备'）/ `sv_setting` |
| 4 | 删除确认弹框 | 同上（Dialog） | 比对弹框描述 → 点击「**删除**」（注意：确认按钮文本是「删除」不是「确定」） | `tv_ai_search_title`（'温馨提示'）/ `tv_ai_search_des`（'确定要删除该设备和子设备及所关联的数据？'）/ `tv_confirm`（'删除'）/ `tv_cancel`（'取消'） |
| 5 | 主页断言 | `MainActivity` | 点「删除」后 app **自动返回主页**；断言设备列表**不含**该 SN 即删除成功 | `tvJingleNeutralName` / `tvCameraName`（经 `get_device_list()` 轮询） |

## 3. 实现要点

### 3.1 定位器（真机 dump 验证 2026-10-10）

| 阶段 | 定位器 | 说明 |
|---|---|---|
| jingle 首页-标题 | `tv_title` | 文本=设备 SN，作为页面识别点 ① |
| jingle 首页-状态图标 | `iv_state_on` | 设备状态（在线/离线指示），作为页面识别点 ②（2026-10-10 增） |
| jingle 首页-日程开关 | `switch_btn_schedules` | 「日程」开关按钮，作为页面识别点 ③（2026-10-10 增） |
| jingle 首页-设置 | `iv_submit` | 工具栏右上角 |
| 设置页-标题 | `tv_title` | 文本='设置'，作为页面识别点 |
| 设置页-删除 | `btn_delete` | 文本='删除设备'，列表底部 |
| 弹框-标题 | `tv_ai_search_title` | 文本='温馨提示' |
| 弹框-描述 | `tv_ai_search_des` | '确定要删除该设备和子设备及所关联的数据？' |
| 弹框-确认 | `tv_confirm` | 文本='删除' |
| 弹框-取消 | `tv_cancel` | 文本='取消' |

### 3.2 关键容错

- **jingle 首页 3 元素识别**（`open_jingle_home_by_sn`，2026-10-10 起）：
  工具栏标题 `tv_title` 文本=SN 与 2 个新识别点（`iv_state_on` 设备状态图标、
  `switch_btn_schedules` 日程开关）**同时存在**才判定进入 jingle 首页。
  多识别点降低点击落空或标题文本撞名导致的误判概率。
- **下滑查找**（`click_delete_button`）：「删除设备」在 `sv_setting`
  最底部，进入设置页时通常在屏幕外（poco 层级中存在但 `visible=False`）；
  实现为「逐屏上滑 → 检查可见 → 可见即点击」，上限 8 屏防死循环
- **主页点击条目名兼容**（`open_jingle_home_by_sn`）：按
  `tvJingleNeutralName` → `tvJingleBaseName` 候选顺序查找 SN 条目
- **删除后断言轮询**（`assert_device_deleted`）：返回主页后设备列表
  需渲染时间，30s 内每 2s 轮询直至列表不含 SN（复用添加流程
  `assert_device_added` 的同款模式，条件相反）
- **条目不在屏内**：主页设备较多时目标 SN 条目可能需下滑，
  如遇此场景可在调用前先手动下滑（当前 3 台设备未触发）

### 3.3 与添加流程的关系

| | 添加（`jingle_add_page`） | 删除（`jingle_delete_page`） |
|---|---|---|
| 入口 | 主页「添加设备」→ 类别页/蓝牙区域 | 主页直接点设备 SN |
| 页面数 | 11 个页面/阶段 | 5 个阶段 |
| 设备前提 | 处于配对态（蓝牙可见/可搜到） | 已在账号中（无需配对态，云端删除） |
| 结束断言 | 主页列表**含** SN | 主页列表**不含** SN |
| 恢复方式 | — | 需设备重进配对态后再走添加流程 |

删除是不可逆操作：删除后如需恢复，须让设备重新进入配对态
（按复位键），再走完整/快捷添加流程。

## 4. 用例

`testcases/android/test_delete_doorbell_chime.py`：

- **前置检查**：主页设备列表应含目标 SN（否则跳过意义）
- **一站式删除**：`delete_jingle_device(sn=...)`
- **断言**：删除后主页设备列表不含该 SN
- **默认 skip**：`HARDWARE_READY=False` 时跳过（真机调试改为 True）
- **数据驱动**：`sn` 参数可被 pytest fixture / 环境变量覆盖

```bash
pytest testcases/android/test_delete_doorbell_chime.py --platform android
```

真机验证结果（2026-10-10）：
主页点 SN → jingle 首页 → 设置页 → 下滑点「删除设备」→ 弹框点「删除」
→ 自动返回主页，设备列表由 `['132003599', '131805981', '131903239']`
变为 `['132003599', '131903239']`，全程约 15 秒，一次通过。

## 5. 文档导航

- 相关：[jingle 添加页面](./jingle-add-page.md)
- 相关：[设备添加流程策略模式](./device-add-flow.md)
