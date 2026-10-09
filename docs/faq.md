# 注意事项与 FAQ

**Q: iOS 用例被跳过，提示「WebDriverAgent 未就绪」？**

iOS 端 poco 依赖 WDA。请先在 iOS 设备上启动 WebDriverAgent（端口与
`config.yaml` 中 `wda_port` 一致），确认 `http://127.0.0.1:8100/status`
可访问后再运行。WDA 未就绪时 iOS 用例会带原因跳过，**不影响安卓端**。

**Q: 用例报「平台无任何在线设备」？**

检查设备连接（`adb devices` / `xcrun devicectl list devices`），并核对
`config.yaml` 中的 `udid` 是否与实际设备一致。可用模块自测比对配置：

```bash
python -m utils.phone_manager
```

**Q: 页面元素找不到？**

仓库中的页面定位器为**示例值**，首次编写业务用例前请按 CloudEdge / 云际
实际 UI 结构调整 `pages/android/`、`pages/ios/` 中的定位器。定位优先级：
基本选择器（`name`/`text`/`type`）> 相对选择器 > 索引 > 正则。

**Q: 日志与截图在哪？**

- 运行日志：`logs/operater_logs/`（按天命名；单文件 ≤ 200MB，保留 5 个备份；总量上限 1GB）
- 串口日志：`logs/serial_logs/`（按天+串口命名；单文件 ≤ 200MB，保留 5 个备份；总量上限 1GB）
- 失败截图：`reports/failure_*.png`（同时附加到 allure 报告）
- allure 结果：`allure-results/`；html 报告：`reports/allure-report/`

**日志轮转配置**（可在 `utils/log_utils.py`、`utils/serial_utils.py` 顶部常量调整）：

```python
# 运行日志
MAX_BYTES = 200 * 1024 * 1024   # 200MB
BACKUP_COUNT = 5                # 保留 5 份

# 串口日志
SERIAL_LOG_MAX_BYTES = 200 * 1024 * 1024   # 200MB
SERIAL_LOG_BACKUP_COUNT = 5                # 保留 5 份

---

## 真机调试问题实录（2026-10-09 · Redmi 22101317C / MIUI / CloudEdge）

> 以下问题均在登录流程用例（`testcases/android/test_login_region.py`）真机联调中实际遇到，
> 每条标记 **状态** 与 **类别**；对应处理逻辑已固化进用例前置/后置或框架代码。

**Q: 运行 pytest 直接报 `ModuleNotFoundError: No module named 'allure'`？** `【已解决 | 环境】`

`allure-pytest` 插件运行时还依赖 `allure-python-commons`。单独 `pip install allure-pytest`
后仍会缺包，需补装：

```bash
pip install allure-python-commons
```

**Q: 报「平台无任何在线设备」（PhoneNotFoundError），但手机明明已连接？** `【已解决 | 设备配置】`

`utils/phone_manager.py` 按 `config.yaml` 中 `devices` 列表的 `udid` 逐台探测，
配置里没有当前连接的手机就无法命中。用 `adb devices` 取真实 udid，
在 `config.yaml` 中新增对应设备条目（`platform: Android`、`app_package` 等字段照现有格式填）。

**Q: app 处于已登录态，启动后直接落 MainActivity，登录页用例失败？** `【已解决 | 用例设计】`

登录用例需要「未登录」初始状态。前置清除 app 数据即可回到登录页：

```bash
adb shell pm clear com.cloudedge.smarteye
```

用例中已封装为 `allure.step("清除 app 数据")` 前置步骤。

**Q: MIUI「自动填充账号」弹窗遮挡登录页，识别点 `et_account/et_password` 一直找不到？**
`【已解决 | MIUI】`

现象：MIUI 的自动填充选择器（`android:id/autofill_dataset_picker`，
包名 `com.miui.contentcatcher`）覆盖在登录页上方，poco DOM 中登录页元素不可见。
按 BACK **不能可靠关闭**（可能把 app 退到后台）。

方案：用例前置临时禁用系统 autofill 服务，结束后还原原值：

```bash
adb shell settings get secure autofill_service    # 记录原值
adb shell settings put secure autofill_service null
# ... 用例执行 ...
adb shell settings put secure autofill_service <原值>   # 还原
```

**Q: `pm clear` 后登录成功时卡在 `GrantPermissionsActivity`，poco/uiautomator 都点不到「允许」？**
`【已解决 | MIUI】`

`pm clear` 会把 app 的运行时权限**全部撤销**；登录后 app 申请权限时，MIUI 的权限弹窗
（`com.lbe.security.miui`）运行在**安全沙箱**中，poco / `uiautomator dump` 均无法
获取其控件树，自动化无法点击。

方案：用例前置用 `pm grant` **预先授予全部运行时权限**，让弹窗根本不出现
（用例常量 `RUNTIME_PERMISSIONS` 共 11 项：CAMERA、RECORD_AUDIO、定位、存储、
POST_NOTIFICATIONS、蓝牙、READ_PHONE_STATE 等）：

```bash
adb shell pm grant com.cloudedge.smarteye android.permission.CAMERA
# ... 其余权限同理
```

**Q: MIUI 权限/通知弹窗的「允许」按钮点击不中？** `【已解决 | MIUI】`

MIUI 弹窗按钮文案与原生 Android 不同：通知权限为「拒绝 / **始终允许**」，
位置权限为「仅在使用中允许 / 本次使用允许」等。poco `text` 为精确匹配，
只配 `{"text": "允许"}` 匹配不到「始终允许」。定位器需覆盖多套文案
（已内置在 `test_login_region.py` 的 `allow_locators` 列表）。

**Q: 登录成功后 Poco DOM 里取不到 `ivAddDevice / ivMenu`，页面断言误报失败？**
`【已规避 | poco】`

部分机型上 poco 的 accessibility dump 与 `uiautomator dump` 存在差异/延迟，
主页面识别点可能长时间取不到，但页面实际已切换。

方案：登录成功断言改用**系统级 Activity 切换**判定（更稳定）：
`BasePage.get_current_activity()` 解析 `dumpsys activity activities` 的
`topResumedActivity`，等待其从 `LoginActivity` 变为 `MainActivity`；
poco 识别点降级为软断言（仅记录，不影响判定）。

### 退出登录联调实录（2026-10-09 第二轮）

**Q: `pm clear` 后立即 `pm grant` 授权，运行时权限弹窗还是弹出来了？**
`【已解决 | MIUI】`

MIUI 上 `pm clear` 是**异步清理**：命令返回后数据仍在后台清理，紧随其后的
`pm grant` 授权会被后续清理覆盖（实测事后检查全部 `granted=false`）。

方案：`pm clear` 后 **等待 2s 再授权**（已加进两个登录/退出用例的前置步骤）。

**Q: MIUI 权限弹窗「始终允许」按钮找到了，但点击报
`Click position out of screen. pos=[1.71, 1.20]`？** `【已规避 | MIUI】**

MIUI 权限弹窗（`com.lbe.security.miui`）运行在安全沙箱，poco dump 出的
控件坐标可能**越界**（超出屏幕归一化范围），click 直接抛错。

方案：`_wait_for_main_activity` 中把「允许」点击包在 `try/except` 里逐个候选
尝试；全部失败则按 **BACK 键拒绝放行**（`BasePage.press_back()`，adb keyevent 4），
登录流程不受权限被拒影响。

**Q: 登录成功后立即点击「我的」页账号入口 `tv_account`，偶发没反应？**
`【已解决 | 用例设计】`

登录后主页 Fragment 尚未完成渲染时，`tv_account` 虽可见但点击可能不生效
（真机复现：第一次点击未跳转，第二次成功）。

方案：跳转判定用**系统级 Activity**（等待 `MyInformationActivity`），
未跳转则**重试点击（最多 3 次）**；点击前加 2s 稳定等待。见
`testcases/android/test_logout.py` 的 `_wait_for_activity` 与重试逻辑。

**Q: `adb shell uiautomator dump` 一直输出 `Killed`？** `【已规避 | MIUI】**

MIUI 上 uiautomator 进程常被系统直接杀死（低内存/省电策略），dump 无法生成。

方案：改用 **poco dump** 采集控件树：`poco.agent.hierarchy.dump()` 返回
JSON dict，控件属性在 `payload` 字段（`resourceId`/`text`/`pos`/`visible` 等），
通过 `Android(udid)` + `G.add_device()` 构造驱动即可，无需 uiautomator。

**Q: `connect_device("android:///udid")` 偶发报
`IndexError: list index out of range`（adb.py `_set_cmd_options`）？**
`【已规避 | airtest】`

airtest 解析 URI 中空 host 时 `server_addr` 列表长度异常，偶发触发该 IndexError。

方案：绕过 `connect_device`，直接构造并注册设备对象：

```python
from airtest.core.android import Android
from airtest.core.api import G
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

device = Android("cfed8c100822")
G.add_device(device)
poco = AndroidUiautomationPoco(device=device, use_airtest_input=True,
                               screenshot_each_action=False)
```

### 账号切换联调实录（2026-10-09 第三轮）

**Q: 退出登录后再登录另一账号，登录页账号/密码框预填了旧账号怎么办？**
`【已验证 | 用例设计】**

登录时勾选「记住密码」，退出登录后账号框预填**上一账号**、密码框预填
**明文密码**（poco `attr("text")` 可直接读到），国家/地区保持上次选择。

真机验证结论：poco `element.set_text("新账号")` 为**替换行为**（非追加），
直接输入新账号/新密码即可覆盖预填，**无需清空**。账号切换流程见
`testcases/android/test_account_switch.py`（美国账号 → 退出 → 中国账号
`ceshi011@qq.com`，一次通过）。

### 添加设备联调实录（2026-10-09 第四轮）

**Q: 「查看更多」点了没反应？设备列表突然空了？** `【已解决 | 控件结构】`

直觉上「查看更多」应该是**原地展开**剩余设备，真机验证却发现：

- 点击后弹出 **BottomSheet 抽屉**（`com.cloudedge.smarteye:id/design_bottom_sheet`），
  标题「搜索到的设备」+ 右上角 `iv_close` 关闭 + `recyclerView` 完整设备列表
- 弹出后**原 `rv_devices` 被覆盖隐藏**，`poco(RV_BT_DEVICES).children()`
  返回空列表（这正是 `get_bluetooth_devices()` 报「蓝牙设备列表为空」的根因）
- 选择设备时按 `tv_model` resource-id + `text=model` 双条件定位即可，
  因为 BottomSheet 弹出后原 RV 不再可见，定位器命中是唯一的

**Q: `poco({dict})` 报 `ValueError: Name selector should only be string types`？**
`【已解决 | poco】`

`poco()` 的第一个位置参数（`name`）要求是字符串，不接受定位器 dict。
`poco(self.RV_CATEGORY)` 会把整个 dict 传给 `name` 然后报错。解法：

```python
# 错误：self.poco(self.RV_CATEGORY)
# 正确：解包为关键字参数
self.poco(**self.RV_CATEGORY)        # 展开成 name="com.xxx:id/xxx"
self.poco(name=self.RV_CATEGORY["name"])  # 或显式取 name 字段
```

> `poco("xxx", text="yyy")` 这种 `name + 文本` 形式不受影响（name 是字符串）。

---

## 文档导航

- 上一篇：[执行规则 ←](./rules/execution.md)

[返回文档中心](./README.md) · [返回项目首页](../README.md)
