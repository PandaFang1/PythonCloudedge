# 参考与工具（reference/）

> 跨模块通用文档 — 扩展指南 / 页面识别 / 串口测试

## 概览

本目录收纳**跨模块通用**的文档，**不属于任何具体业务模块**。包含三类：

- **扩展机制**：如何新增页面 / 设备类型 / 设备 Flow
- **页面识别**：核心页面 + 登录页定位器速查（编写 PO 前必读）
- **测试工具**：串口测试（不依赖 app 的纯硬件层验证）

## 文件清单

| 文档 | 定位 | 何时查阅 |
|---|---|---|
| [extension.md](./extension.md) | 扩展指南（新增页面 / 设备类型 / 设备 Flow 的 3 步流程） | 新增任何 PO / 模块前必读 |
| [page-identification.md](./page-identification.md) | 页面识别（核心页面 + 登录页定位器速查） | 编写 PO / 维护定位器前必读 |
| [serial.md](./serial.md) | 串口测试（按需） | 硬件层验证时查阅 |

## 阅读路径

1. **新同学**必读顺序：`page-identification.md` → `extension.md`
2. 跑串口测试时读 `serial.md`

## 与其他模块的关系

- **上游**：[chime 模块（chime/）→](../chime/README.md)（chime 是最后一个业务模块）
- **本目录不依赖任何业务模块**（是基础层）
- **业务模块都依赖本目录**（特别是 `page-identification.md` 写的定位器规范）

## 导航

- 上一篇：[Chime 模块（chime/）←](../chime/README.md)
- 下一篇：阅读 [代码规范 →](../rules/coding.md)（写代码前必读）
- [返回文档中心](../../README.md)
- [返回项目首页](../../../README.md)
