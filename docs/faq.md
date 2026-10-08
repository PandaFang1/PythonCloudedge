# 注意事项与 FAQ

**Q: iOS 用例被跳过，提示「WebDriverAgent 未就绪」？**

iOS 端 poco 依赖 WDA。请先在 iOS 设备上启动 WebDriverAgent（端口与
`config.yaml` 中 `wda_port` 一致），确认 `http://127.0.0.1:8100/status`
可访问后再运行。WDA 未就绪时 iOS 用例会带原因跳过，**不影响安卓端**。

**Q: 用例报「平台无任何在线设备」？**

检查设备连接（`adb devices` / `xcrun devicectl list devices`），并核对
`config.yaml` 中的 `udid` 是否与实际设备一致。可用模块自测比对配置：

```bash
python -m utils.phone_manager
```

**Q: 页面元素找不到？**

仓库中的页面定位器为**示例值**，首次编写业务用例前请按 CloudEdge / 云际
实际 UI 结构调整 `pages/android/`、`pages/ios/` 中的定位器。定位优先级：
基本选择器（`name`/`text`/`type`）> 相对选择器 > 索引 > 正则。

**Q: 日志与截图在哪？**

- 运行日志：`logs/operater_logs/`（按天命名；单文件 ≤ 200MB，保留 5 个备份；总量上限 1GB）
- 串口日志：`logs/serial_logs/`（按天+串口命名；单文件 ≤ 200MB，保留 5 个备份；总量上限 1GB）
- 失败截图：`reports/failure_*.png`（同时附加到 allure 报告）
- allure 结果：`allure-results/`；html 报告：`reports/allure-report/`

**日志轮转配置**（可在 `utils/log_utils.py`、`utils/serial_utils.py` 顶部常量调整）：

```python
# 运行日志
MAX_BYTES = 200 * 1024 * 1024   # 200MB
BACKUP_COUNT = 5                # 保留 5 份

# 串口日志
SERIAL_LOG_MAX_BYTES = 200 * 1024 * 1024   # 200MB
SERIAL_LOG_BACKUP_COUNT = 5                # 保留 5 份

---

## 文档导航

- 上一篇：[执行规则 ←](./rules/execution.md)

[返回文档中心](./README.md) · [返回项目首页](../README.md)
```
