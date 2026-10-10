# 账号模块 — 用户登录 / 退出登录 / 账号切换

> 真机全流程验证：2026-10-09 / 2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK）

## 1. 模块概述

**账号模块**（`testcases/android/account/`）聚合 CloudEdge 安卓端账号相关的端到端测试，
包括「登录」、「退出登录」、「账号切换」三个核心场景。该模块是**所有其他模块的前置依赖**
（设备模块 jingle_add / jingle_delete 都需要 app 处于登录态）。

```
账号模块的 3 个测试场景
├── test_login.py    → 选国家 + 账号密码登录（首次登录 / pm clear 后）
├── test_logout.py   → 我的信息页退出登录（弹窗取消 + 确定）
└── test_switch.py   → 同一设备切换登录不同账号
```

## 2. 包含的测试用例

| 测试函数 | allure 标签 | 验证内容 |
|---|---|---|
| `test_login_with_region` | epic=登录, feature=账号密码登录, story=ADBKeyboard 搜索国家并登录 | pm clear → 启动 → 选国家「美国」→ 账号密码登录 → 进入 MainActivity |
| `test_login_then_logout` | epic=登录, feature=退出登录, story=我的信息页退出登录 | 登录 → 我的 → 我的信息 → 退出登录（先取消后确定）→ 回登录页 |
| `test_switch_account` | epic=登录, feature=账号切换, story=退出登录后切换登录另一账号 | A 账号登录 → 退出 → B 账号登录 → 「我的」页账号文本已变 |

## 3. 模块目录结构

```
testcases/android/account/
├── __init__.py             # 子包标识 + 模块说明
├── conftest.py             # 模块 fixture：android_my_page、android_account_page
├── test_login.py           # 登录
├── test_logout.py          # 退出登录
└── test_switch.py          # 账号切换
```

## 4. 依赖的 Page Objects

| 页面类 | 工厂 key | 职责 |
|---|---|---|
| `CloudEdgeLoginPage` | `("android", "login_page")` | 登录页（账号/密码输入 + 国家选择） |
| `CloudEdgeMainPage` | _(直接构造)_ | 主页面（添加设备入口 + Tab 切换） |
| `CloudEdgeMyPage` | _(直接构造)_ | 「我的」Tab（账号入口） |
| `CloudEdgeAccountPage` | `("android", "account_page")` | 「我的信息」页（账号显示 + 退出登录） |

## 5. fixture 依赖链

```
android_test_env（testcases/android/conftest.py）
    ↓ pm clear + 预授权 11 项 + 禁用 autofill
android_logged_in（testcases/android/conftest.py）
    ↓ 启动 app + 登录（自动兜底） + MainActivity 断言
android_my_page（account/conftest.py）
    ↓ 切到「我的」Tab + 等待稳定
android_account_page（account/conftest.py）
    ↓ 点击账号入口 tv_account + 3 次重试 + MyInfo Activity 断言
test_logout / test_switch 用例
```

**特殊场景：`test_switch_account`** 需执行两次登录（A → 退出 → B），
无法直接复用 `android_logged_in`（只登录一次），故降级使用
更底层的 `android_test_env` 并在用例内手动管理两次登录流程。

## 6. 运行命令

```bash
# 整模块
pytest testcases/android/account/ --platform android

# 单个测试
pytest testcases/android/account/test_login.py --platform android -k test_login_with_region
pytest testcases/android/account/test_logout.py --platform android -k test_login_then_logout
pytest testcases/android/account/test_switch.py --platform android -k test_switch_account

# 通过 run.py
python run.py --platform android -k test_login_with_region
```

## 7. 与其他模块的关系

```
       ┌──────────────┐
       │  账号模块     │ ← 本模块
       │  (account)   │
       └──────┬───────┘
              │ 提供「登录态」前置
              ↓
   ┌──────────────────────┐    ┌──────────────────────┐
   │  Jingle 添加模块     │    │  Jingle 删除模块     │
   │  (jingle_add)        │    │  (jingle_delete)     │
   └──────────────────────┘    └──────────────────────┘
```

- **账号模块**提供基础登录态
- **Jingle 添加/删除模块**通过 `android_preserved_app`（保持登录态）依赖账号模块的能力
- **禁止反向依赖**：账号模块绝不依赖 jingle_add / jingle_delete

## 8. 真机验证记录

| 用例 | 真机 | 验证时间 | SN | 备注 |
|---|---|---|---|---|
| `test_login_with_region` | Redmi Note 11 5G | 2026-10-09 | — | ADBKeyboard 中文国家搜索 |
| `test_login_then_logout` | Redmi Note 11 5G | 2026-10-09 | — | 弹窗取消 + 确定全流程 |
| `test_switch_account` | Redmi Note 11 5G | 2026-10-10 | — | 美国 → 退出 → 中国切换 |

## 9. 相关页面文档

- [登录页文档](./login-page.md)
- [我的信息页文档](./account-page.md)（退出登录弹窗）
- [主页文档](./page-identification.md)

---

## 文档导航

- 上一篇：[主页文档 ←](./page-identification.md)
- 下一篇：[Jingle 添加模块文档 →](./jingle-add-module.md)
- [返回文档中心](../README.md) · [返回项目首页](../../README.md)
