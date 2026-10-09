# 智能门铃 Chime Base 一站式添加页面（jingle_add_page）

> 真机全流程验证：2026-10-09（Redmi 22101317C / cfed8c100822，SN 131903239）

## 1. 概述

`JingleAddPage`（工厂页面名 `jingle_add_page`，文件
`pages/android/jingle_add_page.py`）是智能门铃 Chime Base 添加的
**一站式门面 PO**：封装从「选择设备类别」页开始，到「添加完成
（主页断言设备列表含 SN）」的完整流程。

对用例暴露单一入口 `add_jingle_device()`，一行代码完成整个添加链路：

```python
jingle_page = PageFactory.create(
    "android", "jingle_add_page", poco=poco, udid=udid,
)
devices = jingle_page.add_jingle_device()  # 全默认参数（环境变量注入）
# 或直接以参数覆盖测试数据
devices = jingle_page.add_jingle_device(
    sn="<SN>", ssid="<SSID>", password="<密码>",
)
```

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
| 11 | 主页断言 | `MainActivity` | 断言设备列表含 SN（判定配网成功） | `tvJingleBaseName`（SN）/ `tvJingleBaseOnline`（'在线'） |

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

## 7. 相关文档

- [设备添加流程架构](device-add-flow.md) — 策略模式 / 工厂 / 9 步模板
- [选择设备类别页](add-device-category-page.md) — 大类别→小类别选择与蓝牙方式
