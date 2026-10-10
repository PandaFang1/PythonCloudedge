# 文档中心

本目录收纳项目的全部模块化文档。每个文件聚焦一个主题，便于按需查阅与维护。

## 文档结构

```
docs/
├── getting-started/      # 快速上手
│   ├── installation.md       # 环境准备
│   ├── configuration.md      # 配置说明
│   └── quickstart.md         # 快速开始
├── architecture/
│   └── overview.md           # 架构说明
├── guide/
│   ├── extension.md          # 扩展指南
│   ├── page-identification.md # 页面识别（核心页面 + 登录页定位器速查）
│   ├── login-page.md         # 登录页与国家/区域选择页（ADBKeyboard 中文搜索）
│   ├── account-page.md       # 我的信息页（退出登录 + 确认弹窗）
│   ├── add-device-category-page.md # 选择设备类别页（按类别/蓝牙两种方式 + 查看更多）
│   ├── device-add-flow.md    # 设备添加流程（策略模式 + 工厂分发 + 5 类设备）
│   ├── jingle-add-page.md    # jingle_add 一站式添加页（Chime Base 完整 11 阶段流程）
│   ├── jingle-delete-page.md # jingle_delete 一站式删除页（Chime Base 5 阶段流程）
│   ├── account-module.md     # 【模块】账号模块总览（登录/登出/切换）
│   ├── jingle-add-module.md  # 【模块】Jingle 添加模块总览（完整 + 快捷）
│   ├── jingle-delete-module.md # 【模块】Jingle 删除模块总览
│   └── serial.md             # 串口测试
├── rules/
│   ├── coding.md             # 代码规范
│   ├── testcase.md           # 用例编写规则
│   └── execution.md          # 执行规则
└── faq.md                    # 注意事项与 FAQ
```

## 推荐阅读顺序

新同学请按以下顺序通读：

1. [环境准备](./getting-started/installation.md)
2. [配置说明](./getting-started/configuration.md)
3. [快速开始](./getting-started/quickstart.md)
4. [架构说明](./architecture/overview.md)
5. [扩展指南](./guide/extension.md)
6. [页面识别文档](./guide/page-identification.md)（编写页面对象 / 维护定位器前必读）
7. [登录页文档](./guide/login-page.md)（登录页与国家/区域选择页，ADBKeyboard 中文搜索方案）
8. [我的信息页文档](./guide/account-page.md)（退出登录与确认弹窗）
9. [选择设备类别页文档](./guide/add-device-category-page.md)（按类别 / 蓝牙两种添加方式 + 查看更多抽屉）
9.1 [设备添加流程文档](./guide/device-add-flow.md)（策略模式架构 + 5 类设备 Flow + 工厂分发）
9.2 [jingle_add 一站式添加文档](./guide/jingle-add-page.md)（智能门铃 Chime Base 完整添加流程 + resource-id 速查）
9.3 [jingle_delete 一站式删除文档](./guide/jingle-delete-page.md)（智能门铃 Chime Base 5 阶段删除流程 + resource-id 速查）

## 模块索引

> 本节按业务模块聚合页面级文档，便于按业务功能查找。每个模块文档都包含：
> 包含的测试用例、依赖的 Page Objects、fixture 链、运行命令、与其他模块的关系。

| 模块 | 文档 | 包含测试 | 关键 Page Object |
|---|---|---|---|
| 账号模块（登录/登出/切换） | [account-module.md](./guide/account-module.md) | `test_login.py`、`test_logout.py`、`test_switch.py` | `CloudEdgeLoginPage` / `CloudEdgeAccountPage` / `CloudEdgeMyPage` |
| Jingle 添加模块（完整 + 快捷） | [jingle-add-module.md](./guide/jingle-add-module.md) | `test_full.py`、`test_quick.py` | `JingleAddPage` / `CloudEdgeAddDeviceCategoryPage` / `DoorbellChimeBaseFlow` |
| Jingle 删除模块 | [jingle-delete-module.md](./guide/jingle-delete-module.md) | `test_delete.py` | `JingleDeletePage` |

### 模块化架构原则

- **代码按模块分子目录**：`testcases/android/{account,jingle_add,jingle_delete}/` 三层目录
- **共享 fixture 上移**：跨模块共用的环境清理、Activity 等待工具统一在
  `testcases/android/conftest.py`（`android_test_env` / `android_logged_in` / `android_preserved_app` / `android_category_page`）
- **模块 fixture 下沉**：单模块特有 fixture 放在各模块 `conftest.py`（如 `account/conftest.py` 的 `android_my_page`）
- **fixture 链式复用**：高级 fixture 依赖低级 fixture（如 `android_account_page` → `android_my_page` → `android_logged_in` → `android_test_env`）
- **禁止测试间 import**：测试文件只能 import 共享 conftest 与 Page Objects，**不得** import 其他 test_*.py 文件

10. [代码规范](./rules/coding.md) — 写代码前必读
11. [用例编写规则](./rules/testcase.md) — 写用例前必读
12. [执行规则](./rules/execution.md) — 运行前必读
13. [串口测试](./guide/serial.md)（按需）
14. [FAQ](./faq.md)（按需）

## 文档导航

每个文档末尾都附有：

- 上一篇 / 下一篇
- 返回文档中心（本页）
- 返回项目首页

[返回项目首页](../README.md)