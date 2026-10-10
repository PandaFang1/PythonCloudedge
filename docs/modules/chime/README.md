# Chime 模块（chime/）

> 智能门铃 Chime Base — 完整添加流程 + 快捷添加流程 + 删除流程

## 概览

Chime 模块聚合 CloudEdge 安卓端智能门铃（Chime Base）的端到端测试，
包含 3 个测试场景：

- **完整添加**（`test_full.py`）：按设备类别选择「智能门铃 → Chime Base」→ 9 步配网
- **快捷添加**（`test_quick.py`）：蓝牙区域直接点 SN → 直达 WiFi 输入页 → 6 步配网
- **删除**（`test_delete.py`）：进入设备详情页 → 5 阶段删除流程

**端到端实现 1 款**：Chime Base（`DoorbellChimeBaseFlow`）。
其他设备类型（电池摄像机 / 常电摄像机 / 4G 摄像机 / 摇头机）由设备管理模块的策略模式分发，
存根在 `pages/android/add_device_flow/` 目录下。

## 文件清单

| 文档 | 定位 | 关键 Page Object / 类 |
|---|---|---|
| [jingle-add-module.md](./jingle-add-module.md) | 【模块总览】完整流程 + 快捷流程全场景 + fixture 链 + 2 个测试用例 | `JingleAddPage` / `DoorbellChimeBaseFlow` |
| [jingle-add-page.md](./jingle-add-page.md) | jingle_add 一站式添加页（Chime Base 完整 11 阶段流程 + resource-id 速查） | 同上 |
| [jingle-delete-module.md](./jingle-delete-module.md) | 【模块总览】删除流程全场景 + fixture 链 + 1 个测试用例 | `JingleDeletePage` |
| [jingle-delete-page.md](./jingle-delete-page.md) | jingle_delete 一站式删除页（Chime Base 5 阶段流程 + resource-id 速查） | 同上 |

## 阅读路径

1. 先读 [jingle-add-module.md](./jingle-add-module.md) 了解完整 + 快捷添加全貌
2. 维护添加页定位器时读 [jingle-add-page.md](./jingle-add-page.md)
3. 删除流程：先读 [jingle-delete-module.md](./jingle-delete-module.md)，定位器细节看 [jingle-delete-page.md](./jingle-delete-page.md)

## 与其他模块的关系

- **上游**：[设备管理模块（device_mgmt/）→](../device_mgmt/README.md)（依赖策略模式 Flow 基类 + 选择设备类别页）
- **上游**：[账号模块（account/）→](../account/README.md)（需要登录态）
- **共享 fixture**：`android_logged_in` / `android_category_page` 定义在 `testcases/android/conftest.py`

## 导航

- 上一篇：[设备管理模块（device_mgmt/）←](../device_mgmt/README.md)
- 下一篇：[参考与工具（reference/）→](../reference/README.md)
- [返回文档中心](../../README.md)
- [返回项目首页](../../../README.md)
