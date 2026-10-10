# Jingle 添加模块 — 智能门铃 Chime Base 完整流程 + 快捷流程

> 真机全流程验证：完整流程 2026-10-09（Redmi 22101317C / cfed8c100822，SN 131903239）
> 快捷流程验证：2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK，SN 131805981）

## 1. 模块概述

**Jingle 添加模块**（`testcases/android/jingle_add/`）聚合 CloudEdge 安卓端
智能门铃（Chime Base）添加的两种路径：

- **完整流程**（`test_full.py`）：按设备类别选择「智能门铃 → Chime Base」→ 9 步配网
- **快捷流程**（`test_quick.py`）：蓝牙区域直接点 SN → 直达 WiFi 输入页 → 6 步配网

```
Jingle 添加模块的 2 条路径
├── test_full.py    → 完整配网（11 个页面/阶段）
└── test_quick.py   → 快捷配网（跳过前 3 个阶段，从 WiFi 输入开始）
```

## 2. 包含的测试用例

| 测试函数 | allure 标签 | 验证内容 |
|---|---|---|
| `test_add_doorbell_chime_base` | epic=设备, feature=添加设备, story=智能门铃 Chime Base 端到端 | 选类别 → 选 Chime Base → 9 步配网 → 主页断言设备列表含 SN |
| `test_add_doorbell_chime_quick` | epic=设备, feature=添加设备, story=智能门铃 Chime Base 快捷流程 | 蓝牙点 SN → 直达 WiFi → 6 步配网 → 主页断言设备列表含 SN |

### 2.1 完整流程 vs 快捷流程

| 维度 | 完整 `test_full.py` | 快捷 `test_quick.py` |
|---|---|---|
| 入口动作 | 选「智能门铃」→「Chime Base」 | 类别页蓝牙区域**直接点设备 SN** |
| 跳过的页面 | — | 安装位置指引、接入电源指引、连接设备页 |
| 主页断言 | 主页设备列表含 SN | 主页设备列表含 SN |

## 3. 模块目录结构

```
testcases/android/jingle_add/
├── __init__.py             # 子包标识 + 模块说明
├── conftest.py             # 模块 fixture：jingle_category_page
├── test_full.py            # 完整配网流程
└── test_quick.py           # 快捷配网流程
```

## 4. 依赖的 Page Objects

| 页面类 | 工厂 key | 职责 |
|---|---|---|
| `CloudEdgeLoginPage` | `("android", "login_page")` | 启动/登录（如需兜底） |
| `CloudEdgeMainPage` | _(直接构造)_ | 主页（添加设备入口 + 新手引导） |
| `CloudEdgeAddDeviceCategoryPage` | `("android", "add_device_category_page")` | 选择设备类别页（方式 A 按类别 + 方式 B 蓝牙） |
| `JingleAddPage` | `("android", "jingle_add_page")` | Jingle 一站式添加门面（`add_jingle_device` / `add_jingle_device_quick`） |
| `DoorbellChimeBaseFlow` | _(内部使用)_ | 9 步配网策略类（含 `run()` / `run_quick()`） |

## 5. fixture 依赖链

```
android_preserved_app（testcases/android/conftest.py）
    ↓ force-stop + 启动 + 按需登录（不 pm clear，保留账号/设备数据）
jingle_category_page（jingle_add/conftest.py）
    ↓ handle_guide + open_add_device_category_page + 3 次重试
test_full / test_quick 用例
```

## 6. 依赖的测试基础设施

`test_add_device.py`（位于 `testcases/android/` 根目录）是 jingle_add 的**前置基础设施**，
提供「选择设备类别」页的两种方式（按类别 + 蓝牙）的页面级验证。jingle_add 在其基础上
组合出端到端配网流程。

- `test_add_device.py::test_add_device_by_category` — 验证按类别选择进入配网页
- `test_add_device.py::test_add_device_by_bluetooth` — 验证蓝牙区域 + 「查看更多」抽屉

## 7. 依赖的设备添加流程

`pages/android/add_device_flow/` 是策略模式 + 工厂分发的设备添加流程层：

```
BaseAddDeviceFlow（基类）
    ↓ 继承
DoorbellChimeBaseFlow（已实现：9 步完整流程 + 6 步快捷流程）
BatteryCameraFlow / WiredCameraFlow / Mobile4GCameraFlow / PtzCameraFlow（存根）
    ↑
DeviceFlowFactory（按 (category, type_name) 分发）
```

注册表：

```python
# pages/android/add_device_flow/factory.py
REGISTRY = {
    ("智能门铃", "Chime Base"): DoorbellChimeBaseFlow,  # ★ 端到端已实现
    ("电池摄像机", "电池摄像机"): BatteryCameraFlow,     # 存根
    ("常电摄像机", "常电摄像机"): WiredCameraFlow,       # 存根
    ("4G摄像机", "4G摄像机"): Mobile4GCameraFlow,         # 存根
    ("摇头机", "摇头机"): PtzCameraFlow,                 # 存根
}
```

## 8. 运行命令

```bash
# 整模块
pytest testcases/android/jingle_add/ --platform android

# 单个测试
pytest testcases/android/jingle_add/test_full.py --platform android
pytest testcases/android/jingle_add/test_quick.py --platform android

# 通过环境变量注入真机测试数据
export CLOUDEDGE_DEVICE_SN=131805981
export CLOUDEDGE_WIFI_SSID=TP-LINK_BEB6
export CLOUDEDGE_WIFI_PASSWORD=18268056861
pytest testcases/android/jingle_add/test_full.py --platform android
```

## 9. 与其他模块的关系

```
   ┌──────────────┐
   │  账号模块     │ 提供登录态
   │  (account)   │
   └──────┬───────┘
          ↓
┌──────────────────────┐
│  Jingle 添加模块     │ ← 本模块
│  (jingle_add)        │
└──────────┬───────────┘
           │ 添加完成后，设备进入账号
           ↓
┌──────────────────────┐
│  Jingle 删除模块     │ 删除由本模块添加的设备
│  (jingle_delete)     │
└──────────────────────┘
```

## 10. 真机验证记录

| 用例 | 真机 | 验证时间 | SN | WiFi | 备注 |
|---|---|---|---|---|---|
| `test_full` | Redmi 22101317C | 2026-10-09 | 131903239 | — | 完整 11 阶段流程 |
| `test_quick` | Redmi Note 11 5G | 2026-10-10 | 131805981 | TP-LINK_BEB6 | 蓝牙区域点 SN 直达 |
| `test_add_doorbell_chime_131903227` | Redmi 22101317C | 2026-10-10 | 131903227 | xiaoMI-楼顶拷机IPC | 完整配网 + **性能基线 96.71s**（详见 §12） |

## 11. 相关页面/流程文档

- [智能门铃 Chime Base 一站式添加页（jingle_add_page）](./jingle-add-page.md)
- [选择设备类别页（add_device_category_page）](./add-device-category-page.md)
- [设备添加流程（add_device_flow）](./device-add-flow.md)

## 12. 性能基线与优化记录（2026-10-10）

`test_add_doorbell_chime_131903227`（SN 131903227 / WiFi xiaoMI-楼顶拷机IPC /
Redmi 22101317C）首次跑通耗时 ~151s，优化后 **96.71s**（-36%）。

| 步骤 | 优化前 | 优化后 | 节省 |
|---|---:|---:|---:|
| `wait_wifi_ready`（最大瓶颈） | 60.44s | **8.35s** | -52.09s（-86%） |
| `wait_network_connected`（次大瓶颈） | 43.74s | 42.91s | -0.83s（设备真实入网耗时，不可省） |
| 其他 8 步 | 16.29s | 35.63s（含 input_wifi_credentials 11.24s） | — |
| **9 步 TOTAL** | **120.47s** | **86.89s** | **-33.58s（-28%）** |
| **用例总耗时** | **~151s** | **96.71s** | **-54s（-36%）** |

**根因**：`DoorbellChimeBaseFlow.wait_wifi_ready` 串行等两次 `RV_WIFI_LIST`
渲染（30s + 30s），但走「手动输入 SSID」路径根本不用列表项；APP 端列表是
异步渲染的，30s 几乎必超时；且 `wait_wifi_ready` 不检查返回值。

**修复**（2 处 + 1 bug）：
1. `ChimeWifiConfigPage.wait_for_page_loaded` 改为等 `wifi_name_et`（SSID 输入框，< 1s 就绪）
2. `DoorbellChimeBaseFlow.wait_wifi_ready` 去掉冗余第二次等待 + `if not ... raise`
3. `BaseAddDeviceFlow.log_step` 兼容 `开始（...）` 带后缀的「开始」日志（之前 3 步耗时丢失）；新增 `print_step_durations()` 自动打印耗时表

**详细耗时表 / 根因 / 教训**：见 [jingle-add-page.md §8](./jingle-add-page.md#8-性能基线与优化记录2026-10-10)

---

## 文档导航

- 上一篇：[账号模块文档 ←](./account-module.md)
- 下一篇：[Jingle 删除模块文档 →](./jingle-delete-module.md)
- [返回文档中心](../README.md) · [返回项目首页](../../README.md)
