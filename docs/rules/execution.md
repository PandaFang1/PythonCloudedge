# 执行规则

> 本章是后续执行的**统一约定**，违反约定的执行方式将无法复现或定位问题。

## 3.1 环境准备 checklist

- [ ] `pip install -r requirements.txt` 已安装
- [ ] Android：`adb devices` 状态为 `device`
- [ ] iOS：`xcrun devicectl list devices` 状态为 `available (paired)`
- [ ] iOS：`config.yaml` 中 `wda_port` 指定的 WDA 已启动（`http://127.0.0.1:<port>/status` 可访问）
- [ ] allure 命令行已安装（`allure --version`）
- [ ] 串口（如使用）：`serial_ports` 配置正确，可用列表展示系统中该串口存在
- [ ] 运行目录为仓库根目录
- [ ] 日志目录：`logs/operater_logs/` 与 `logs/serial_logs/` 已存在（首次运行自动创建）；CI runner 建议定期清理，避免单目录超 1GB（200MB × 5 备份）

## 3.2 运行命令规范

### 方式一：run.py 入口（必须）

```bash
# 完整运行
python run.py --platform all --report

# 仅 Android
python run.py --platform android --report

# 仅 iOS
python run.py --platform ios --report

# 仅冒烟
python run.py --pytest-args "-m smoke" --report

# 仅串口
python run.py --pytest-args "-m serial" --report

# 透传任意 pytest 参数
python run.py --pytest-args "-k restart --maxfail=0"
```

### 方式二：pytest 直调（仅在调试时）

```bash
pytest testcases/test_app_lifecycle.py --platform android -v
pytest -m serial -v
pytest --collect-only -q        # 仅收集用例
```

> **原则**：CI / 正式运行走 `run.py`；本地调试可直接 `pytest`。

## 3.3 平台选择规则

| 场景 | --platform |
|---|---|
| CI 双端跑 | `all`（默认） |
| Android 调试 | `android` |
| iOS 调试 | `ios` |
| 串口跑（与平台无关） | `all` + `-m serial` |

共用用例的 `platform` fixture 由 `pytest_generate_tests` 按 `--platform` 参数化：
- `--platform all` → 生成 `[android]` + `[ios]` 两组
- `--platform android` → 仅生成 `[android]`
- `--platform ios` → 仅生成 `[ios]`

## 3.4 报告生成与查看

```bash
# 方式一：run.py --report 自动生成
python run.py --platform android --report

# 方式二：手动生成
allure generate allure-results -o reports/allure-report --clean
allure open reports/allure-report

# 方式三：实时服务
allure serve allure-results
```

**报告检查清单**：

- [ ] 用例按平台分组（`安卓端 · xxx` / `iOS 端 · xxx`）
- [ ] 失败用例附带截图
- [ ] 串口用例可在 `Categories` / `Suites` 中看到 `@serial` 标签
- [ ] 串口用例**失败**时附带最近 200 行串口输出（`pytest_runtest_makereport` 钩子自动 attach，便于定位）
- [ ] 报告目录 `reports/allure-report/` 可正常打开（目录存在说明 allure 命令可用）

## 3.5 无设备 / 无串口的跳过行为

| 场景 | 行为 |
|---|---|
| Android 设备离线 | Android 用例 `skip`（含原因），iOS 用例继续 |
| iOS 设备离线 / WDA 未就绪 | iOS 用例 `skip`（含原因），Android 用例继续 |
| `serial_ports` 未配置 / 空 | 串口用例 `skip`（含原因），UI 用例不受影响 |
| 串口连接失败 | 该串口用例 `skip`（含原因），其他用例继续 |
| 用例无断言 | pytest 收集期发出警告 `pytest warning` |

> **跳过不等于失败**：CI 配置时，`--strict-markers` 与 `--strict-config` 可开启，
> 但**不要**将 `skip` 计为 failure。建议 CI 使用 `--no-header -q --tb=line`。

## 3.6 日志管理

日志与串口输出统一收口到 `logs/` 目录，便于维护与清理。

**目录与用途**

| 目录 | 来源 | 内容 |
|---|---|---|
| `logs/operater_logs/` | `utils/log_utils.py` | 框架运行日志（按天命名） |
| `logs/serial_logs/` | `utils/serial_utils.py` | 串口原始输出（按天+串口命名） |
| `reports/` | `testcases/conftest.py` | 失败截图 + allure html 报告 |

**轮转策略**（默认值，可在源文件顶部常量调整）

| 维度 | 运行日志 | 串口日志 |
|---|---|---|
| 单文件上限 | 200MB | 200MB |
| 保留备份数 | 5 | 5 |
| 单目录总量上限 | 1GB | 1GB |

轮转触发时机：
- **运行日志**：`RotatingFileHandler` 在 `logging` 写盘时自动判定并轮转
- **串口日志**：每写一行测试库 `log_file.tell()` 检查，超限即关闭 → 滚动 → 新建

**串口用例失败时的 allure 增强**

- 串口用例失败时，`pytest_runtest_makereport` 钩子自动 attach 该用例最近 200 行历史输出，便于回溯死前串口状态
- UI 用例失败时仍仅附设备截图（不附加无关串口）

**运维要点**

- CI runner 建议定期清理 `logs/` 与 `reports/`，避免磁盘占满
- 调整常量后无须重启 IDE，仅需重跑测试即可加载新策略
- 不要把 `logs/` 加入版本管理（已在 `.gitignore` 中忽略）

---

## 文档导航

- 上一篇：[用例编写规则 ←](./testcase.md)
- 下一篇：[FAQ →](../faq.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
