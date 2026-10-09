# 文档中心

本目录收纳项目的全部模块化文档。每个文件聚焦一个主题，便于按需查阅与维护。

## 文档结构

```
docs/
├── getting-started/      # 快速上手
│   ├── installation.md       # 环境准备
│   ├── configuration.md      # 配置说明
│   └── quickstart.md         # 快速开始
├── architecture/
│   └── overview.md           # 架构说明
├── guide/
│   ├── extension.md          # 扩展指南
│   ├── page-identification.md # 页面识别（核心页面 + 登录页定位器速查）
│   ├── login-page.md         # 登录页与国家/区域选择页（ADBKeyboard 中文搜索）
│   ├── account-page.md       # 我的信息页（退出登录 + 确认弹窗）
│   ├── add-device-category-page.md # 选择设备类别页（按类别/蓝牙两种方式 + 查看更多）
│   └── serial.md             # 串口测试
├── rules/
│   ├── coding.md             # 代码规范
│   ├── testcase.md           # 用例编写规则
│   └── execution.md          # 执行规则
└── faq.md                    # 注意事项与 FAQ
```

## 推荐阅读顺序

新同学请按以下顺序通读：

1. [环境准备](./getting-started/installation.md)
2. [配置说明](./getting-started/configuration.md)
3. [快速开始](./getting-started/quickstart.md)
4. [架构说明](./architecture/overview.md)
5. [扩展指南](./guide/extension.md)
6. [页面识别文档](./guide/page-identification.md)（编写页面对象 / 维护定位器前必读）
7. [登录页文档](./guide/login-page.md)（登录页与国家/区域选择页，ADBKeyboard 中文搜索方案）
8. [我的信息页文档](./guide/account-page.md)（退出登录与确认弹窗）
9. [选择设备类别页文档](./guide/add-device-category-page.md)（按类别 / 蓝牙两种添加方式 + 查看更多抽屉）
10. [代码规范](./rules/coding.md) — 写代码前必读
11. [用例编写规则](./rules/testcase.md) — 写用例前必读
12. [执行规则](./rules/execution.md) — 运行前必读
13. [串口测试](./guide/serial.md)（按需）
14. [FAQ](./faq.md)（按需）

## 文档导航

每个文档末尾都附有：

- 上一篇 / 下一篇
- 返回文档中心（本页）
- 返回项目首页

[返回项目首页](../README.md)