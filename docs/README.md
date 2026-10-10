# 文档中心

本目录收纳项目的全部模块化文档，按「业务模块 + 全局参考」两层组织。
- **新同学**：先按下方「推荐阅读顺序」通读 1-13 步（约 1-2 小时）。
- **老同学**：直接用「快速跳转」按业务模块定位。

## 快速跳转（按业务模块）

| 业务场景 | 入口模块 |
|---|---|
| 登录 / 退出 / 切换账号 | [账号模块 →](./modules/account/README.md) |
| 添加 / 删除设备（设备类别页 + 策略 Flow） | [设备管理 →](./modules/device_mgmt/README.md) |
| 智能门铃 Chime（完整 + 快捷 + 删除） | [Chime →](./modules/chime/README.md) |
| 编写新页面 / 维护定位器 | [参考与工具 →](./reference/README.md) |
| 跑串口测试 | [串口测试 →](./reference/serial.md) |

## 文档结构

```
docs/
├── getting-started/      # 快速上手
│   ├── installation.md       # 环境准备
│   ├── configuration.md      # 配置说明
│   └── quickstart.md         # 快速开始
├── architecture/
│   └── overview.md           # 架构说明
├── modules/                 # 业务模块（按业务切分，物理隔离）
│   ├── account/             # 账号模块（登录/登出/切换）
│   ├── device_mgmt/         # 设备管理（选择设备类别 + 策略模式 Flow）
│   └── chime/               # Chime 模块（智能门铃完整 + 快捷 + 删除）
├── reference/               # 参考与工具（跨模块通用）
│   ├── extension.md            # 扩展指南
│   ├── page-identification.md  # 页面识别（核心页面 + 登录页定位器速查）
│   └── serial.md               # 串口测试
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
5. [扩展指南](./reference/extension.md)
6. [页面识别文档](./reference/page-identification.md)（编写页面对象 / 维护定位器前必读）
7. [账号模块 — 登录页文档](./modules/account/login-page.md)（登录页与国家/区域选择页，ADBKeyboard 中文搜索方案）
8. [账号模块 — 我的信息页文档](./modules/account/account-page.md)（退出登录与确认弹窗）
9. [设备管理 — 选择设备类别页文档](./modules/device_mgmt/add-device-category-page.md)（按类别 / 蓝牙两种添加方式 + 查看更多抽屉）
9.1 [设备管理 — 设备添加流程文档](./modules/device_mgmt/device-add-flow.md)（策略模式架构 + 5 类设备 Flow + 工厂分发）
9.2 [Chime 模块 — jingle_add 一站式添加文档](./modules/chime/jingle-add-page.md)（智能门铃 Chime Base 完整添加流程 + resource-id 速查）
9.3 [Chime 模块 — jingle_delete 一站式删除文档](./modules/chime/jingle-delete-page.md)（智能门铃 Chime Base 5 阶段删除流程 + resource-id 速查）

## 模块索引

> 本节按业务模块聚合。每个模块的 `README.md` 是该模块的「分」入口，
> 包含测试用例、依赖的 Page Objects、fixture 链、运行命令、与其他模块的关系。

| 模块 | 入口 | 包含测试 | 关键 Page Object |
|---|---|---|---|
| 账号模块（登录/登出/切换） | [account/README.md →](./modules/account/README.md) | `test_login.py`、`test_logout.py`、`test_switch.py` | `CloudEdgeLoginPage` / `CloudEdgeAccountPage` / `CloudEdgeMyPage` |
| 设备管理（选择类别 + 策略 Flow） | [device_mgmt/README.md →](./modules/device_mgmt/README.md) | （由各设备类型模块的测试覆盖） | `CloudEdgeAddDeviceCategoryPage` / `BaseAddDeviceFlow` |
| Chime（智能门铃） | [chime/README.md →](./modules/chime/README.md) | `test_full.py`、`test_quick.py`、`test_delete.py` | `JingleAddPage` / `JingleDeletePage` / `DoorbellChimeBaseFlow` |
| 参考与工具（跨模块通用） | [reference/README.md →](./reference/README.md) | （无测试） | （通用扩展 + 定位器速查） |

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
13. [串口测试](./reference/serial.md)（按需）
14. [FAQ](./faq.md)（按需）

## 文档导航

每个文档末尾都附有：

- 上一篇 / 下一篇
- 返回文档中心（本页）
- 返回项目首页

[返回项目首页](../README.md)
