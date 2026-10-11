"""jingle 设备页面深度自动探测脚本（CLI 工具，Android 端）。

用途：
    从主页点击设备 SN（Chime Base 条目）进入 jingle 首页（JingleBaseActivity），
    DFS 自动遍历可达页面：逐页 dump（含滚动补充采集）→ 收集全部可点入口 →
    安全入口逐个点击 → 按 Activity 变化判定去向：
    - 新 Activity（历史未探测）→ dump（JSON + 元素汇总）并继续深入
    - 已知 Activity → 增量模式只记录命中；``--full`` 全量模式同样 dump
      并继续深入（设置页 → 子页 → 最深层级全部罗列）
    - 同 Activity（弹框/开关/选择）→ 记录反应并恢复原状
    直到无新页面可达，输出带页面树的汇总报告供人工筛选。

与既有工具的分工：
    - utils/dump_page.py    → 采集「当前页面」层级（单页，不动导航）
    - tools/explore_page.py → 探测「指定父页面的指定入口」（人工筛选后精确探测）
    - tools/explore_deep.py → 从 jingle 首页起的「自动遍历」：
        * 默认增量模式：只罗列历史未探测过的新页面
        * --full 全量模式：主页→设备首页→设置→设置内全部可点击页面/开关，
          穿透已知页面直至最里层级，逐页罗列元素（每 Activity 一趟一次）

增量去重：启动时扫描 ``logs/dumps/*_summary.txt`` 中出现过的「前台 Activity」，
与手工维护的 KNOWN_ACTIVITIES 合并为已知集合——增量模式下之前探测过的页面
不再罗列元素；全量模式下已知页面照常罗列（报告标注「已知」）。

安全约定（见 tools/README.md 探测规则，2026-10-11 用户授权收窄）：
    - 仅格式化/删除/升级/恢复出厂及返回类按钮**只罗列永不点击**；
      其余入口（含确定/保存/完成/重启/解绑/对讲/报警等）正常点击探测
    - 弹框落盘后点「确认」观察实际效果；弹框文本含危险词时仅取消（防线）
    - 只用 negativeButton / tv_cancel / btn_cancel / iv_back / 系统返回键返回
    - 开关类控件点击观察后再次点击还原原状（还原弹框同样确认）
    - 添加设备向导（PowerOnActivity 起）与选择设备类别页不深入，只记命中
    - 无法回到父页面时：回主页 → 重进设备 → 按已记录路径重放恢复

用法：
    # 增量模式（只找新页面）
    python tools/explore_deep.py --reason "jingle 首页起增量探测"

    # 全量模式（主页→设备首页→设置→最深层级全部罗列）
    python tools/explore_deep.py --full --reason "设置内全部页面/开关全量罗列"

产物（logs/dumps/，固定名，重探覆盖）：
    - deep_<Activity短名>.json / _summary.txt        页面层级与元素汇总
    - deep_<Activity短名>_dlg<N>.json / _summary.txt 同页弹框状态
    - deep_report.txt                                汇总报告（页面树+元素清单）
"""

import argparse
import json
import sys
import time
from pathlib import Path

from airtest.core.api import connect_device
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pages.android.jingle_sub_page_base import RID  # noqa: E402
from pages.android.main_page import CloudEdgeMainPage  # noqa: E402
from pages.base_page import BasePage  # noqa: E402
from utils.dump_page import (  # noqa: E402
    APP_PKG_PREFIX,
    DUMP_DIR,
    build_summary,
    count_nodes,
    get_root,
    walk_nodes,
)
from utils.log_utils import get_logger  # noqa: E402

logger = get_logger(__name__)

# 被测 app 包名（判断 app 是否在前台）
APP_PACKAGE = "com.cloudedge.smarteye"

# 探测起点（jingle 首页）
START_ACTIVITY = "JingleBaseActivity"

# 手工维护的已知 Activity 短名（PO / 既有流程已覆盖）
MANUAL_KNOWN_ACTIVITIES = {
    "MainActivity",                 # 主页
    "JingleBaseActivity",           # jingle 首页（探测起点，元素单独罗列）
    "CameraSettingNewActivity",     # jingle 设置页
    # 设置子页（2026-10-10/11 已探测）
    "DeviceInfoActivity", "DeviceNameActivity", "DeviceSceneActivity",
    "DeviceAssignmentActivity", "DeviceVersionActivity",
    "SleepTimeListActivity", "SleepTimeAddActivity",
    "SoundLightAlarmDingActivity", "DeviceSettingShareActivity",
    "ShareTypeActivity", "SoundSettingActivity", "SdCardActivity",
    "GeneralSettingActivity", "GuideRightPlacePicActivity",
    "GuideRightPlaceActivity", "NetworkDiagnosticActivity",
    "JingleUnbindChannelActivity",
    # 添加设备向导（DoorbellChimeBaseFlow 已覆盖，2026-10-09）
    "PowerOnActivity", "BleSearchDeviceActivity",
    "AddDeviceGetWifiListActivity", "SmartWiFiActivity",
    "SearchDeviceActivity", "AddDeviceSetRoomActivity",
    # 选择设备类别页（CloudEdgeAddDeviceCategoryPage 已覆盖）
    "AddSeriesTypeActivity",
}

# 添加设备向导入口 Activity：即使 --full 也不深入（避免误触重配网流程）
EXCLUDED_ACTIVITIES = {"PowerOnActivity", "AddSeriesTypeActivity"}

# 结构性容器 id（点击无意义，排除出候选）
STRUCTURAL_IDS = {"action_bar_root", "v_bg", "toolbar", "content"}

# 候选节点面积上限（占屏幕比例，超过视为容器背景）
MAX_NODE_AREA = 0.30

# 危险词黑名单：入口文本命中任一子串则**只罗列永不点击**
# （2026-10-11 用户授权收窄：除格式化/删除/升级外，其余入口——含确定/保存/
#   完成/重启/解绑/对讲/报警等——均正常点击探测）
DANGER_TEXTS = ("删除", "格式化", "升级", "恢复出厂")
# 危险 id 黑名单（resource-id 短名，只罗列永不点击）
DANGER_IDS = {"btn_delete", "btn_format", "btn_upgrade"}
# 弹框取消按钮（关闭弹框专用，按优先级）
DIALOG_CANCEL_IDS = ("negativeButton", "tv_cancel", "btn_cancel")
# 弹框确认按钮（用户授权后非危险弹框正常确认观察，按优先级）
DIALOG_CONFIRM_IDS = ("positiveButton", "tv_confirm", "btn_confirm")
# 页面返回按钮（按优先级；含弹框取消兜底）
BACK_IDS = ("iv_back",) + DIALOG_CANCEL_IDS

# 主页上 Chime Base 设备条目的候选 resource-id
HOME_JINGLE_NAME_IDS = ("tvJingleNeutralName", "tvJingleBaseName")

# 依赖设备/账号状态的不可达项（报告中静态标注，供人工补探）
UNREACHABLE_NOTES = (
    "编辑时间段（SleepTimeAddActivity 编辑模式，标题'编辑时间段'）：需铃铛勿扰"
    "列表已有时间段；若本趟「保存」已创建时间段，重跑本工具即可探测编辑模式",
    "设备分享-已分享用户条目操作（删除/权限修改）：当前无已分享用户，"
    "仅空态与添加入口可罗列",
)


def _activity_short(page: BasePage) -> str:
    """取当前前台 Activity 的短类名（如 DeviceInfoActivity）。"""
    full = (page.get_current_activity() or "").strip().rstrip("}")
    return full.split("/")[-1].split(".")[-1] if full else ""


def _load_known_activities() -> set:
    """合并历史 dump 产物中出现过的前台 Activity（跨运行增量去重）。"""
    known = set(MANUAL_KNOWN_ACTIVITIES)
    for summary in DUMP_DIR.glob("*_summary.txt"):
        try:
            for line in summary.read_text(encoding="utf-8").splitlines():
                if not line.startswith("前台 Activity"):
                    continue
                full = line.split("：", 1)[-1].strip().rstrip("}")
                short = full.split("/")[-1].split(".")[-1]
                if short:
                    known.add(short)
        except OSError:
            continue
    logger.info(f"已知 Activity 共 {len(known)} 个（含历史 dump 合并）")
    return known


def _dump_page(page: BasePage, reason: str,
               max_retries: int = 5, interval: float = 2.0) -> dict:
    """带重试的当前页面层级抓取（走 BasePage.dump_hierarchy 门控）。"""
    for attempt in range(1, max_retries + 1):
        raw = page.dump_hierarchy(f"{reason}（explore_deep.py 第 {attempt} 次尝试）")
        if count_nodes(get_root(raw)) > 1:
            return raw
        time.sleep(interval)
    raise RuntimeError("层级树为空，PocoService 可能未就绪")


def _nodes_of(raw: dict) -> list:
    """展平层级树为节点属性列表。"""
    nodes: list = []
    walk_nodes(get_root(raw), 0, nodes)
    return nodes


def _collect_candidates(raw: dict, limit: int) -> list:
    """收集可点入口候选（罗列层，含危险入口，按 (id, text) 去重）。

    注意：
    1. 本 app 无障碍树多不暴露 ``clickable`` 属性（2026-10-11 真机
       JingleBaseActivity dump 验证，全部节点 click=None），因此**不要求**
       clickable=True，改用「可见 + 面积适中 + 非结构容器」启发式。
    2. 按 (id, text) 去重而非仅 id：设置宫格/列表条目共用 tv_title 等 id，
       需按文本区分（'铃铛勿扰'/'声音设置'/...）。
    3. 危险词命中者带 ``danger=True`` 标记——**只进报告，实际点击层过滤**。
    """
    cands, seen = [], set()
    for n in _nodes_of(raw):
        rid = n["id"] or ""
        if APP_PKG_PREFIX not in rid:
            continue
        short = rid.replace(APP_PKG_PREFIX, "")
        if short in STRUCTURAL_IDS:
            continue
        if not n["visible"]:
            continue
        text = n["text"] or ""
        key = (short, text)
        if key in seen:
            continue
        size = n["size"] or [0, 0]
        if not n["pos"] or size[0] < 0.005 or size[1] < 0.005:
            continue
        if size[0] * size[1] > MAX_NODE_AREA:
            continue
        seen.add(key)
        danger = (short in DANGER_IDS or short in BACK_IDS
                  or any(word in text for word in DANGER_TEXTS))
        cands.append({"id": short, "text": text, "type": n["type"],
                      "danger": danger})
        if len(cands) >= limit:
            break
    return cands


def _merge_candidates(frames: list, limit: int) -> list:
    """合并多帧（滚动前后）候选，按 (id, text) 去重。"""
    cands, seen = [], set()
    for raw in frames:
        for c in _collect_candidates(raw, limit * 2):
            key = (c["id"], c["text"])
            if key in seen:
                continue
            seen.add(key)
            cands.append(c)
    return cands[:limit]


def _merge_nodes(frames: list) -> list:
    """合并多帧节点（元素清单罗列用），按 (id, text) 去重。"""
    merged, seen = [], set()
    for raw in frames:
        for n in _nodes_of(raw):
            key = (n["id"], n["text"])
            if key in seen:
                continue
            seen.add(key)
            merged.append(n)
    return merged


def _app_ids(raw: dict) -> set:
    """取层级树中全部可见的 app resource-id 短名集合（弹框 diff 用）。"""
    return {n["id"].replace(APP_PKG_PREFIX, "")
            for n in _nodes_of(raw)
            if n["id"] and APP_PKG_PREFIX in n["id"] and n["visible"]}


def _save_artifacts(raw: dict, activity_full: str, tag: str) -> tuple:
    """落盘 deep_<tag> 产物（JSON + 元素汇总），返回文件名二元组。"""
    nodes = _nodes_of(raw)
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DUMP_DIR / f"deep_{tag}.json"
    json_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    summary_path = DUMP_DIR / f"deep_{tag}_summary.txt"
    summary_path.write_text(
        "\n".join([f"前台 Activity：{activity_full or '(未知)'}",
                   f"探测标签：{tag}"] + build_summary(nodes, activity_full)),
        encoding="utf-8",
    )
    logger.info(f"[{tag}] 产物：{json_path.name} / {summary_path.name}")
    return json_path.name, summary_path.name


def _sections_from_nodes(nodes: list, activity_full: str) -> list:
    """取汇总文本的【一】【二】两段（app id 节点 + 无 id 文本节点）。"""
    lines = build_summary(nodes, activity_full)
    result = []
    for line in lines:
        if line.startswith("【三、"):
            break
        result.append(line)
    return result


class DeepExplorer:
    """jingle 首页起的 DFS 页面探测器（增量 / --full 全量两种模式）。"""

    def __init__(self, poco, page: BasePage, reason: str, settle: float,
                 max_pages: int, max_candidates: int, known: set,
                 full: bool = False):
        self.poco = poco
        self.page = page
        self.reason = reason
        self.settle = settle
        self.max_pages = max_pages
        self.max_candidates = max_candidates
        self.known = known
        self.full = full
        self.visited: dict = {}   # activity短名 -> {"path", "json", "summary", "nodes", "known"}
        self.edges: list = []     # 入口记录 {"parent","entry","text","child","kind","note"}
        self.issues: list = []    # 异常与恢复记录
        self._dlg_count = 0

    # ==================== 基础操作 ====================

    def current(self) -> str:
        return _activity_short(self.page)

    def app_foreground(self) -> bool:
        return APP_PACKAGE in (self.page.get_current_activity() or "")

    def _locate(self, cand: dict):
        """按候选定位节点：优先 (id, text) 精确匹配；id 兜底需文本一致。

        id 兜底必须校验文本（2026-10-11 路径恢复教训：目标条目在屏外时，
        id 兜底会撞上同 id 的工具栏标题等节点，点错节点导致恢复失败）。
        """
        if cand["text"]:
            node = self.poco(RID + cand["id"], text=cand["text"])
            if node.exists():
                return node
        node = self.poco(RID + cand["id"])
        if not node.exists():
            return None
        if cand["text"]:
            try:
                text = node.attr("text") or ""
            except Exception:  # noqa: BLE001
                return None
            if text and text != cand["text"]:
                return None  # 撞 id 的其他节点，拒绝（走滚动补救）
        return node

    def _click(self, cand: dict) -> bool:
        """点击候选入口，返回是否发生了补救滚动（同页场景用于回滚顶部）。

        定位失败时的补救（2026-10-11 真机教训）：
        1. 先关弹框重试——时间选择器等弹框未关时页面节点不在无障碍树中，
           表现为「入口不存在」（上趟 SleepTimeAdd/CreateFamily 28 条失败主因）
        2. 再上滑（最多 2 次）露出页面底部重试——保存按钮/底部列表条目等
           屏外入口（如设置页「通用设置」条目，撞 id 误点工具栏标题的教训）
        """
        node = self._locate(cand)
        if node is None and self.dismiss_dialog():
            time.sleep(0.8)
            node = self._locate(cand)
        if node is not None:
            node.click()
            return False
        for _ in range(2):
            self.poco.swipe([0.5, 0.75], [0.5, 0.35], duration=0.8)
            time.sleep(1.0)
            node = self._locate(cand)
            if node is not None:
                node.click()
                return True
        raise RuntimeError(f"入口 {cand['id']}({cand['text']!r}) 不存在"
                           "（弹框遮挡与滚动补救后仍未找到）")

    def _confirm_dialog(self) -> bool:
        """点击弹框确认按钮（用户授权：非危险弹框正常确认观察）。"""
        for rid in DIALOG_CONFIRM_IDS:
            try:
                node = self.poco(RID + rid)
                if node.exists():
                    node.click()
                    time.sleep(1.0)
                    return True
            except Exception:  # noqa: BLE001 弹框消失竞态按未命中处理
                continue
        return False

    def _safe_close_dialog(self) -> None:
        """关闭弹框：优先取消按钮，否则系统返回键。"""
        if not self.dismiss_dialog():
            self.page.press_back()
            time.sleep(1.0)

    @staticmethod
    def _raw_has_danger(raw: dict) -> bool:
        """判断层级树文本是否含危险词（弹框确认前的最后一道防线）。"""
        return any(any(word in n["text"] for word in DANGER_TEXTS)
                   for n in _nodes_of(raw) if n["text"])

    def dismiss_dialog(self) -> bool:
        """关闭弹框（只点取消类按钮）。成功点击返回 True。"""
        for rid in DIALOG_CANCEL_IDS:
            try:
                node = self.poco(RID + rid)
                if node.exists():
                    node.click()
                    time.sleep(1.0)
                    return True
            except Exception:  # noqa: BLE001 弹框消失竞态按未命中处理
                continue
        return False

    def back_to(self, target: str, tries: int = 5) -> bool:
        """返回到指定 Activity（弹框优先取消，其次返回键）。"""
        for _ in range(tries):
            if self.current() == target:
                return True
            if not self.app_foreground():
                return False
            if not self.dismiss_dialog():
                self.page.press_back()
            time.sleep(self.settle)
        return self.current() == target

    # ==================== 滚动补充采集 ====================

    def _swipe_collect(self, base_raw: dict) -> list:
        """上滑补充屏外入口（设置页底部按钮等），返回多帧 raw 列表。

        每次上滑后 dump 一帧，无新增 app id 即停止（最多 2 次），
        结束后等次数下滑滚回顶部，保证后续按 (id, text) 点击时入口可见。
        """
        frames = [base_raw]
        merged = _app_ids(base_raw)
        swipes = 0
        for _ in range(3):
            self.poco.swipe([0.5, 0.75], [0.5, 0.35], duration=0.8)
            swipes += 1
            time.sleep(1.2)
            try:
                raw2 = _dump_page(self.page, f"{self.reason} 滚动补充采集")
            except Exception as exc:  # noqa: BLE001 采集失败按当前帧收束
                logger.warning(f"滚动补充采集失败：{exc}")
                break
            frames.append(raw2)
            new_ids = _app_ids(raw2) - merged
            merged |= _app_ids(raw2)
            if not new_ids:
                break
        for _ in range(swipes):
            self.poco.swipe([0.5, 0.35], [0.5, 0.75], duration=0.8)
            time.sleep(0.8)
        if swipes:
            logger.info(f"滚动补充采集 {swipes} 次，合并后 app id {len(merged)} 个")
        return frames

    # ==================== 导航 ====================

    def _go_main_page(self) -> None:
        """从任意 jingle 层级回到主页（系统返回键循环）。"""
        main = CloudEdgeMainPage(poco=self.poco, udid=self.page.udid)
        if main.is_home_page():
            return
        for _ in range(8):
            if not self.app_foreground():
                raise RuntimeError("app 已不在前台，请手动打开 app 后重试")
            self.page.press_back()
            time.sleep(self.settle)
            if main.is_home_page():
                return
        raise RuntimeError("连续返回仍未回到主页，请手动回到主页后重试")

    def enter_jingle_home(self, sn: str = "") -> str:
        """主页点击 Chime Base 设备条目，进入 jingle 首页。

        :param sn: 指定设备 SN（缺省取主页第一个 Chime Base 条目）
        :return: 实际点击的设备 SN
        """
        self._go_main_page()
        target_text = ""
        for rid in HOME_JINGLE_NAME_IDS:
            try:
                for node in self.poco(RID + rid):
                    text = node.attr("text")
                    if text and (not sn or text == sn):
                        target_text = text
                        break
            except Exception:  # noqa: BLE001 该 id 不存在时跳过
                continue
            if target_text:
                break
        if not target_text:
            raise RuntimeError("主页未找到 Chime Base 设备条目"
                               + (f"（SN={sn}）" if sn else ""))

        for attempt in range(3):
            node = None
            for rid in HOME_JINGLE_NAME_IDS:
                try:
                    for n in self.poco(RID + rid):
                        if n.attr("text") == target_text:
                            node = n
                            break
                except Exception:  # noqa: BLE001
                    continue
                if node:
                    break
            if node is None:
                raise RuntimeError("设备条目消失，无法点击")
            node.click()
            time.sleep(self.settle)
            if self.current() == START_ACTIVITY:
                logger.info(f"已进入 jingle 首页（设备 {target_text}，"
                            f"模式：{'全量' if self.full else '增量'}）")
                return target_text
            logger.warning(
                f"第 {attempt + 1}/3 次点击设备未进入 jingle 首页"
                f"（当前 {self.current()}），重试")
        raise RuntimeError(f"点击设备 {target_text} 3 次仍未进入 jingle 首页")

    def _recover(self, path: list) -> None:
        """路径恢复：回主页 → 重进设备 → 重放入口路径到原页面。

        :param path: [(入口id, 入口text, 子Activity), ...]（从 jingle 首页起）
        """
        logger.warning(f"执行路径恢复（{len(path)} 级）")
        self.enter_jingle_home()
        for entry_id, entry_text, child in path:
            self._click({"id": entry_id, "text": entry_text})
            time.sleep(self.settle)
            if self.current() != child:
                raise RuntimeError(
                    f"路径恢复失败：点击 {entry_id} 后应为 {child}，"
                    f"实际 {self.current()}")
        self.issues.append(f"路径恢复成功（{len(path)} 级）")

    # ==================== 探测主流程 ====================

    def _record(self, parent: str, cand: dict, child: str,
                kind: str, note: str) -> None:
        self.edges.append({
            "parent": parent, "entry": cand["id"], "text": cand["text"],
            "child": child, "kind": kind, "note": note,
        })
        logger.info(f"[{parent}] --{cand['id']}({cand['text']!r})--> "
                    f"{child or '(无变化)'}：{note}")

    def _observe_same_page(self, act: str, cand: dict, base_ids: set,
                           scrolled: bool = False) -> None:
        """同 Activity 反应观察：弹框落盘 → 正常确认 → 记录，开关还原原状。

        用户授权（2026-10-11）：除格式化/删除/升级外均可正常探测——弹框
        落盘后点「确认」观察实际效果；弹框文本含危险词时仅取消（防线）。
        """
        try:
            raw2 = _dump_page(self.page, f"{self.reason} 同页反应观察")
        except Exception as exc:  # noqa: BLE001 观察失败不阻断
            self._record(act, cand, act, "same", f"同页观察失败：{exc}")
            self._safe_close_dialog()
            return
        new_ids = _app_ids(raw2) - base_ids
        if new_ids:
            self._dlg_count += 1
            tag = f"{act}_dlg{self._dlg_count}"
            activity_full = self.page.get_current_activity().rstrip("}")
            _save_artifacts(raw2, activity_full, tag)
            extra = f"（新增控件：{','.join(sorted(new_ids)[:8])}）"
            if self._raw_has_danger(raw2):
                self._safe_close_dialog()
                self._record(act, cand, act, "same",
                             f"同页弹框{extra}（含危险词，仅取消）")
            elif self._confirm_dialog():
                time.sleep(self.settle)
                if self.current() != act:
                    self.back_to(act)
                self._record(act, cand, act, "same",
                             f"同页弹框{extra}（已点击确认）")
            else:
                self._safe_close_dialog()
                self._record(act, cand, act, "same",
                             f"同页弹框{extra}（无确认按钮，已取消/返回）")
        else:
            self._record(act, cand, act, "same", "同页无弹框（状态切换/无反应）")

        # 开关类还原：再点一次；若再弹确认框则确认使还原生效
        if "switch" in cand["id"].lower() or "Switch" in (cand["type"] or ""):
            try:
                self._click(cand)
                time.sleep(1.0)
                if not self._confirm_dialog():
                    self.dismiss_dialog()
            except Exception:  # noqa: BLE001
                pass
        if scrolled and self.current() == act:
            self.poco.swipe([0.5, 0.35], [0.5, 0.75], duration=0.8)
            time.sleep(0.8)
        if self.current() != act:
            self.back_to(act)

    def explore(self, act: str, path: list) -> None:
        """DFS 探测当前页面：dump（含滚动）→ 逐入口点击 → 分类处理。

        :param act: 当前 Activity 短名（调用前保证设备停在该页面）
        :param path: 从 jingle 首页到本页面的入口路径（恢复用）
        """
        raw = _dump_page(self.page, f"{self.reason} 页面 {act}")
        activity_full = self.page.get_current_activity().rstrip("}")
        frames = self._swipe_collect(raw)
        merged_nodes = _merge_nodes(frames)
        candidates = _merge_candidates(frames, self.max_candidates)

        register = act not in self.visited and (
            self.full or act == START_ACTIVITY or act not in self.known)
        if register:
            json_name, sum_name = _save_artifacts(raw, activity_full, act)
            self.visited[act] = {
                "path": list(path),
                "json": json_name, "summary": sum_name,
                "nodes": merged_nodes,
                "known": act in self.known,
            }
            logger.info(f"[{act}] {'已知页面（全量罗列）' if act in self.known else '新发现页面'}，"
                        f"合并元素 {len(merged_nodes)} 个，候选入口 {len(candidates)} 个")

        base_ids = {n["id"].replace(APP_PKG_PREFIX, "")
                    for n in merged_nodes
                    if n["id"] and APP_PKG_PREFIX in n["id"] and n["visible"]}

        for cand in candidates:
            if len(self.visited) >= self.max_pages:
                self.issues.append(
                    f"达到单趟页面上限 {self.max_pages}，{act} 剩余入口未探测")
                return
            if cand["danger"]:
                self._record(act, cand, "", "danger",
                             "黑名单入口（格式化/删除/升级/返回类）：只罗列未点击")
                continue
            try:
                scrolled = self._click(cand)
            except Exception as exc:  # noqa: BLE001 单入口失败不阻断
                self._record(act, cand, "", "fail", f"点击失败：{exc}")
                continue
            time.sleep(self.settle)

            if not self.app_foreground():
                self._record(act, cand, "", "external", "离开 app（外部页面）")
                self.page.press_back()
                time.sleep(self.settle)
                if not self.app_foreground():
                    raise RuntimeError("离开 app 后无法回到前台，终止探测")
                continue

            new_act = self.current()
            if new_act == act:
                self._observe_same_page(act, cand, base_ids, scrolled)
            elif new_act in EXCLUDED_ACTIVITIES:
                self._record(act, cand, new_act, "excluded",
                             "添加设备向导（安全约定不深入）")
                if not self.back_to(act):
                    self._recover(path)
            elif new_act in self.visited:
                self._record(act, cand, new_act, "visited", "本趟已访问（跳过）")
                if not self.back_to(act):
                    self._recover(path)
            elif self.full or new_act not in self.known:
                note = "已知页面（全量模式深入）" if new_act in self.known \
                    else "新页面"
                self._record(act, cand, new_act, "new", note)
                self.explore(new_act,
                             path + [(cand["id"], cand["text"], new_act)])
                if self.current() != act and not self.back_to(act):
                    self._recover(path)
            else:
                self._record(act, cand, new_act, "known",
                             "已知页面（增量模式不深入）")
                if not self.back_to(act):
                    self._recover(path)

    # ==================== 报告 ====================

    def write_report(self, sn: str) -> Path:
        """输出汇总报告 deep_report.txt，返回路径。"""
        mode = "全量（--full：已知页面穿透罗列）" if self.full else "增量（只罗列新页面）"
        lines = [
            "=" * 100,
            "jingle 深度探测报告（explore_deep.py）",
            f"时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"设备 SN：{sn}",
            f"模式：{mode}",
            f"探测范围：主页点击设备 SN → {START_ACTIVITY} 起 DFS 自动遍历",
            f"已知 Activity（含历史 dump 合并）：{len(self.known)} 个",
            "=" * 100,
            "",
            "【一、页面树（DFS 访问顺序）】",
        ]
        for idx, (act, info) in enumerate(self.visited.items(), 1):
            depth = len(info["path"])
            via = (f"（经 {info['path'][-1][0]} 进入）"
                   if info["path"] else "（起点：主页点击设备 SN）")
            tag = "已知" if info["known"] else "新发现"
            lines.append(f"  [{'%02d' % idx}] {'    ' * depth}{act} "
                         f"[{tag}]{via}")

        lines += ["", f"【二、页面元素清单：{len(self.visited)} 页（供筛选）】"]
        for idx, (act, info) in enumerate(self.visited.items(), 1):
            depth = len(info["path"])
            chain = START_ACTIVITY + "".join(
                f" --{e}({t!r})--> {c}" for e, t, c in info["path"])
            lines += [
                "",
                f"[{'%02d' % idx}] {act}"
                f"（{'已知页面·全量罗列' if info['known'] else '新发现页面'}，"
                f"第 {depth + 1} 层）",
                f"    路径：{chain}",
                f"    产物：{info['json']} / {info['summary']}",
                "    元素（app resource-id + 无 id 文本节点）：",
            ]
            sections = _sections_from_nodes(info["nodes"], act)
            lines += [f"        {ln}" for ln in sections if ln.strip()]

        danger_edges = [e for e in self.edges if e["kind"] == "danger"]
        lines += ["", f"【三、安全黑名单入口（格式化/删除/升级/返回按钮，"
                      f"只罗列未点击）：{len(danger_edges)} 个】"]
        for e in danger_edges:
            lines.append(f"    {e['parent']} --{e['entry']}({e['text']!r})")

        dlg_edges = [e for e in self.edges
                     if e["kind"] == "same" and "同页弹框" in e["note"]]
        lines += ["", f"【四、同页弹框状态：{len(dlg_edges)} 个（产物 deep_*_dlg*）】"]
        for e in dlg_edges:
            lines.append(f"    {e['parent']} --{e['entry']}({e['text']!r})：{e['note']}")

        page_edges = [e for e in self.edges
                      if e["kind"] in ("new", "known", "visited", "excluded")]
        lines += ["", f"【五、通向页面的入口明细：{len(page_edges)} 条】"]
        for e in page_edges:
            lines.append(f"    {e['parent']} --{e['entry']}({e['text']!r})--> "
                         f"{e['child']}：{e['note']}")

        same_edges = [e for e in self.edges if e["kind"] == "same"]
        lines += ["", f"【六、同页反应（开关/选择/无反应）：{len(same_edges)} 条】"]
        for e in same_edges:
            lines.append(f"    {e['parent']} --{e['entry']}({e['text']!r})：{e['note']}")

        fail_edges = [e for e in self.edges if e["kind"] in ("fail", "external")]
        lines += ["", f"【七、点击失败/离开 app 的入口：{len(fail_edges)} 条】"]
        for e in fail_edges:
            lines.append(f"    {e['parent']} --{e['entry']}({e['text']!r})：{e['note']}")

        lines += ["", f"【八、依赖状态不可达项（静态标注）：{len(UNREACHABLE_NOTES)} 条】"]
        for note in UNREACHABLE_NOTES:
            lines.append(f"    - {note}")

        lines += ["", f"【九、异常与恢复记录：{len(self.issues)} 条】"]
        for issue in self.issues:
            lines.append(f"    {issue}")

        lines += [
            "",
            "说明：",
            "1. 安全黑名单（2026-10-11 用户授权收窄）：仅格式化/删除/升级/"
            "恢复出厂及返回类按钮只罗列未点击；其余入口（含确定/保存/完成/"
            "重启/解绑等）均已正常点击探测，弹框已点确认观察，开关已还原。",
            "2. 添加设备向导（PowerOnActivity/AddSeriesTypeActivity）按安全约定"
            "只记命中不深入。",
            "3. 同页非开关类点击（如铃声选定/场景选定/星期勾选/家庭选择+确定/"
            "时间段保存）可能已切换并保存设备配置（用户授权正常探测），"
            "如需还原请手动检查勿扰时间段/使用场景/所属家庭/报警推送等设置。",
            "4. 屏幕外入口已通过滚动采集罗列，但点击仍以顶部可见为准，"
            "点击失败条目可用 tools/explore_page.py 精探。",
            "5. 增量模式重跑时，历史 deep_* 产物中的 Activity 自动并入已知集合；"
            "全量模式不受影响，始终逐页罗列。",
            "=" * 100,
        ]

        DUMP_DIR.mkdir(parents=True, exist_ok=True)
        report_path = DUMP_DIR / "deep_report.txt"
        report_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"汇总报告：{report_path}")
        return report_path


def main() -> int:
    """脚本入口：主页 → jingle 首页 → DFS 探测（增量/全量）→ 报告。"""
    parser = argparse.ArgumentParser(
        description="从 jingle 首页起 DFS 自动遍历页面，dump 并产出页面树报告"
    )
    parser.add_argument("--reason", required=True,
                        help="探测诉求（必填，透传给 dump_hierarchy 门控）")
    parser.add_argument("--full", action="store_true",
                        help="全量模式：已知页面同样穿透罗列并深入到最深层级"
                             "（主页→设备首页→设置→全部子页面）")
    parser.add_argument("--sn", default="",
                        help="指定设备 SN（缺省取主页第一个 Chime Base 条目）")
    parser.add_argument("--udid", default="",
                        help="目标设备 UDID（缺省自动选第一台在线安卓设备）")
    parser.add_argument("--settle", type=float, default=2.5,
                        help="页面切换等待秒（默认 2.5）")
    parser.add_argument("--max-pages", type=int, default=0,
                        help="单趟页面数上限（默认：增量 15 / 全量 40）")
    parser.add_argument("--max-candidates", type=int, default=0,
                        help="每页候选入口数上限（默认：增量 30 / 全量 60，"
                             "设备信息页约 40 个候选，全量务必 >= 60）")
    args = parser.parse_args()

    max_pages = args.max_pages or (40 if args.full else 15)
    max_candidates = args.max_candidates or (60 if args.full else 30)

    from utils.dump_page import _resolve_udid  # noqa: PLC0415 延迟导入避免循环

    try:
        udid = _resolve_udid(args.udid)
        device = connect_device(f"android:///{udid}")
        poco = AndroidUiautomationPoco(
            device=device,
            use_airtest_input=True,
            screenshot_each_action=False,
        )
        page = BasePage(poco=poco, udid=udid, platform="android")
        known = _load_known_activities()

        explorer = DeepExplorer(
            poco, page, args.reason, args.settle,
            max_pages, max_candidates, known, full=args.full)
        sn = explorer.enter_jingle_home(args.sn)

        # 遍历异常也保留已采集数据出报告（2026-10-11 教训：路径恢复失败
        # 曾导致整趟 20 分钟数据全部丢失）
        probe_error = None
        try:
            explorer.explore(START_ACTIVITY, [])
        except Exception as exc:  # noqa: BLE001
            probe_error = exc
            logger.error(f"遍历中断：{exc}（已访问 {len(explorer.visited)} 页，"
                         "仍输出报告）")

        report = explorer.write_report(sn)

        known_count = len([1 for info in explorer.visited.values() if info["known"]])
        new_count = len(explorer.visited) - known_count
        danger_count = len([e for e in explorer.edges if e["kind"] == "danger"])
        logger.info("=" * 60)
        logger.info(f"访问页面 {len(explorer.visited)} 个"
                    f"（已知 {known_count} / 新发现 {new_count}），"
                    f"弹框 {explorer._dlg_count} 个，"
                    f"入口记录 {len(explorer.edges)} 条"
                    f"（危险入口只罗列 {danger_count} 条）")
        logger.info(f"报告：{report}")
        if probe_error is not None:
            logger.error(f"注意：本趟遍历中途出错（{probe_error}），"
                         "报告仅含出错前采集的数据")
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001 CLI 工具统一兜底
        logger.error(f"深度探测失败：{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
