# 设备添加流程策略模式（device-add-flow）

> 在「选择设备类别」页之后，CloudEdge app 的添加流程会按设备类型走不同路径
> （智能门铃 Chime Base / 电池摄像机 / 常电摄像机 / 4G 摄像机 / 摇头机 等）。
> 本模块用**策略模式**抽象这一层，注册 5 类设备类型，**端到端实现 1 款 + 4 款存根**，
> 便于后续真机接入时按模板补齐。

## 1. 设计目标

- 不同设备类型走不同配网流程（按设备走不同添加流程）
- 业务用例**只关心调用入口**，不感知具体设备类型差异
- 新增设备类型只需写一个 Flow 子类 + 注册到工厂
- 单测可验证分发与存根行为（不依赖真机）

## 2. 架构图

```
业务用例
    │
    ▼
add_device_category_page.start_flow(category, type, type_des)
    │   (1) 调 add_device_by_category() 选大/小类别+跳转 PowerOnActivity
    │   (2) 调 DeviceFlowFactory.create() 返回 Flow 实例
    ▼
DeviceFlowFactory.create(category, type, type_des, poco, udid)
    │   按 (category, type) 从 REGISTRY 分发
    ▼
BaseAddDeviceFlow 子类（如 DoorbellChimeBaseFlow）
    │
    ▼
.run(sn, ssid, password, ...)  模板方法按序执行 9 步
    │
    ├── 步骤 1-3: 物理准备 → ChimePreSetupPages
    │     ├── PAGE 1: PowerOnActivity - 选择 Chime Base 页面（安装位置）
    │     ├── PAGE 2: PowerOnActivity - 接入电源
    │     └── PAGE 3: PowerOnActivity - 请点按复位键（添加摄像机）
    ├── 步骤 4: 设备配对 → ChimeSelectDevicePage
    │     └── PAGE 4: RouterWiFiActivity - 搜到的设备列表 BottomSheet
    ├── 步骤 5-6: 无线连接 → ChimeWifiConfigPage
    │     ├── PAGE 5: AddDeviceGetWifiListActivity - WiFi 输入
    │     └── PAGE 6: WiFi 信息确认弹框（待真机 dump）
    ├── 步骤 7-8: 配网完成 → ChimeConnectionPages
    │     ├── PAGE 7: 连接网络（转圈）
    │     └── PAGE 8: 连接成功（下一步/完成）
    └── 步骤 9-10: 收尾 → ChimePostSetupPages
          ├── PAGE 9: 安装指引（下一步）
          └── PAGE 10: 网络诊断（返回首页）→ 主页
```

## 3. 目录结构

```
pages/android/add_device_flow/
├── __init__.py                       # 对外公共导出
├── base_add_device_flow.py           # 抽象基类 + 10 步模板
├── doorbell_chime_base_flow.py       # ★ 端到端实现（智能门铃 + Chime Base）
├── battery_camera_flow.py            # 存根（电池摄像机）
├── wired_camera_flow.py              # 存根（常电摄像机）
├── mobile_4g_camera_flow.py          # 存根（4G 摄像机）
├── ptz_camera_flow.py                # 存根（摇头机）
├── factory.py                        # DeviceFlowFactory 工厂 + REGISTRY
└── pages/                            # 下游页面 PO（智能门铃专用）
    ├── __init__.py
    ├── chime_pre_setup_pages.py      # 安装位置 + 接入电源 + 请点按复位键
    ├── chime_device_pairing_pages.py # 选设备 + 无线连接 + 弹框
    ├── chime_connection_pages.py     # 连接网络 + 连接成功
    └── chime_post_setup_pages.py     # 安装指引 + 网络诊断
```

## 4. 智能门铃 Chime Base 完整路径（真机验证）

| 步骤 | 页面 | Activity | resource-id 关键 | 关键操作 |
|---|---|---|---|---|
| 1 | 选择 Chime Base 页面（安装位置）| PowerOnActivity | `tv_power_on_title`=`安装位置`、`tv_next` | 点「下一步」 |
| 2 | 接入电源 | PowerOnActivity | `tv_des_title`=`接入电源`、`tv_next` | 点「下一步」 |
| 3 | 请点按复位键 | PowerOnActivity | `tv_des_title`=`请点按复位键`、`tv_next` | 用户物理按 Chime Base 复位键 + 点「下一步」 |
| 4 | 搜到的设备列表 | RouterWiFiActivity (BottomSheet) | `design_bottom_sheet`、`recyclerView`、`tv_model` | 点目标 SN 行（整行 clickable） |
| 5 | 无线连接（WiFi 输入）| AddDeviceGetWifiListActivity | `wifi_name_et`、`pwd_et`、`rv_wifi_list` | 选/输入 SSID + 密码 + 点「下一步」 |
| 6 | WiFi 信息确认弹框 | AddDeviceGetWifiListActivity (Dialog) | `tv_dialog_*`（待 PAGE 6 dump 替换）| 比对弹框内容 + 点「确定」 |
| 7 | 连接网络 | 待 PAGE 7 dump | `pb_loading`（占位符）| 等待转圈消失 |
| 8 | 连接成功 | 待 PAGE 8 dump | `btn_done`（占位符）| 「下一步」→「完成」 |
| 9 | 安装指引 | 待 PAGE 9 dump | `tv_next` | 点「下一步」 |
| 10 | 网络诊断 | 待 PAGE 10 dump | `btn_back_home` | 点「返回首页」+ 断言首页含 SN |
| 11 | 主页 | MainActivity | `rv_device_list`、`tv_device_name` | 设备列表断言 |

## 5. 关键设计要点

### 5.1 模板方法模式

`run()` 是模板方法，**子类一般不重写**，而是重写具体的步骤方法。
如需前后置逻辑（如初始化额外状态），可在子类重写 `run()`，但**必须**
调用 `super().run(**kwargs)`。

```python
class MyFlow(BaseAddDeviceFlow):
    def run(self, **kwargs):
        # 1. 前后置逻辑
        self.setup_extra_state()
        # 2. 调用基类模板方法
        super().run(**kwargs)
        # 3. 后续清理
        self.cleanup()
```

### 5.2 工厂分发

`DeviceFlowFactory.create()` 按 `(category, type_name)` 元组从
`REGISTRY: Dict[Tuple[str, str], Type[BaseAddDeviceFlow]]` 查表分发：

- **key 联合**：用 `(category, type_name)` 而非仅 `type_name`，避免同名
  类型在不同大类别下误分发（如 `Chime Base` 仅在「智能门铃」下）
- **type_des 不参与分发**：仅用于 `select_device_type()` 消歧同名项
- **未命中抛异常**：`UnsupportedDeviceTypeError(ElementNotFoundError)`，
  异常含已支持类型列表，便于排查

### 5.3 存根策略

未实现的 4 个 Flow 类（电池/常电/4G/PTZ）继承基类，**不重写任何步骤方法**。
调用 `.run()` 时第一步就抛 `FlowStepNotImplementedError`，异常文案含
「请在 XxxFlow 中重写该步骤」+ 步骤名 + Flow 类名，便于排查。

```python
flow = DeviceFlowFactory.create("电池摄像机", "电池摄像机", "(2.4G Wi-Fi)", ...)
flow.run()  # → 立即抛 FlowStepNotImplementedError
```

**优势**：
- 工厂分发永远成功（不会因某 Flow 未实现而无法 import）
- 业务调用方可以先看 Flow 类名再决定是否调用 run
- 新增设备类型时只重写需要的步骤，其余继承基类默认行为

### 5.4 硬件交互处理

部分步骤需物理硬件操作（按住复位按钮、摄像头扫码等）无法在 CI 自动化。
`BaseAddDeviceFlow` 提供 `mark_step(step_name, reason)` 工具：

```python
def power_on_device(self, **kwargs):
    self.mark_step("power_on_device", "需用户按住 Chime Base 复位按钮 5 秒")
```

**软信号** vs 硬异常：
- `HardwareInteractionRequired` 是 `Exception` 子类，**不计入错误日志**
- 业务测试可捕获做特殊处理（mock 设备状态 / 跳过）

### 5.5 入口衔接

`add_device_category_page.start_flow(category, type_name, type_des)` 一站式：

```python
add_device_page = PageFactory.create(platform, "add_device_category_page", ...)
flow = add_device_page.start_flow("智能门铃", "Chime Base")
flow.run(sn="<SN>", ssid="<SSID>", password="<密码>")
```

## 6. 真机测试数据

`DoorbellChimeBaseFlow` 内置默认测试数据（可在 `run()` / `add_jingle_device()`
时以参数覆盖，或通过环境变量注入）：

| 常量 | 默认值 |
|---|---|
| `DEFAULT_DEVICE_SN` | `131805981` |
| `DEFAULT_WIFI_SSID` | `TP-LINK_BEB6` |
| `DEFAULT_WIFI_PASSWORD` | `18268056861` |

```bash
export CLOUDEDGE_DEVICE_SN="<设备SN>"
export CLOUDEDGE_WIFI_SSID="<WiFi名称>"
export CLOUDEDGE_WIFI_PASSWORD="<WiFi密码>"
```

### 6.1 ADBKeyboard 输入法管理（chime_device_pairing_pages.py）

WiFi 名称/密码输入需要 ADBKeyboard（`com.android.adbkeyboard/.AdbIME`），
PO 已封装完整生命周期：

- `switch_to_adb_keyboard()`：切到 ADBKeyboard（返回原输入法 ID）。
  ADBKeyboard 不渲染键盘视图，点击输入框时系统键盘不会遮挡 `pwd_et`
- `input_ssid()` / `input_password()`：通过
  `adb shell am broadcast -a ADB_INPUT_TEXT --es msg "<文本>"` 输入
- `restore_ime(ime_id)`：输入完成后还原原输入法（如讯飞）
- 输入密码后通过 `uiautomator dump` 回读校验（长度比对，失败自动重试）

### 6.2 登录后新手引导处理（main_page.py）

登录成功后 app 可能弹**新手引导浮层**（多页，遮挡主页元素导致
「添加设备」点击失败）。`CloudEdgeMainPage.handle_guide()` 处理：

- 逐页点击「下一步」（`GUIDE_BTN_NEXT`），最多 10 页防死循环
- 末页按钮候选 `GUIDE_BTN_DONE_CANDIDATES`（按优先级）：
  「知道了」/「完成」/「立即体验」/「开始使用」/「进入」
  （真机 2026-10-09 验证：末页按钮为「知道了」）
- 处理完毕后确认无引导按钮残留才返回

`testcases/android/test_add_device.py` 的 `_open_category_page()` 中，
登录后先 `sleep 3s` 等主页稳定 → `handle_guide()` → 再 `sleep 2s` →
点「添加设备」，真机验证稳定。

### 6.3 快捷添加流程（蓝牙直达，2026-10-10 真机验证）

除完整流程外，还有一条**快捷路径**：在「选择设备类别」页顶部
蓝牙区域**直接点击设备 SN 号**，跳过「安装位置/接入电源指引」和
「连接设备」页，直达 WiFi 信息输入页；后续步骤与完整流程一致。

```
完整流程：类别页 → PowerOn 指引×2 → 连接设备页(点添加) → WiFi 输入 → ...
快捷流程：类别页 → 蓝牙区域点 SN（或「查看更多」抽屉下滑查找）
              → WiFi 输入 → 弹框确定 → 等待入网 → 成功页
              → 设置房间 → 安装指引 → 网络诊断 → 返回首页 → 主页断言
```

三个层次封装：

| 层次 | 入口 | 说明 |
|---|---|---|
| PO | `CloudEdgeAddDeviceCategoryPage.select_bt_device_auto(sn)` | 蓝牙区域自动查找并点击 SN：可见列表直接命中；未命中且有「查看更多」→ 展开底部抽屉逐屏上滑查找（`_swipe_up_bt_sheet`，滑到底自动停） |
| Flow | `DoorbellChimeBaseFlow.run_quick(**kwargs)` | 快捷模板方法：跳过步骤 1-3，从步骤 4（`wait_wifi_ready`）开始执行至主页断言，步骤 4-9 与 `run()` 完全一致 |
| 门面 | `JingleAddPage.add_jingle_device_quick(sn, ssid, password, ...)` | 一站式：类别页 `select_bt_device_auto` → `run_quick` → 主页断言 |

对应用例：`testcases/android/test_add_doorbell_chime_quick.py`
（结构同完整流程用例，仅第 3 步换为快捷入口）。

**注意事项**：
- 蓝牙区域（`ll_bt`）仅在附近有处于配对态的设备时显示；设备配网
  成功后即离开配对态，重跑前需按复位键重置（或先从账号删除设备）
- 快捷流程跳过类型选择，无法保证设备类型匹配——蓝牙区域展示的
  即为可直连的设备，直接点 SN 即可

## 7. 真机 resource-id 汇总（已替换到 POs）

### 7.1 PowerOnActivity（步骤 1-3 共用）

| resource-id | 用途 | 备注 |
|---|---|---|
| `iv_back` | 返回 | 顶部左 |
| `tv_title` | 页面标题 | "添加Chime Base"（步骤 1-2）/ "添加摄像机"（步骤 3）|
| `tv_power_on_title` | 步骤 1 标题 | "安装位置" |
| `tv_power_on_des` | 步骤 1 描述 | 长描述 |
| `tv_des_title` | 步骤 2-3 标题 | "接入电源" / "请点按复位键" |
| `tv_des` | 步骤 2-3 描述 | |
| `viewPager` | 翻页器 | 步骤 2-3 |
| `iv_play_sound` | 播放提示音 | 步骤 3 |
| `sdv_sketch` | 示意图 | |
| `tv_problem2` / `tv_problem3` | 问题反馈 | |
| `ll_problem2` | 问题容器 | |
| `layout_next` | 下一步容器 | |
| `tv_next` | 下一步按钮 | "下一步" |

### 7.2 RouterWiFiActivity（步骤 4 - BottomSheet 设备列表）

| resource-id | 用途 | 备注 |
|---|---|---|
| `touch_outside` | BottomSheet 外部点击 | |
| `design_bottom_sheet` | BottomSheet 容器 | |
| `iv_close` | 关闭 BottomSheet | |
| `recyclerView` | 设备列表 | |
| `iv_pic` | 设备图标 | |
| `tv_model` | 设备 SN 文本 | "131903239" 等数字串 |

### 7.3 AddDeviceGetWifiListActivity（步骤 5）

| resource-id | 用途 | 备注 |
|---|---|---|
| `iv_back` | 返回 | |
| `iv_submit` | 提交 | |
| `tv_top_title` | 顶部标题 | "无线连接" |
| `tv_alert` | 提示语 | |
| `rl_wifi_name` | WiFi 名容器 | |
| `wifi_name_et` | SSID 输入框 | |
| `tv_change_wifi` | 切换 WiFi | |
| `ll_wifi_list` | WiFi 列表容器 | |
| `rv_wifi_list` | WiFi 列表 | |
| `tv_wifi_name` | 列表中 WiFi 名 | |
| `pwd_et` | 密码输入框 | |
| `tv_pwd_chk` | 显示/隐藏密码 | |
| `tv_tip` | 提示 | |
| `layout_next` | 下一步容器 | |
| `tv_next` | 下一步按钮 | "下一步" |

### 7.4 真机验证的后续页面 resource-id（2026-10-09 全流程 dump）

| 步骤 | Activity | 关键 resource-id |
|---|---|---|
| 3 连接设备 | `BleSearchDeviceActivity`（整页，非 BottomSheet） | `tv_title`='连接设备'、`tv_device_name`=SN、`tv_next`='添加'（行右侧） |
| 5 无线连接 | `AddDeviceGetWifiListActivity` | `wifi_name_et`、`tv_change_wifi`（**SSID 框右侧箭头，点击收起列表露出密码框**）、`pwd_et`、`tv_next`='下一步' |
| 6 弹框 | 同上 Activity 内 | `title`='提示'、`message`（含 'WIFI名称：xxx\nWIFI密码：yyy'，解析比对）、`positiveButton`='确定'、`negativeButton`='取消' |
| 7 连接网络 | `SmartWiFiActivity` | `tv_title`='连接网络'、`tv_time` 倒计时、`tvDeviceRegister`='注册到云端'（完成判定=成功页 `tv_find_device` 出现） |
| 8 连接成功 | `SearchDeviceActivity` | `tv_title`='连接成功'、`tv_find_device`='添加设备成功'、`scan_camera_name`=SN、`pps_back_home`='下一步' |
| 8.5 设置房间 | `AddDeviceSetRoomActivity` | `tv_device_name`=SN、`tv_category_name`=房间名、`pps_back_home`='完成' |
| 9 安装指引 | `GuideRightPlacePicActivity` | `tv_title`='安装指引'、`tv_content`、`tv_next_vp`='下一步' |
| 10 网络诊断 | `NetworkDiagnosticActivity` | `tv_title`='网络诊断'、`tv_back_home`='返回首页'、`next`='检查更新' |
| 11 主页 | `MainActivity` | `tvCameraName`（摄像机）、`tvJingleNeutralName`=SN（Chime Base，状态 `tvJingleNeutralOnline`）；PO 兼容旧 id `tvDeviceName`/`tvJingleBaseName` |

## 8. 新增设备类型模板

按以下 3 步新增一种设备类型的完整配网流程：

### Step 1: 新建 Flow 子类

```python
# pages/android/add_device_flow/my_device_flow.py
from pages.android.add_device_flow.base_add_device_flow import BaseAddDeviceFlow


class MyDeviceFlow(BaseAddDeviceFlow):
    FLOW_NAME = "MyDeviceFlow"

    def __init__(self, poco, udid, category="MyCategory", type_name="MyType", type_des=None):
        super().__init__(poco, udid, category, type_name, type_des)
        # 如需，构造下游 PO
        # self.my_page = MyDownstreamPage(poco, udid)

    def wait_chime_install_page(self, timeout=30.0):
        # 适配本设备的「步骤 1」逻辑
        ...

    # 重写其他有差异的步骤
```

### Step 2: 注册到工厂

```python
# pages/android/add_device_flow/factory.py
from pages.android.add_device_flow.my_device_flow import MyDeviceFlow

REGISTRY: Dict[Tuple[str, str], Type[BaseAddDeviceFlow]] = {
    # ... 现有注册
    ("MyCategory", "MyType"): MyDeviceFlow,  # 新增
}
```

### Step 3: 在 `__init__.py` 导出

```python
# pages/android/add_device_flow/__init__.py
from pages.android.add_device_flow.my_device_flow import MyDeviceFlow

__all__ = [
    # ... 现有导出
    "MyDeviceFlow",  # 新增
]
```

## 9. 单测

`tests/test_device_flow_factory.py` 覆盖（28 个用例，0.22s 跑完）：

- **TestFactoryDispatch**：5 类设备正确分发到对应 Flow 类
- **TestFactoryHelpers**：`supported_types()` / `is_supported()` / `get_flow_class()` 行为
- **TestStubFlowBehavior**：4 个存根 Flow 调 run() 第一步抛 `FlowStepNotImplementedError`
- **TestDoorbellChimeBaseFlowConstruction**：端到端 Flow 构造与基本属性
- **TestRegistryIntegrity**：REGISTRY 完整性（5 项 / 类型正确 / key 格式）

```bash
python -m pytest tests/test_device_flow_factory.py -v
```

## 10. 端到端用例

`testcases/android/test_add_doorbell_chime_base.py` 走完整 10 步配网：

- **默认 skip**：因需真实 Chime Base 设备 + 真实 WiFi，`HARDWARE_READY=False`
- **真机调试**：将 `HARDWARE_READY` 改为 `True` 启用
- **数据驱动**：`sn` / `ssid` / `wifi_password` 三个参数可被 pytest fixture 覆盖
- **真机验证进度**（2026-10-09，Redmi Note 11 5G，SN=131805981）：
  登录 → 引导处理 → 类别页 → PowerOn 三步 → 选设备 → WiFi 输入 →
  确认弹框 → 配网成功 → 设置房间 → 网络诊断「返回首页」**全流程已打通**
- **快捷流程用例**：`testcases/android/test_add_doorbell_chime_quick.py`
  （2026-10-10 真机验证通过：蓝牙区域点 SN 直达 WiFi 输入页 → 配网
  成功 → 主页断言设备列表含 SN，设备显示「在线」）
- **本轮修复**：
  - `run()` 模板方法中 `wait_wifi_ready(timeout=)` → `timeout_loading=`、
    `wait_network_connected(timeout=)` → `timeout_connecting=`（参数名
    与子类方法签名不匹配导致 TypeError）
  - `assert_device_added()` 加轮询重试：点「返回首页」后主页设备列表
    需渲染时间，立即查询 `tvDeviceName` 会抛 `PocoNoSuchNodeException`；
    现在在 timeout 内每 2s 轮询直至设备列表含 SN
  - 安装指引页（步骤 9）不强制出现，未加载时记 WARNING 并跳过，
    按网络诊断页/主页继续

## 11. 已知限制与约定

- **忽略提示文案**（用户已确认）：不等待/不断言「WiFi 搜索中」等提示文案，
  无线连接页直接以 `rv_wifi_list` 渲染完成判定就绪
- **WiFi 频段**（用户已确认）：**2.4G / 5G 均支持**，不按频段过滤或断言
- **中文 SSID 输入**：需用 ADBKeyboard（已装），不能直接 `input text`；
  输入 SSID 后必须点 SSID 框右侧箭头（`tv_change_wifi`）收起 WiFi 列表，
  密码框 `pwd_et` 才会渲染出来
- **Chime Base 配对态**：必须物理上电 + 进入配对态（指示灯蓝灯闪烁），
  否则「搜到的设备列表」为空，测试卡在 `click_add_button_by_sn`。
  **注意**：设备配网成功后即离开配对态，重跑用例前需按复位键重置设备
  （或先从账号删除该设备）
- **重复添加**：2026-10-09 真机全流程验证（SN 131903239、131805981）
  成功后，Chime Base 已绑定测试账号；再次试跑需先重置设备

## 12. 后续扩展

| 优先级 | 任务 | 价值 |
|---|---|---|
| 高 | 真机 dump PAGE 6-11 替换占位符 | 端到端用例可启用 |
| 高 | ADBKeyboard 输入中文 SSID 的封装工具 | 端到端用例可输入实际 SSID |
| 中 | 实现 `BatteryCameraFlow`（按住复位 + 蓝牙配对） | 覆盖电池摄像机业务 |
| 中 | 实现 `WiredCameraFlow`（插电 + WiFi 配网） | 覆盖常电摄像机业务 |
| 低 | 实现 `Mobile4GCameraFlow` / `PtzCameraFlow` | 补齐 4G/PTZ 业务 |
| 低 | 增加 iOS 端 Flow 子类（云际 app） | 跨端支持 |

## 13. 文档导航

- 上一篇：[「选择设备类别」页](./add-device-category-page.md)
- 相关：[jingle 添加页面](./jingle-add-page.md)
- 相关：[jingle 删除页面](./jingle-delete-page.md)
- 相关：[PO 模式基类与扩展指南](../README.md)
- 框架：[执行规则](../README.md)
