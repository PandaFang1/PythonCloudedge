# 智能门铃 Chime Base 一站式添加页面（jingle_add_page）

> 真机全流程验证：2026-10-09（Redmi 22101317C / cfed8c100822，SN 131903239）
> 快捷流程验证：2026-10-10（Redmi Note 11 5G / TC55LJMR59W8ZPRK，SN 131805981）

## 1. 概述

`JingleAddPage`（工厂页面名 `jingle_add_page`，文件
`pages/android/jingle_add_page.py`）是智能门铃 Chime Base 添加的
**一站式门面 PO**：封装从「选择设备类别」页开始，到「添加完成
（主页断言设备列表含 SN）」的完整流程。

对用例暴露两个入口：

```python
jingle_page = PageFactory.create(
    "android", "jingle_add_page", poco=poco, udid=udid,
)
# 入口 1：完整流程（类别选择 → 指引×2 → 选设备 → WiFi → ... → 主页断言）
devices = jingle_page.add_jingle_device()  # 全默认参数（环境变量注入）
# 或直接以参数覆盖测试数据
devices = jingle_page.add_jingle_device(
    sn="<SN>", ssid="<SSID>", password="<密码>",
)
# 入口 2：快捷流程（蓝牙区域直接点 SN → 直达 WiFi 输入页 → 后续同完整流程）
devices = jingle_page.add_jingle_device_quick(
    sn="<SN>", ssid="<SSID>", password="<密码>",
)
```

### 1.1 快捷流程 vs 完整流程

| | 完整 `add_jingle_device()` | 快捷 `add_jingle_device_quick()` |
|---|---|---|
| 入口动作 | 选「智能门铃」→「Chime Base」 | 类别页蓝牙区域**直接点设备 SN** |
| 跳过的页面 | — | 安装位置指引、接入电源指引、连接设备页 |
| 进入方式 | `start_flow()` → `Flow.run()`（步骤 1-9） | `select_bt_device_auto(sn)` → `Flow.run_quick()`（步骤 4-9） |
| 后续步骤 | WiFi 输入 → 弹框 → 入网 → 设置房间 → 安装指引 → 网络诊断 → 主页断言 | **完全一致** |
| 蓝牙区域 SN 未直接可见 | — | 自动点「查看更多」展开抽屉，逐屏上滑查找（滑到底自动停） |
| 前提 | 设备已上电（会在连接设备页被搜到） | 设备处于配对态（蓝牙区域 `ll_bt` 可见） |

## 2. 完整流程记录（11 个页面/阶段，真机逐步验证）

前置：主页 `ivAddDevice` → 弹窗「添加设备」条目 → 进入「选择设备类别」页。

| # | 阶段 | Activity | 操作 | 关键 resource-id |
|---|---|---|---|---|
| 0 | 选择设备类别页 | `SelectDeviceTypeActivity` | 选大类别「智能门铃」→ 等右侧刷新 → 选小类别「Chime Base」 | `recyclerview_main` / `tv_category_name` / `tv_device_name` |
| 1 | 选择 Chime Base（安装位置） | `PowerOnActivity` | 提示语带安装位置，点「下一步」 | `tv_des_title`（'安装位置'）/ `tv_next` |
| 2 | 接入电源 | `PowerOnActivity` | 提示语带接入电源，点「下一步」 | `tv_des_title`（'接入电源'）/ `tv_next` |
| 3 | 连接设备 | `BleSearchDeviceActivity`（整页列表） | 在搜到的设备中点目标 SN 行右侧「添加」 | `tv_title`（'连接设备'）/ `tv_device_name`（SN）/ `tv_next`（'添加'） |
| 4 | 无线连接（列表态） | `AddDeviceGetWifiListActivity` | 等列表渲染完成（忽略提示文案；2.4G/5G 均支持） | `rv_wifi_list` / `wifi_name_et` |
| 5 | 无线连接（输入态） | 同上 | 输入 SSID → **点 SSID 框最右侧箭头收起 WiFi 列表**（密码框才出现）→ 输入密码 → 点「下一步」 | `wifi_name_et` / `tv_change_wifi`（箭头）/ `pwd_et` / `tv_next` |
| 6 | WiFi 信息确认弹框 | 同上（Dialog） | 比对弹框中 WiFi 名称/密码与输入一致 → 点「确定」 | `title`（'提示'）/ `message`（含 'WIFI名称：xxx\nWIFI密码：yyy'）/ `positiveButton`（'确定'） |
| 7 | 连接网络 | `SmartWiFiActivity` | 等待设备入网（倒计时 + 注册到云端） | `tv_title`（'连接网络'）/ `tv_time` / `tvDeviceRegister`（'注册到云端'） |
| 8 | 连接成功 | `SearchDeviceActivity` | 点「下一步」 | `tv_title`（'连接成功'）/ `tv_find_device`（'添加设备成功'）/ `scan_camera_name`（SN）/ `pps_back_home`（'下一步'） |
| 8.5 | 设置房间 | `AddDeviceSetRoomActivity` | 点「完成」 | `tv_device_name`（SN）/ `tv_category_name`（房间名）/ `pps_back_home`（'完成'） |
| 9 | 安装指引 | `GuideRightPlacePicActivity` | 点「下一步」 | `tv_title`（'安装指引'）/ `tv_content` / `tv_next_vp`（'下一步'） |
| 10 | 网络诊断 | `NetworkDiagnosticActivity` | 底部点「返回首页」 | `tv_title`（'网络诊断'）/ `tv_back_home`（'返回首页'） |
| 11 | 主页断言 | `MainActivity` | 断言设备列表含 SN（判定配网成功） | `tvJingleNeutralName`（SN）/ `tvJingleNeutralOnline`（'在线'）；摄像机为 `tvCameraName` / `tvStatusOnline` |

## 3. 内部组合（Facade，不重复实现）

| 模块 | 职责 |
|---|---|
| `CloudEdgeAddDeviceCategoryPage.start_flow()` | 步骤 0：选大/小类别 + 二次断言右侧列表 + 工厂分发 Flow |
| `DoorbellChimeBaseFlow.run()` | 步骤 1-10：9 步配网模板方法（真机验证） |
| `CloudEdgeMainPage.get_device_list()` / `is_device_online()` | 步骤 11：主页设备列表断言 + 在线状态 |

各下游页面 PO 位于 `pages/android/add_device_flow/pages/`：

| PO 文件 | 覆盖阶段 |
|---|---|
| `chime_pre_setup_pages.py` | 步骤 1-2（安装位置 / 接入电源） |
| `chime_device_pairing_pages.py` | 步骤 3-6（连接设备 / 无线连接 / 弹框） |
| `chime_connection_pages.py` | 步骤 7-8.5（连接网络 / 成功页 / 设置房间） |
| `chime_post_setup_pages.py` | 步骤 9-11（安装指引 / 网络诊断 / 主页断言） |

## 4. 方法速查

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 等「选择设备类别」页加载（流程起点） |
| `add_jingle_device(sn, ssid, password, type_des, timeout, timeout_loading, timeout_connecting)` | **一站式添加**：类别页 → 9 步配网 → 主页断言，返回设备列表 |
| `assert_device_added(sn, timeout)` | 单独断言主页设备列表含 SN（含在线状态附加检查） |

默认测试数据（`doorbell_chime_base_flow.py`，从环境变量读取，不硬编码）：

| 常量 | 来源 |
|---|---|
| `DEFAULT_DEVICE_SN` | 环境变量 `CLOUDEDGE_DEVICE_SN` |
| `DEFAULT_WIFI_SSID` | 环境变量 `CLOUDEDGE_WIFI_SSID` |
| `DEFAULT_WIFI_PASSWORD` | 环境变量 `CLOUDEDGE_WIFI_PASSWORD` |

## 5. 用例

`testcases/android/test_add_doorbell_chime_base.py` 已改用一站式入口：

```python
with allure.step("一站式添加（jingle_add_page）：设备类别页 → 添加完成"):
    devices = jingle_add_page.add_jingle_device(
        sn=sn, ssid=ssid, password=wifi_password,
        timeout=30.0, timeout_loading=30.0, timeout_connecting=90.0,
    )
    assert sn in devices
```

运行方式（需真实 Chime Base 处于配对态）：

```
pytest testcases/android/test_add_doorbell_chime_base.py --platform android
```

## 6. 关键交互细节（真机踩坑记录）

1. **SSID 框右侧箭头**：输入 SSID 后 WiFi 列表会把密码框盖住，必须点
   `tv_change_wifi`（SSID 框最右侧箭头）收起列表，`pwd_et` 才渲染出来
2. **弹框比对**：SSID 与密码合并在 `message` 一个文本里
   （`WIFI名称：xxx\nWIFI密码：yyy`），需解析后比对
3. **连接完成判定**：`SmartWiFiActivity` 无转圈控件，以成功页特征元素
   `tv_find_device`（'添加设备成功'）出现为准（默认 120s）
4. **设置房间页**：流程比用户口述多一页 `AddDeviceSetRoomActivity`
   （成功页「下一步」后出现），点「完成」进入安装指引
5. **主页 Chime Base 专用 id**：`tvJingleBaseName`（SN）与
   `tvJingleBaseOnline`（在线状态），与普通设备 `tvDeviceName` 不同
6. **忽略提示文案**：不等待「WiFi 搜索中」等文案，列表渲染即就绪；
   WiFi 2.4G / 5G 均支持，不按频段过滤
7. **重跑前置**：设备配网成功后即离开配对态，重跑需先按复位键重置
   （或从账号删除设备）

## 8. 性能基线与优化记录（2026-10-10）

### 8.1 性能基线（真机 SN 131903227 / Redmi 22101317C）

通过 `log_step` 自动计时（`base_add_device_flow.py::print_step_durations`），
单次完整配网用例 `test_add_doorbell_chime_131903227` 的 10 步耗时（**优化后**）：

| # | 步骤 | 耗时 | 占比 | 备注 |
|---|---|---:|---:|---|
| 1 | `wait_chime_install_page` | 2.68s | 3.1% | 等安装位置页+点「下一步」 |
| 2 | `confirm_power_supply` | 2.63s | 3.0% | 等电源页+点「下一步」 |
| 3 | `select_device_by_sn` | 4.48s | 5.2% | 搜到设备 → 点 SN「添加」 |
| 4 | **`wait_wifi_ready`** | **8.35s** | 9.6% | 等「无线连接」页 + SSID 输入框就绪 |
| 5 | `input_wifi_credentials` | 11.24s | 12.9% | 切 IME → 输 SSID → 收列表 → 输密码 → 下一步 |
| 6 | `confirm_wifi_popup` | 2.94s | 3.4% | 弹框比对+点「确定」 |
| 7 | **`wait_network_connected`** | **42.91s** | **49.4%** | 等设备入网 + 云端注册（最大瓶颈） |
| 8 | `click_next_and_finish` | 5.07s | 5.8% | 成功页「下一步」+设置房间「完成」 |
| 9 | `skip_install_guide` | 3.00s | 3.5% | 安装指引「下一步」 |
| 10 | `back_to_homepage_and_assert` | 3.59s | 4.1% | 网络诊断+主页断言 |
| | **TOTAL（9 步）** | **86.89s** | 100% | |
| | **用例总耗时** | **96.71s** | | 含 app 启动+主页断言前置 ~10s |

### 8.2 优化前后对比

| 步骤 | 优化前 | 优化后 | 节省 |
|---|---:|---:|---:|
| `wait_wifi_ready` | **60.44s** | **8.35s** | **-52.09s（-86%）** ⚡ |
| 9 步 TOTAL | 120.47s | 86.89s | -33.58s（-28%） |
| 用例总耗时 | ~151s | 96.71s | -54s（-36%） |

### 8.3 根因（`wait_wifi_ready` 60s 问题）

**原实现**（`doorbell_chime_base_flow.py` / `chime_device_pairing_pages.py`）：

```python
def wait_wifi_ready(self, timeout_loading: float = 30.0) -> None:
    self.log_step("wait_wifi_ready", "开始")
    self.wifi_config_page.wait_for_page_loaded(timeout=timeout_loading)        # 30s
    self.wifi_config_page.wait_wifi_search_finished(timeout=timeout_loading)  # 30s
    self.log_step("wait_wifi_ready", "完成")
```

**问题清单**：
1. `ChimeWifiConfigPage.wait_for_page_loaded` 严格等 `TV_TOP_TITLE` + `RV_WIFI_LIST` **同时存在**；APP 端 WiFi 列表是**异步渲染**（先出标题+输入框，再异步出列表），30s 几乎必超时
2. `ChimeWifiConfigPage.wait_wifi_search_finished` 又调 `wait_for_element(RV_WIFI_LIST, 30)` —— **完全冗余**（第 1 步已等过）
3. `wait_wifi_ready` **不检查返回值**（两次都返回 False 也继续）
4. **60s 完全是浪费**：`input_ssid` 实际只用 `wifi_name_et`（SSID 输入框），**根本不用列表项**；列表渲染的等待只服务于 `ensure_wifi_list_collapsed` 中「是否点箭头收起」判断，而后者有显式 10s `wait_for_element(tv_change_wifi)` 兜底

### 8.4 修复方案（2 处 + 1 个 bug）

**改 1**：`DoorbellChimeBaseFlow.wait_wifi_ready` —— 去掉冗余第二次等待，加 raise

```python
def wait_wifi_ready(self, timeout_loading: float = 30.0) -> None:
    self.log_step("wait_wifi_ready", "开始")
    if not self.wifi_config_page.wait_for_page_loaded(timeout=timeout_loading):
        raise ElementNotFoundError(
            f"「无线连接」页 SSID 输入框（wifi_name_et）在 {timeout_loading}s 内未出现"
        )
    # 不再调 wait_wifi_search_finished（冗余）
    self.log_step("wait_wifi_ready", "完成")
```

**改 2**：`ChimeWifiConfigPage.wait_for_page_loaded` —— 改为等 SSID 输入框（< 1s 就绪）

```python
def wait_for_page_loaded(self, timeout: float = 30.0) -> bool:
    """等 SSID 输入框（wifi_name_et）出现 —— 标题+输入框瞬间就绪。"""
    return self.wait_for_element(self.WIFI_NAME_ET, timeout=timeout)
```

**Bug 修复**（同次改动）：`BaseAddDeviceFlow.log_step` 兼容 `开始（...）` 带后缀的「开始」日志（`select_device_by_sn` / `input_wifi_credentials` 等用 f-string 拼附加信息导致原 `==` 判定失效，3 步耗时丢失）；同时新增 `print_step_durations()` 便于回归基线对比。

### 8.5 进一步优化空间（暂未做）

| 步骤 | 当前 | 理论下限 | 优化方向 |
|---|---:|---:|---|
| `wait_wifi_ready` 8.35s | 8.35s | < 1s | 改 `wait_for_element` 用更小轮询间隔（0.2s）；或先检测 `TV_TOP_TITLE` 再 dump `WIFI_NAME_ET`（2 阶段检测） |
| `input_wifi_credentials` 11.24s | 11.24s | ~9s | `ensure_wifi_list_collapsed` 检测到密码框可见即输入，不等列表完全收起 |
| `wait_network_connected` 42.91s | 42.91s | 不可优化 | APP 端设备入网+云端注册真实耗时，**测试侧无法干预** |

**预计**再优化可省 **5-8s**（总耗时 96s → ~90s），但因大头（设备入网 42.91s）不可省，**投入产出比低**。

### 8.6 教训

1. **不要等 APP 异步渲染的列表** —— 走「手动输入」路径时，只需等输入框就绪，列表渲染交给后续「是否收起」判断处理
2. **超时判定必须检查返回值** —— 之前 `wait_wifi_ready` 不检查返回 False，30s 浪费被吞掉
3. **「开始」+「完成」配对判定要用 `startswith`** —— 兼容 `开始（SN=...）` 等带附加信息的开始日志，否则耗时统计会丢步
4. **log_step 自动计时 + print_step_durations** 是性能瓶颈分析的关键工具，所有 `run()` 末尾自动打印

## 7. 相关文档

- [设备添加流程架构](device-add-flow.md) — 策略模式 / 工厂 / 9 步模板
- [选择设备类别页](add-device-category-page.md) — 大类别→小类别选择与蓝牙方式
