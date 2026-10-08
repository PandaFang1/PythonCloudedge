# 快速开始

## 方式一：run.py 入口（推荐）

```bash
python run.py                          # 双端全跑
python run.py --platform android       # 仅安卓端（CloudEdge）
python run.py --platform ios           # 仅 iOS 端（云际）
python run.py --platform android --report   # 运行后生成 allure 报告
python run.py --pytest-args "-k smoke"      # 透传任意 pytest 参数
python run.py --pytest-args "--collect-only -q"  # 仅收集用例
```

## 方式二：pytest 直接调用

```bash
pytest                                  # 双端全跑
pytest --platform android               # 指定平台
pytest testcases/test_app_lifecycle.py  # 指定文件
pytest -k "restart"                     # 按关键字筛选
```

`--platform` 选项会自动参数化声明了 `platform` fixture 的共用用例：
`--platform all` 生成 `test_xxx[android]` 与 `test_xxx[ios]` 两组用例。

## 查看 allure 报告

```bash
allure generate allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

或运行后直接 `allure serve allure-results`。用例按平台自动打标签
（`安卓端 · app 生命周期` / `iOS 端 · app 生命周期`），失败用例自动附加设备截图。

---

## 文档导航

- 上一篇：[配置说明 ←](./configuration.md)
- 下一篇：[架构说明 →](../architecture/overview.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
