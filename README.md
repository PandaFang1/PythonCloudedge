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
│   │   ├── main_page.py          #   首页：识别点 + Tab 导航 + 添加设备弹窗
│   │   ├── message_page.py       #   消息页：报警/分享 Tab
│   │   ├── my_page.py            #   我的页：二维码/反馈 + 功能入口
│   │   ├── login_page.py         #   登录页：国家/区域选择（ADBKeyboard）+ 登录
│   │   ├── account_page.py       #   我的信息页：账号资料 + 退出登录
│   │   └── add_device_category_page.py # 选择设备类别页：按类别/蓝牙两种添加方式
│   └── ios/                      # iOS 平台页面包（云际）
│       ├── main_page.py          #   首页：与安卓端同名接口
│       ├── message_page.py       #   消息页：与安卓端同名接口
│       └── my_page.py            #   我的页：与安卓端同名接口
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

## 页面识别与导航（双端真机验证）

框架已覆盖产品三大核心页面，双端定位器均来自真机验证，详细对照表见
[页面识别文档](docs/guide/page-identification.md)：

| 页面 | 工厂页面名 | Android 识别点（CloudEdge） | iOS 识别点（云际） |
|---|---|---|---|
| 首页 | `main_page` | `ivAddDevice` + `ivMenu` | `nav home add` + `nav home menu` |
| 消息页 | `message_page` | 顶部 Tab「报警」+「分享」 | 顶部 Tab「报警」+「分享」（name 属性） |
| 我的页 | `my_page` | `iv_qr_code` + `feedback` | `img me qrcode` + `img me scan` |

Android 端另覆盖 **登录页** 与其内嵌的 **国家/区域选择页**（不单独注册工厂，
定位器与 ADBKeyboard 中文搜索方案详见
[登录页文档](docs/guide/login-page.md)）：

| 页面 | Android 识别点（CloudEdge） | 说明 |
|---|---|---|
| 登录页 | `et_account` + `et_password` | 一站式登录入口 `login_with_region(...)`：选国家 → 勾选记住密码 → 输入账号密码 → 登录 |
| 国家/区域选择页 | `et_region_search`（弹出页） | ADBKeyboard 输入中文（如「美国」）过滤列表后点击目标国家返回登录页 |

Android 端另覆盖 **我的信息页**（「我的」页点击 `tv_account` 进入，
退出登录与确认弹窗详见
[我的信息页文档](docs/guide/account-page.md)）：

| 页面 | Android 识别点（CloudEdge） | 说明 |
|---|---|---|
| 我的信息页 | `tv_title`（我的信息）+ `logout_layout`（退出登录） | 一站式退出 `logout(confirm=True/False)`：底部「退出登录」→ 弹窗「确定 / 取消」→ 回登录页 / 停留本页 |

Android 端另覆盖 **选择设备类别页**（首页 `ivAddDevice` → 弹窗「添加设备」，
按类别 / 蓝牙两种添加方式详见
[选择设备类别页文档](docs/guide/add-device-category-page.md)）：

| 页面 | Android 识别点（CloudEdge） | 说明 |
|---|---|---|
| 选择设备类别页 | `tv_title`（选择设备类别）+ `recyclerview_main`（左侧分类） | 方式 A：左侧 `tv_category_name` + 右侧 `tv_device_name`；方式 B：顶部 `rv_devices` 蓝牙列表 + 「查看更多」弹出 `design_bottom_sheet` 抽屉 |

Android 端另覆盖 **智能门铃 Chime Base 一站式添加页**（工厂页面名 `jingle_add_page`，
封装从「选择设备类别」页到「添加完成（主页断言）」的完整 11 阶段流程，
真机 2026-10-09 全链路验证，详见
[一站式添加页文档](docs/guide/jingle-add-page.md)）：

| 页面 | Android 识别点（CloudEdge） | 说明 |
|---|---|---|
| jingle_add 一站式添加页 | 起点复用「选择设备类别」页识别点 | 一站式入口 `add_jingle_device(sn, ssid, password)`：选「智能门铃→Chime Base」→ 安装位置/接入电源指引 → 连接设备点 SN「添加」→ 无线连接（输 SSID → 点箭头收列表 → 输密码）→ 弹框比对「确定」→ 等待入网 → 成功页「下一步」→ 设置房间「完成」→ 安装指引「下一步」→ 网络诊断「返回首页」→ 主页断言 `tvJingleBaseName` 含 SN |

- **底部 Tab 导航**：首页 ⇄ 消息页、首页 ⇄ 我的页，双端业务方法同名
  （`open_home_page` / `open_message_page` / `open_my_page`）
- **双端定位器差异**：Android 文本用 `{"text": "xxx"}`、控件 ID 用
  `{"name": "com.cloudedge.smarteye:id/xxx"}`；iOS 文本统一挂在可访问性标签上，
  用 `{"name": "xxx"}` 定位

## 文档导航

### 快速上手

- [环境准备](docs/getting-started/installation.md) — Python 依赖、系统工具、设备连接
- [配置说明](docs/getting-started/configuration.md) — devices 设备配置 + serial_ports 串口配置
- [快速开始](docs/getting-started/quickstart.md) — run.py / pytest 运行与 allure 报告

### 架构与指南

- [架构说明](docs/architecture/overview.md) — 分层设计、fixture 依赖链、双端差异处理
- [扩展指南](docs/guide/extension.md) — 新增页面、新增共用用例
- [页面识别文档](docs/guide/page-identification.md) — 三大页面双端识别点与定位器速查
- [登录页文档](docs/guide/login-page.md) — 登录页与国家/区域选择页（Android）：定位器、
  ADBKeyboard 中文搜索、`login_with_region` 一站式登录
- [我的信息页文档](docs/guide/account-page.md) — 我的信息页（Android）：账号资料、
  退出登录确认弹窗、`logout` 一站式退出
- [选择设备类别页文档](docs/guide/add-device-category-page.md) — 选择设备类别页
  （Android）：按类别 / 蓝牙两种添加方式 + 「查看更多」BottomSheet
- [设备添加流程文档](docs/guide/device-add-flow.md) — 策略模式架构：
  BaseAddDeviceFlow + 5 类设备 Flow + DeviceFlowFactory 工厂分发
- [jingle_add 一站式添加文档](docs/guide/jingle-add-page.md) — 智能门铃
  Chime Base 一站式添加页：完整 11 阶段流程记录 + resource-id 速查 +
  真机踩坑细节（箭头收列表 / 弹框解析 / 主页断言）
- [串口测试](docs/guide/serial.md) — 串口 fixture、用例编写、运行

### 开发与执行规则

- [代码规范](docs/rules/coding.md) — 命名、目录、PO、定位器、串口、风格约束
- [用例编写规则](docs/rules/testcase.md) — 共用/特有用例、marker、参数化、allure、断言
- [执行规则](docs/rules/execution.md) — 环境准备、运行命令、平台选择、报告、跳过行为、日志管理

### 其他

- [注意事项与 FAQ](docs/faq.md) — 常见问题排查
