# PO_PythonProject — 移动 App 双端 UI 自动化测试框架

基于 **poco + pytest + allure** 的移动 App UI 自动化测试框架，采用 **PO（Page Object）设计模式**，支持 **Android 与 iOS 双端**用例共用、按平台参数化运行。

同一产品的双端版本共用一套业务用例：

| 平台 | App | 包名 / Bundle ID |
|---|---|---|
| Android | CloudEdge | `com.cloudedge.smarteye` |
| iOS | 云际 | `com.meari.smartcamera` |

## 技术栈

- **语言**：Python 3（遵循 PEP-8，行宽 100，已通过 pycodestyle 检查）
- **UI 驱动**：poco（pocoui）+ airtest 设备连接
- **测试框架**：pytest（fixture 体系 + 参数化）
- **测试报告**：allure-pytest（步骤、失败截图、平台分组标签）
- **设备管理**：adb（Android）/ Xcode devicectl（iOS），多设备多平台统一管理
- **设计模式**：PO 模式 + 页面工厂 + 抽象连接器（OOP 优先）

## 目录结构

```text
PO_PythonProject/
├── pages/                        # PO 页面对象层
│   ├── base_page.py              # [共用] 基类：元素操作 + app 生命周期
│   ├── page_factory.py           # [共用] 页面工厂：按 (平台, 页面名) 分发页面类
│   ├── android/                  # Android 平台页面包（CloudEdge）
│   │   └── main_page.py          #   主页面：定位器 + 业务方法
│   └── ios/                      # iOS 平台页面包（云际）
│       └── main_page.py          #   主页面：与安卓端同名接口
├── testcases/                    # 测试用例层
│   ├── conftest.py               # 核心 fixtures：--platform 选项、设备连接、
│   │                             #   poco 驱动、app 生命周期、失败截图钩子
│   ├── test_app_lifecycle.py     # 双端共用用例（按 platform 参数化）
│   ├── android/                  # 安卓端特有用例（权限弹窗、系统键等）
│   └── ios/                      # iOS 端特有用例
├── utils/                        # 公共工具层
│   ├── log_utils.py              # 日志（控制台 + 按大小轮转文件）
│   ├── serial_utils.py           # 串口工具（循环读取/写入/关键字检测）
│   └── phone_manager.py          # 手机管理（adb/devicectl 多态连接器 + 配置比对）
├── config/
│   ├── config.yaml               # 设备与 app 配置（devices 列表）
│   └── config_manager.py         # 配置校验
├── test_datas/                   # 测试数据
├── reports/                      # 失败截图 + allure html 报告输出
├── allure-results/               # allure 原始结果（运行后自动生成）
├── logs/                         # 运行日志与串口日志（统一父目录）
│   ├── operater_logs/            #   运行日志（按天轮转）
│   └── serial_logs/              #   串口日志（按天+端口命名）
├── docs/                         # 文档（按模块组织）
├── run.py                        # 运行入口（pytest 命令组装 + allure 报告）
├── pytest.ini                    # pytest 配置（markers、allure 输出）
├── requirements.txt              # Python 依赖
└── README.md                     # 本文档
```

## 文档导航

### 快速上手

- [环境准备](docs/getting-started/installation.md) — Python 依赖、系统工具、设备连接
- [配置说明](docs/getting-started/configuration.md) — devices 设备配置 + serial_ports 串口配置
- [快速开始](docs/getting-started/quickstart.md) — run.py / pytest 运行与 allure 报告

### 架构与指南

- [架构说明](docs/architecture/overview.md) — 分层设计、fixture 依赖链、双端差异处理
- [扩展指南](docs/guide/extension.md) — 新增页面、新增共用用例
- [串口测试](docs/guide/serial.md) — 串口 fixture、用例编写、运行

### 开发与执行规则

- [代码规范](docs/rules/coding.md) — 命名、目录、PO、定位器、串口、风格约束
- [用例编写规则](docs/rules/testcase.md) — 共用/特有用例、marker、参数化、allure、断言
- [执行规则](docs/rules/execution.md) — 环境准备、运行命令、平台选择、报告、跳过行为、日志管理

### 其他

- [注意事项与 FAQ](docs/faq.md) — 常见问题排查
