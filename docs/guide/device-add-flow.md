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
flow.run(sn="131903239", ssid="xiaoMI-楼顶拷机IPC", password="56565099")
```

## 6. 真机测试数据（用户已提供）

```python
DEFAULT_WIFI_SSID = "xiaoMI-楼顶拷机IPC"     # 中文 SSID，需用 ADBKeyboard 输入
DEFAULT_WIFI_PASSWORD = "56565099"
DEFAULT_DEVICE_SN = "131903239"
```

ADBKeyboard 已安装（`com.android.adbkeyboard/.AdbIME`），可通过
`adb shell am broadcast -a ADB_INPUT_TEXT --es msg "xiaoMI-楼顶拷机IPC"`
输入中文 SSID。

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

### 7.4 待 PAGE 6-11 dump 替换的占位符

| 步骤 | 占位符 | 备注 |
|---|---|---|
| 6 弹框 | `tv_dialog_title` / `tv_dialog_ssid` / `tv_dialog_password` / `btn_determine` | 需 Chime Base 配对后真机 dump |
| 7 连接网络 | `pb_loading` | 同上 |
| 8 成功页 | `btn_done` | 同上 |
| 9 安装指引 | `tv_next`（共用）| 同上 |
| 10 网络诊断 | `btn_back_home` | 同上 |
| 11 主页设备列表 | `rv_device_list` / `tv_device_name` | 同上 |

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
- **当前阻塞**：
  - Chime Base 配对态（搜不到时跑不通）
  - 4-6 个 PAGE 待 dump（弹框 / 连接 / 成功 / 安装 / 诊断 / 主页）
  - 当前 `add_device_by_category("智能门铃", "Chime Base")` 跳转的 Activity
    实际是 PowerOnActivity 而非预期 ResetDeviceActivity

## 11. 已知限制与约定

- **忽略提示文案**（用户已确认）：不等待/不断言「WiFi 搜索中」等提示文案，
  无线连接页直接以 `rv_wifi_list` 渲染完成判定就绪
- **WiFi 频段**（用户已确认）：**2.4G / 5G 均支持**，不按频段过滤或断言
- **中文 SSID 输入**：需用 ADBKeyboard（已装），不能直接 `input text`
- **PAGE 6-11 占位符**：弹框 / 连接 / 成功 / 安装 / 诊断 / 主页 6 个页面
  的 resource-id 仍为占位符，需在 Chime Base 配对后真机 dump 替换
- **Chime Base 配对态**：必须物理上电 + 进入配对态（指示灯蓝灯闪烁），
  否则「搜到的设备列表」为空，测试卡在 `click_add_button_by_sn`
- **`xiaoMI-楼顶拷机IPC` 不在默认 WiFi 列表**：需手动输入或 ADBKeyboard

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
- 相关：[PO 模式基类与扩展指南](../README.md)
- 框架：[执行规则](../README.md)
