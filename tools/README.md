# tools 探测工具集

UI 自动化开发期的**页面探测与定位器采集工具**。运行前提：目标安卓设备已连接、
屏幕点亮、被测 app（CloudEdge）在前台且已进入 jingle 设备相关页面层级。

## 工具清单

| 脚本 | 用途 | 产物 |
|---|---|---|
| `tools/explore_page.py` | 探测「点击入口后的新页面」：自动导航到父页面 → 逐个点击入口 → dump 新页面 → 返回父页面 | `logs/dumps/explore_<入口id>.json` / `explore_<入口id>_summary.txt`（固定名，重探覆盖） |
| `tools/explore_deep.py` | 从 jingle 首页起的**自动 DFS 遍历**：主页点击设备 SN → 逐页收集入口（滚动补充屏外项）→ 安全入口逐个点击 → 新 Activity 即 dump 并深入；增量模式已知页面只记命中，`--full` 全量模式穿透已知页面至最深层级逐页罗列 | `logs/dumps/deep_<Activity>.json` / `_summary.txt`、`deep_<Activity>_dlg<N>_*`（弹框）、`deep_report.txt`（页面树+元素清单汇总报告） |
| `utils/dump_page.py` | 采集「当前页面」层级（单页，不动导航） | `logs/dumps/dump_<时间戳>.json` / `_summary.txt` |

两者均走项目唯一收口 `BasePage.dump_hierarchy(reason)`，`--reason` 必填（门控）。

## explore_page.py 用法

```bash
# 探测某父页面的多个入口（逗号分隔 resource-id）
python tools/explore_page.py --reason "设备信息页下一级定位器采集" ^
    --parent jingle_device_info_page ^
    --entries layout_device_name,layout_device_scene,layout_location_manager,layout_firmware_version

# 指定设备
python tools/explore_page.py --reason "..." --parent jingle_general_page ^
    --entries layout_install_guide,layout_jingle_unbind --udid TC55LJMR59W8ZPRK
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--reason` | 是 | 探测诉求，透传给 dump 门控 |
| `--parent` | 是 | 父页面 PO 名称（PageFactory key） |
| `--entries` | 是 | 待探测入口 resource-id，逗号分隔 |
| `--udid` | 否 | 缺省自动选第一台在线安卓设备 |
| `--settle` | 否 | 页面切换等待秒（默认 3.0） |
| `--max-retries` | 否 | 层级为空重试次数（默认 5） |

## explore_deep.py 用法

```bash
# 增量模式：只罗列历史未探测过的新页面
python tools/explore_deep.py --reason "jingle 首页起增量探测"

# 全量模式：主页→设备首页→设置→设置内全部可点击页面/开关，穿透已知页面
# 直至最深层级，逐页罗列元素（推荐 --settle 2.0 加速）
python tools/explore_deep.py --full --reason "设置内全部页面/开关全量罗列" --settle 2.0

# 指定 SN / 限制规模
python tools/explore_deep.py --full --reason "..." --sn 131903227 --max-pages 40
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--reason` | 是 | 探测诉求，透传给 dump 门控 |
| `--full` | 否 | 全量模式：已知页面同样 dump 罗列并继续深入（默认增量模式只找新页面） |
| `--sn` | 否 | 指定设备 SN（缺省主页第一个 Chime Base 条目） |
| `--udid` | 否 | 缺省自动选第一台在线安卓设备 |
| `--settle` | 否 | 页面切换等待秒（默认 2.5） |
| `--max-pages` | 否 | 单趟页面数上限（默认：增量 15 / 全量 40） |
| `--max-candidates` | 否 | 每页候选入口数上限（默认：增量 30 / 全量 60，设备信息页约 40 候选） |

深度遍历规则（在下方探测规则基础上补充）：

1. **增量去重**：启动时扫描 `logs/dumps/*_summary.txt` 中的「前台 Activity」
   与 `KNOWN_ACTIVITIES` 常量合并——增量模式下之前探测过的页面只记录入口
   命中不再罗列元素；`--full` 全量模式不受影响，始终逐页罗列（报告标注
   「已知/新发现」）。
2. **候选双层**：入口按 (id, text) 去重收集（设置宫格/列表条目共用 id 需按
   文本区分）；黑名单命中者**只罗列永不点击**；该 app 无障碍树不暴露
   `clickable`，用「可见+面积≤30%+非结构容器」启发式。
3. **滚动采集**：每页 dump 后上滑（最多 3 次）补充屏外入口（如设置页底部
   重启/删除按钮），合并罗列后滚回顶部再逐入口点击；点击定位失败时自动
   「关弹框重试 → 上滑露出底部重试」。
4. **安全黑名单（2026-10-11 用户授权收窄）**：仅格式化、删除、升级、恢复
   出厂及返回类按钮**只罗列永不点击**；其余入口（含确定/保存/完成/重启/
   解绑等）正常点击探测。弹框落盘后点「确认」观察实际效果（含危险词的
   弹框仅取消）；开关类控件观察后再次点击还原。
5. **路径恢复**：无法返回父页面时自动「回主页 → 重进设备 → 重放已记录路径」。
6. **添加向导隔离**：PowerOnActivity / AddSeriesTypeActivity（添加设备向导）
   只记命中不深入，避免误触重配网流程。
7. **漏探提示**：点击以顶部可见为准，点击失败条目及依赖状态的入口
   （如编辑时间段需已有数据）在报告中标注，可用 `explore_page.py` 精探。

## 探测规则

1. **导航规则**：脚本先把设备带回设置页（系统返回键循环，app 退到前台之外则报错），
   再按 `NAVIGATE_MAP`（脚本内常量）导航到父页面。**新增子页面 PO 后必须在
   `NAVIGATE_MAP` 登记导航方法**，否则只能探测「当前已在该父页面」的场景。
2. **安全规则**：探测过程只执行返回类操作（优先级 `iv_back` → `negativeButton` →
   `tv_cancel` → 系统返回键），**永不点击确认类按钮**（tv_confirm / positiveButton /
   格式化、解绑、删除等破坏性操作）。单个入口探测完必须验证父页面重新加载，
   验证失败立即终止，避免在未知页面继续误操作。
3. **产物规则**：固定文件名 `explore_<入口id>_*`，重探覆盖旧产物；汇总 txt 为三段式
   （① app resource-id 定位器候选 ② 无 id 有文本节点 ③ 系统/容器节点）。
4. **dump 禁令**：不使用 `adb shell uiautomator dump`（与 pocoservice 抢占
   accessibility 服务，exit 137，2026-10-09 真机验证，见 docs/reference/extension.md）。
5. **整理规则**：阅读 `explore_*_summary.txt` 第一段挑选定位器（优先有 resource-id
   的稳定节点；列表项用 `tv_title` 文本 + 父容器锚定）→ 编写/补充 PO 定位器表与
   方法 → 真机验证 → 更新 `docs/modules/chime/` 下对应 `*-page.md`。

## 典型工作流（新页面 PO 编写）

```
1. 确认设备位于 jingle 页面层级 → 运行 explore_page.py 探测入口
2. 阅读 logs/dumps/explore_<入口id>_summary.txt → 整理定位器与页面结构
3. 编写 pages/android/<新页面>_page.py（继承 JingleSubPageBase）
4. 在 NAVIGATE_MAP 登记新父页面（若其还有下一级页面待探测）
5. 真机验证页面识别 / 业务方法
6. 更新 docs/modules/chime/ 对应 MD 文档
```
