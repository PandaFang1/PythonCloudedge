# 环境准备

## 1. Python 依赖

```bash
pip install -r requirements.txt
```

依赖清单：`PyYAML`、`pocoui`、`airtest`、`pytest`、`allure-pytest`、`pyserial`

## 2. 系统工具

| 工具 | 用途 | 安装方式 |
|---|---|---|
| adb | Android 设备连接 | 安装 Android platform-tools |
| Xcode 命令行工具 | iOS 设备连接（`xcrun devicectl`） | `xcode-select --install` |
| allure 命令行 | 生成 html 报告 | `brew install allure` |

## 3. 设备连接

- **Android**：USB 连接并开启「开发者选项 → USB 调试」，确认 `adb devices` 状态为 `device`
- **iOS**：USB 连接并在手机上信任此电脑，确认已配对（`xcrun devicectl list devices` 显示 `available (paired)`）

---

## 文档导航

- 下一篇：[配置说明 →](./configuration.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
