# PO_PythonProject — 移动 App 双端 UI 自动化测试框架

> 基于 **poco + pytest + allure** 的双端 UI 自动化测试框架，PO 设计模式 + 策略模式 Flow + pytest fixture 体系。

## ✨ 核心特性

- **PO 模式 + 页面工厂**：双端业务方法同名，按 `(平台, 页面名)` 自动分发
- **双端共用一套用例**：同一产品 Android + iOS 用例共享，按 `--platform` 参数化运行
- **pytest + allure**：完整 fixture 链 + 失败截图 + 平台分组 + 步骤详情
- **poco 驱动**：统一抽象连接器（adb / devicectl），多设备多平台一键管理
- **策略模式 Flow**：5 类设备添加流程，端到端实现 1 款 + 4 款存根，新设备按模板补齐

## 🚀 快速上手

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置设备
vim config/config.yaml   # 填入 devices / serial_ports

# 3. 跑测试（Android 端）
python run.py --platform android

# 4. 看报告
allure serve reports/allure-html
```

## 📚 文档

完整文档在 [`docs/`](docs/README.md)，推荐路径：

- 🚀 [快速开始](docs/getting-started/quickstart.md) — 安装 + 配置 + 第一个测试
- 🏗️ [架构说明](docs/architecture/overview.md) — 分层 + fixture 依赖链 + 双端差异
- 🧩 [业务模块](docs/modules/) — 账号 / 设备管理 / Chime 三大模块
- 🛠️ [扩展与定位器](docs/reference/) — 新增页面、定位器采集、串口测试

## 🛠️ 技术栈

`Python 3` + `pytest` + `poco (pocoui)` + `airtest` + `allure-pytest` + `adb / Xcode devicectl`

## 📁 目录结构

```
PO_PythonProject/
├── pages/                        # PO 页面对象层（android/ + ios/）
├── testcases/                    # 测试用例（按业务模块分子目录）
├── utils/                        # 公共工具（日志 / 串口 / 设备管理）
├── config/                       # 设备与 app 配置
├── docs/                         # 项目文档（按模块组织）
├── logs/                         # 运行日志 + 串口日志
├── reports/                      # allure html 报告输出
├── run.py                        # 运行入口
└── requirements.txt
```

## 🧪 常用命令

```bash
# 跑指定 marker
pytest -m "android and not serial" -v

# 跑指定文件
pytest testcases/android/jingle_add/test_full.py --platform android

# 跑指定场景
pytest -k "login_with_region" --platform android

# 串口测试（不依赖 app）
pytest testcases/serial/ -v
```
