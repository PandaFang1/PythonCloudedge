# Chime 模块（chime/）

> 智能门铃 Chime Base — 完整添加流程 + 快捷添加流程 + 删除流程 + 设置模块

## 概览

Chime 模块聚合 CloudEdge 安卓端智能门铃（Chime Base）的端到端测试，
包含 4 个测试场景：

- **完整添加**（`test_full.py`）：按设备类别选择「智能门铃 → Chime Base」→ 9 步配网
- **快捷添加**（`test_quick.py`）：蓝牙区域直接点 SN → 直达 WiFi 输入页 → 6 步配网
- **删除**（`test_delete.py`）：进入设备详情页 → 5 阶段删除流程
- **设置模块**（2026-10-11 全量补齐）：设置页 + 7 个子页面 + 8 个下级页面 PO，
  共 18 个注册页面（`jingle_*_page`）

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
| [jingle-setting-page.md](./jingle-setting-page.md) | 设置页（枢纽：7 个子页面入口 + 推送开关 + 重启/删除） | `JingleSettingPage` |
| [jingle-device-info-page.md](./jingle-device-info-page.md) | 设备信息页（11 个字段 getter + 4 个下级入口） | `JingleDeviceInfoPage` |
| [jingle-bell-dnd-page.md](./jingle-bell-dnd-page.md) | 铃铛勿扰页（时间段列表 + 添加/编辑入口） | `JingleBellDndPage` |
| [jingle-ringtone-page.md](./jingle-ringtone-page.md) | 铃声设置页（音频列表 + 长按录制 + 弹框 + 删除） | `JingleRingtonePage` |
| [jingle-device-share-page.md](./jingle-device-share-page.md) | 设备分享页（添加入口） | `JingleDeviceSharePage` |
| [jingle-sound-page.md](./jingle-sound-page.md) | 声音设置页（扬声器开关 + 事件序列拖动音量） | `JingleSoundPage` |
| [jingle-storage-page.md](./jingle-storage-page.md) | 存储管理页（容量 getter + 格式化弹框仅取消） | `JingleStoragePage` |
| [jingle-general-page.md](./jingle-general-page.md) | 通用设置页（LED/12小时制开关 + 指引/解绑入口） | `JingleGeneralPage` |
| [jingle-device-name-page.md](./jingle-device-name-page.md) | 设备名称页（昵称读写） | `JingleDeviceNamePage` |
| [jingle-device-scene-page.md](./jingle-device-scene-page.md) | 使用场景页（11 场景宫格选定 + 保存） | `JingleDeviceScenePage` |
| [jingle-device-location-page.md](./jingle-device-location-page.md) | 位置管理页（家庭列表/选择/确定） | `JingleDeviceLocationPage` |
| [jingle-device-version-page.md](./jingle-device-version-page.md) | 设备版本页（版本 getter，只读） | `JingleDeviceVersionPage` |
| [jingle-sleep-time-add-page.md](./jingle-sleep-time-add-page.md) | 添加/编辑时间段页（时间选择器 + 星期 + 删除计划） | `JingleSleepTimeAddPage` |
| [jingle-share-type-page.md](./jingle-share-type-page.md) | 分享方式页（二维码/输入账号识别） | `JingleShareTypePage` |
| [jingle-install-guide-page.md](./jingle-install-guide-page.md) | 安装指引页（3 页翻页流，末页保护） | `JingleInstallGuidePage` |
| [jingle-unbind-channel-page.md](./jingle-unbind-channel-page.md) | 解绑设备页（仅识别，删除按钮永不点击） | `JingleUnbindChannelPage` |

## 阅读路径

1. 先读 [jingle-add-module.md](./jingle-add-module.md) 了解完整 + 快捷添加全貌
2. 维护添加页定位器时读 [jingle-add-page.md](./jingle-add-page.md)
3. 删除流程：先读 [jingle-delete-module.md](./jingle-delete-module.md)，定位器细节看 [jingle-delete-page.md](./jingle-delete-page.md)
4. 设置模块：从 [jingle-setting-page.md](./jingle-setting-page.md) 进入页面树，
   按文档导航逐级深入

## 设置模块通用限制（2026-10-11 真机验证）

- **Switch checked 不可靠**：模块内所有开关（推送/LED/12小时制/扬声器/固件自动升级）
  `attr("checked")` 恒 False；扬声器以音量条可见性替代判断，其余用截图比对
- **系统 Toast 不可见**：「设置成功」「录音时间短」等提示对 poco
  accessibility 树不可见，无法自动断言
- **安全红线**：格式化确认、删除设备、解绑确认、指引末页「完成」永不点击
- **保存类验证闭环**：设备昵称（改回）、自定义铃声（删除）、勿扰时间段（删除计划）
  均已验证「写入→断言→恢复」闭环；使用场景保存后原场景无 UI 可读（测试设备保持）

## 与其他模块的关系

- **上游**：[设备管理模块（device_mgmt/）→](../device_mgmt/README.md)（依赖策略模式 Flow 基类 + 选择设备类别页）
- **上游**：[账号模块（account/）→](../account/README.md)（需要登录态）
- **共享 fixture**：`android_logged_in` / `android_category_page` 定义在 `testcases/android/conftest.py`
- **探测工具**：[tools/explore_page.py](../../../tools/README.md)（子页面下一级探测，
  NAVIGATE_MAP 已登记全部 18 个 jingle 页面）

## 导航

- 上一篇：[设备管理模块（device_mgmt/）←](../device_mgmt/README.md)
- 下一篇：[参考与工具（reference/）→](../reference/README.md)
- [返回文档中心](../../README.md)
- [返回项目首页](../../../README.md)
