# 选择设备类别页面文档 — Android（CloudEdge）· 添加设备

本文档记录 **CloudEdge 安卓端「选择设备类别」页
（`com.dctrain.module_add_device.view.AddSeriesTypeActivity`）** 及其顶部
「添加设备」弹窗、蓝牙区域「查看更多」底部抽屉的页面识别点、控件定位器与
业务方法，供编写和维护页面对象、用例时快速查阅。

> **范围说明**：本文档仅覆盖 Android（CloudEdge）端，iOS（云际）端对应页面待补齐。
>
> **数据来源**：定位器全部基于真机 poco dump 验证（udid=`cfed8c100822`，Redmi /
> MIUI，屏幕分辨率 1080×2400），并由用例 `testcases/android/test_add_device.py`
> 真机验证通过（方式 A：按类别、方式 B：蓝牙 + 查看更多）。

---

## 页面对象与页面工厂注册表

| 页面名 | Android 页面类 | iOS 页面类 | 工厂 key |
|---|---|---|---|
| 选择设备类别页 | `CloudEdgeAddDeviceCategoryPage` | _(待实现)_ | `(android, "add_device_category_page")` |

`CloudEdgeMainPage`（首页）同时提供添加设备弹窗相关方法：

| 方法 | 说明 |
|---|---|
| `open_add_device_menu()` | 点击首页 `ivAddDevice`，唤起「扫一扫 / 添加设备」弹窗 |
| `click_add_device_popup_item(name)` | 点击弹窗中的指定条目（`tvName`，text=「扫一扫」/「添加设备」）|
| `open_add_device_category_page()` | 一站式：唤起弹窗 → 点击「添加设备」条目 |

---

## 1. 页面职责

「选择设备类别」页是设备添加流程的**入口页**，承担以下职责：

1. **顶部蓝牙区域**（附近有 BT 设备时显示）：展示蓝牙搜索结果，含状态提示
   「请确保设备处于配网状态」与搜索图标；超过显示数量时第 6 个槽位显示
   「查看更多」按钮
2. **左下「手动添加」**：跳转 SN/序列号手动添加流程
3. **左侧分类列表**：按品类浏览设备（电池摄像机 / 智能门铃 / 常电摄像机 /
   婴儿摄像机 / 灯具摄像机 / 宠物摄像机 / 4G摄像机 / 摄像机套装 / 狩猎摄像机 /
   智能门锁）
4. **右侧类型列表**：当前选中分类下的具体类型，每项含设备图、特色标签、
   名称、描述（如 `(2.4G Wi-Fi)`、`(WIFI+蓝牙)`）
5. **顶部右上 `iv_multi` + `iv_submit`**：多选模式与提交按钮

进入路径：**首页 → 右上「添加设备」(`ivAddDevice`) → 弹窗「添加设备」条目**
返回路径：左上 `iv_back`（返回首页）

页面元素概览（从上到下）：

```
┌─────────────────────────────────────┐
│ ←      选择设备类别           ☐ ✓  │  ← top_tool / iv_back / tv_title / iv_multi / iv_submit
│ 🔍  搜索到的设备...                  │  ← iv_search / tv_search（蓝牙标题）
│       请确保设备处于配网状态          │  ← tv_be_sure_status
│ ┌──┐ ┌──┐ ┌──┐                    │
│ │📷│ │📷│ │📷│   ← 蓝牙设备列表     │  ← rv_devices
│ │M1│ │M2│ │M3│                    │
│ └──┘ └──┘ └──┘                    │
│ ┌──┐ ┌──┐ ┌──┐                    │
│ │M4│ │M5│ │更多│   ← 第 6 个为「查看更多」│
│ └──┘ └──┘ └──┘                    │
│           手动添加                   │  ← tv_add_manual_add
│ ┌──────┐  ┌────────┐ ┌────────┐  │
│ │电池摄像机│ │电池摄像机│ │电池摄像机│  │  ← 左 recyclerview_main / 右 recyclerview_detail
│ │智能门铃 │ │(2.4G Wi-Fi)│ │(WIFI+蓝牙)│  │     分类列表       类型列表
│ │常电摄像机│ │  ⋮    │ │  ⋮    │  │
│ │  ⋮    │ └────────┘ └────────┘  │
│ │  ⋮    │                          │
│ └──────┘                          │
└─────────────────────────────────────┘
```

---

## 2. 页面识别点（用于 `wait_for_page_loaded` / `is_page`）

| 识别点 | Android 定位器（resource-id） | 文本 |
|---|---|---|
| 页面标题 | `{"name": "com.cloudedge.smarteye:id/tv_title"}` | **「选择设备类别」** |
| 左侧分类列表 | `{"name": "com.cloudedge.smarteye:id/recyclerview_main"}` | — |

**两个识别点同时存在 + 标题文本 = 「选择设备类别」**才判定为本页（`is_page()`
三重校验，避免相似页误判）。

---

## 3. 控件定位器

### 3.1 顶部工具栏

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 工具栏 | `{"name": "com.cloudedge.smarteye:id/top_tool"}` / `toolbar` | 标题栏容器 |
| 返回键 | `{"name": "com.cloudedge.smarteye:id/iv_back"}` | 返回首页 |
| 标题 | `{"name": "com.cloudedge.smarteye:id/tv_title"}` | 文本「选择设备类别」|
| 多选模式 | `{"name": "com.cloudedge.smarteye:id/iv_multi"}` | 顶部右上图标（pos ≈ [0.80, 0.07]）|
| 提交 | `{"name": "com.cloudedge.smarteye:id/iv_submit"}` | 顶部右上图标（pos ≈ [0.90, 0.07]）|

### 3.2 蓝牙区域（`ll_bt` 容器，附近有 BT 设备时显示）

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 蓝牙区域容器 | `{"name": "com.cloudedge.smarteye:id/ll_bt"}` | 整块蓝牙区域 |
| 搜索图标 | `{"name": "com.cloudedge.smarteye:id/iv_search"}` | 左侧放大镜图标 |
| 搜索标题 | `{"name": "com.cloudedge.smarteye:id/tv_search"}` | 文本「搜索到的设备...」|
| 状态提示 | `{"name": "com.cloudedge.smarteye:id/tv_be_sure_status"}` | 文本「请确保设备处于配网状态」|
| 设备列表 | `{"name": "com.cloudedge.smarteye:id/rv_devices"}` | RecyclerView，每项含 `wv`（波纹背景）+ `iv_pic`（设备图）+ `tv_model`（型号）|
| 设备型号项 | `{"name": "com.cloudedge.smarteye:id/tv_model"}` | 文本 = 设备型号字符串（数字 SN 形式）或「查看更多」|
| 设备图片 | `{"name": "com.cloudedge.smarteye:id/iv_pic"}` | Item 缩略图 |
| 手动添加 | `{"name": "com.cloudedge.smarteye:id/tv_add_manual_add"}` | 文本「手动添加」按钮 |

### 3.3 分类与类型列表

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 左侧分类列表 | `{"name": "com.cloudedge.smarteye:id/recyclerview_main"}` | 列表项 `framelayout`（clickable）|
| 分类项文本 | `{"name": "com.cloudedge.smarteye:id/tv_category_name"}` | 文本 = 类别名（电池摄像机/智能门铃/...）|
| 右侧类型列表 | `{"name": "com.cloudedge.smarteye:id/recyclerview_detail"}` | 列表项 `RelativeLayout`（clickable）|
| 类型项名称 | `{"name": "com.cloudedge.smarteye:id/tv_device_name"}` | 文本 = 设备类型名 |
| 类型项描述 | `{"name": "com.cloudedge.smarteye:id/tv_des"}` | 文本 = 类型描述（如 `(2.4G Wi-Fi)`）|
| 类型项特色 | `{"name": "com.cloudedge.smarteye:id/iv_device_features"}` | 特色标签图标（推荐/新品等）|
| 类型项图片 | `{"name": "com.cloudedge.smarteye:id/iv_device"}` | 设备图 |

### 3.4 「查看更多」底部抽屉（点击后弹出）

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 抽屉容器 | `{"name": "com.cloudedge.smarteye:id/design_bottom_sheet"}` | BottomSheet 容器 |
| 关闭按钮 | `{"name": "com.cloudedge.smarteye:id/iv_close"}` | 右上角 × 关闭 |
| 完整设备列表 | `{"name": "com.cloudedge.smarteye:id/recyclerView"}` | 展开后的完整 BT 搜索结果 |
| 列表项 | — | `RelativeLayout` + `iv_pic` + `tv_model`（结构与原 RV 一致）|

### 3.5 首页「添加设备」弹窗（顶层 PopupWindow）

点击首页 `ivAddDevice` 后弹出的 2 条目弹窗（`recyclerview` 容器）：

| 控件 | 定位器（Android） | 说明 |
|---|---|---|
| 弹窗条目 | `{"name": "com.cloudedge.smarteye:id/tvName"}` | 文本 = 「扫一扫」/「添加设备」|

---

## 4. 业务方法

### 4.1 页面识别与基础操作

| 方法 | 说明 |
|---|---|
| `wait_for_page_loaded(timeout)` | 双识别点轮询等待（默认 20s）|
| `is_page()` | 标题=「选择设备类别」+ 分类列表可见 |
| `get_page_title()` | 读取标题文本 |
| `click_back()` | 点击左上返回键返回首页 |

### 4.2 方式 A：按类别添加

| 方法 | 说明 |
|---|---|
| `get_categories()` | 获取左侧分类列表的可见类别名（递归 item 内的 `tv_category_name`）|
| `select_category(name)` | 点击指定类别（多条件 `tv_category_name` + `text=name`），**内部 0.6s 等待右侧列表刷新**|
| `get_device_types()` | 获取右侧类型列表的 [(名称, 描述), ...] |
| `select_device_type(name, type_des=None)` | 点击指定类型，触发跳转至配网/开机说明页（`PowerOnActivity`）。**前提**：必须先调 `select_category` 选好大类别；同名类型推荐传 `type_des` 双条件定位 |
| **`add_device_by_category(category, type, type_des=None)`** | **一站式：强制"大类别→小类别"顺序执行**。先 `select_category`（含等待）、再断言右侧列表中已含目标项（防切换异常）、最后 `select_device_type`。**推荐用例使用** |

### 4.3 方式 B：蓝牙添加

| 方法 | 说明 |
|---|---|
| `is_bluetooth_area_visible()` | 顶部蓝牙区域 `ll_bt` 是否可见（仅附近有 BT 设备时显示）|
| `get_bluetooth_devices()` | 获取设备型号列表。**优先读取「查看更多」底部抽屉中的完整列表**，未展开时回退到原 `rv_devices` |
| `has_more_bt_devices_button()` | 是否有「查看更多」按钮（原 RV 列表中含 `text="查看更多"`）|
| `click_more_bt_devices()` | 点击「查看更多」，弹出 BottomSheet 显示完整结果 |
| `is_more_devices_sheet_visible()` | BottomSheet 是否已弹出 |
| `close_more_devices_sheet()` | 点击 `iv_close` 关闭 BottomSheet |
| `select_bluetooth_device(model)` | 选择指定型号蓝牙设备。**自动适配**：优先从 BottomSheet 选择，未展开时从原 RV 选择（基于 `tv_model` resource-id + `text=model` 双条件定位）|
| `click_manual_add()` | 点击「手动添加」入口 |

> **「查看更多」与底部抽屉的关系**：点击原 RV 中的「查看更多」文本
> 触发 BottomSheet 弹出，标题「搜索到的设备」+ 完整设备列表；
> BottomSheet 弹出后原 `rv_devices` 隐藏，`is_more_devices_sheet_visible()`
> 返回 True，`get_bluetooth_devices()` 读取 BottomSheet 的 `recyclerView`。

---

## 5. Android 特有说明

- **多层级结构**：`recyclerview_main` 下的每个 `framelayout` 直接包含
  `tv_category_name`；而 `recyclerview_detail` 下先有 `LinearLayout` 行容器，
  再嵌入 `RelativeLayout`（item）才含 `tv_device_name` 与 `tv_des`。
  `get_categories()` / `get_device_types()` 已处理该层级差异
  （前者 `.child()`，后者 `.children().children()`）。
- **必须先选大类别再选小类别**：右侧类型列表内容随左侧分类动态切换。
  若先调 `select_device_type` 而未先调 `select_category`，会误点其他分类下
  同名类型。**推荐用例使用一站式 `add_device_by_category(category, type, type_des)`**
  由 PO 内部强制顺序与断言。
- **同名类型消歧**：同一大类别下类型名可能重复（如「电池摄像机」下有
  2.4G Wi-Fi / WIFI+蓝牙 两个同名项），`select_device_type` 接受 `type_des`
  可选参数用 (名称, 描述) 双条件唯一定位。不传则按「同名第一个」命中。
- **「查看更多」展开方式**：点击后会弹出 `BottomSheetDialog`
  （`design_bottom_sheet` 容器），**不是原地展开**。原 `rv_devices` 被覆盖隐藏，
  `get_bluetooth_devices()` 会自动从 BottomSheet 的 `recyclerView` 读取完整列表。
- **类别 / 类型重名**：左侧分类名与右侧类型名可能重复（如「电池摄像机」既是
  分类名也是 2.4G Wi-Fi / WIFI+蓝牙 两个类型的类型名）；通过 `tv_category_name`
  与 `tv_device_name` 不同的 resource-id 区分。
- **设备型号为数字 SN**：蓝牙设备显示的不是产品名而是数字型号字符串
  （如 `131903239`、`124207252`），不可读性较差，用例断言时直接用该字符串。
- **左侧分类可滚动**：分类数超过可视范围时可通过 `swipe_up` 滑动加载更多；
  `get_categories()` 仅返回当前可见项。
- **首页弹窗条目同 resource-id**：弹窗「扫一扫」与「添加设备」两个条目都使用
  `tvName`，仅靠 `text` 区分，定位时必须叠加 `text=` 条件
  （`main_page.click_add_device_popup_item` 已处理）。

---

## 6. 用法示例

### 6.1 方式 A：一站式按类别添加（推荐）

```python
from pages.android.main_page import CloudEdgeMainPage
from pages.page_factory import PageFactory


def test_add_by_category(poco, udid):
    main_page = CloudEdgeMainPage(poco=poco, udid=udid)
    add_device_page = PageFactory.create(
        "android", "add_device_category_page", poco=poco, udid=udid,
    )

    # 1. 首页 → 添加设备弹窗 → 「添加设备」条目
    main_page.open_add_device_category_page()

    # 2. 断言进入「选择设备类别」页
    assert add_device_page.wait_for_page_loaded(timeout=15)
    assert add_device_page.get_page_title() == "选择设备类别"

    # 3. 一站式按"大类别→小类别"添加（强制顺序，推荐用法）
    #    内部会：选「电池摄像机」→ 等 0.6s 右侧刷新 →
    #    断言右侧列表含「电池摄像机 (2.4G Wi-Fi)」→ 点击该项
    add_device_page.add_device_by_category(
        category_name="电池摄像机",
        type_name="电池摄像机",
        type_des="(2.4G Wi-Fi)",  # 必传：同名项消歧（电池摄像机下有两个）
    )
    # 此时已跳转至 PowerOnActivity（按住电源按钮等配网说明）

    # 4. (可选) 若不传 type_des，则按"同名第一个"命中（不推荐于同名项）：
    # add_device_page.add_device_by_category("电池摄像机", "电池摄像机")
```

#### 细粒度方式（需自行保证顺序，谨慎使用）

```python
# 顺序：select_category → select_device_type（必须先选大类别）
add_device_page.select_category("电池摄像机")
types = add_device_page.get_device_types()
# types = [("电池摄像机", "(2.4G Wi-Fi)"), ("电池摄像机", "(WIFI+蓝牙)")]
add_device_page.select_device_type("电池摄像机", type_des="(2.4G Wi-Fi)")
```

> **重要**：直接调用 `select_device_type("电池摄像机")`（不传 `type_des`）
> 会命中右侧第一个同名项；若调用前未选对大类别还会误点其他分类下同名类型。
> 强烈推荐使用一站式 `add_device_by_category`，由 PO 内部强制顺序与断言。

### 6.2 方式 B：蓝牙添加

```python
# 1. 进入「选择设备类别」页（同上）
main_page.open_add_device_category_page()
assert add_device_page.wait_for_page_loaded(timeout=15)

# 2. 断言蓝牙区域可见 + 获取设备列表
assert add_device_page.is_bluetooth_area_visible()
devices = add_device_page.get_bluetooth_devices()
# 展开前（可能含「查看更多」占位）：
#   ["131903239", "124207252", "124338168", "112929266", "118610900", "查看更多"]
# 展开后（从 BottomSheet 读取）：
#   ["131903239", "124207252", "124338168", "112929266", "118610900", "120760434", ...]

# 3. 「查看更多」可见时点击展开
if add_device_page.has_more_bt_devices_button():
    add_device_page.click_more_bt_devices()
    assert add_device_page.is_more_devices_sheet_visible()
    add_device_page.close_more_devices_sheet()  # 关闭抽屉（如需）

# 4. 选择蓝牙设备（自动适配原 RV / BottomSheet 两种来源）
add_device_page.select_bluetooth_device("131903239")
```

### 6.3 完整可运行用例

```bash
python run.py --platform android -k test_add_device_by_category
python run.py --platform android -k test_add_device_by_bluetooth
```

完整用例见 `testcases/android/test_add_device.py`（含登录前置与 Activity 级断言）：

- `test_add_device_by_category` — 方式 A：按类别添加（电池摄像机 → 电池摄像机 (2.4G Wi-Fi) → PowerOnActivity）
- `test_add_device_by_bluetooth` — 方式 B：蓝牙设备列表 + 查看更多 BottomSheet + 选择设备触发 Activity 切换

---

## 文档导航

- 上一篇：[我的信息页（退出登录）←](./account-page.md)
- 下一篇：[串口测试 →](./serial.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
