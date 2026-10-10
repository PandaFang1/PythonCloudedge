# 设备管理模块（device_mgmt/）

> 选择设备类别页 + 设备添加流程（策略模式 + 5 类设备 Flow）

## 概览

设备管理模块聚合「选择设备类别」入口页与「设备添加流程」策略模式架构，
是账号模块与具体设备类型模块（chime 等）之间的桥梁。

**核心设计**：

- 不同设备类型走不同配网流程（智能门铃 Chime Base / 电池摄像机 / 常电摄像机 / 4G 摄像机 / 摇头机）
- 业务用例**只关心调用入口**，不感知具体设备类型差异
- 新增设备类型只需写一个 Flow 子类 + 注册到工厂
- 单测可验证分发与存根行为（不依赖真机）

## 文件清单

| 文档 | 定位 | 关键 Page Object / 类 |
|---|---|---|
| [add-device-category-page.md](./add-device-category-page.md) | 选择设备类别页（按类别 / 蓝牙两种方式 + 查看更多抽屉） | `CloudEdgeAddDeviceCategoryPage` |
| [device-add-flow.md](./device-add-flow.md) | 设备添加流程策略模式（5 类设备 Flow + 工厂分发） | `BaseAddDeviceFlow` / `DoorbellChimeBaseFlow` / 4 款存根 |

## 阅读路径

1. 先读 [device-add-flow.md](./device-add-flow.md) 理解策略模式架构
2. 维护设备类别页定位器时读 [add-device-category-page.md](./add-device-category-page.md)

## 与其他模块的关系

- **上游**：[账号模块（account/）→](../account/README.md)（需要登录态）
- **下游**：[chime 模块（chime/）→](../chime/README.md)（chime 是设备类型之一，依赖本模块的 Flow 基类）
- **共享 fixture**：`android_category_page` 定义在 `testcases/android/conftest.py`

## 导航

- 上一篇：[账号模块（account/）←](../account/README.md)
- 下一篇：[Chime 模块（chime/）→](../chime/README.md)
- [返回文档中心](../../README.md)
- [返回项目首页](../../../README.md)
