# 账号模块（account/）

> 用户登录 / 退出登录 / 账号切换 — 所有其他模块的前置依赖

## 概览

账号模块（`testcases/android/account/`）聚合 CloudEdge 安卓端账号相关的端到端测试，
包括「登录」「退出登录」「账号切换」三个核心场景。

**前置依赖**：所有其他业务模块（`jingle_add` / `jingle_delete` 等）都需要 app 处于登录态，
本模块 fixture `android_logged_in` 被 `testcases/android/conftest.py` 统一托管。

## 文件清单

| 文档 | 定位 | 关键 Page Object |
|---|---|---|
| [login-page.md](./login-page.md) | 登录页 + 国家/区域选择页（ADBKeyboard 中文搜索方案） | `CloudEdgeLoginPage` |
| [account-page.md](./account-page.md) | 我的信息页（退出登录 + 确认弹窗） | `CloudEdgeAccountPage` / `CloudEdgeMyPage` |
| [account-module.md](./account-module.md) | 【模块总览】登录/登出/切换全场景 + fixture 链 + 3 个测试用例 | 上述 PO 汇总 |

## 阅读路径

1. 先读 [account-module.md](./account-module.md) 了解模块全貌
2. 维护登录页定位器时读 [login-page.md](./login-page.md)
3. 维护退出登录弹窗时读 [account-page.md](./account-page.md)

## 与其他模块的关系

- **上游**：无（账号模块是入口模块）
- **下游依赖本模块**：`jingle_add` / `jingle_delete` 等所有需要登录态的模块
- **共享 fixture**：`android_logged_in` 定义在 `testcases/android/conftest.py`（不在本目录）

## 导航

- 上一篇：[页面识别（reference/）→](../reference/page-identification.md)
- 下一篇：[设备管理模块（device_mgmt/）→](../device_mgmt/README.md)
- [返回文档中心](../../README.md)
- [返回项目首页](../../../README.md)
