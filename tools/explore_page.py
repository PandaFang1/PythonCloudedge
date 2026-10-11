"""jingle 设置子页面下一级页面探测脚本（CLI 工具，Android 端）。

用途：
    从指定的父页面（--parent）逐个点击入口（--entries），进入下一级页面，
    dump 其完整 UI 层级后自动返回父页面。产物固定命名，便于直接查阅。

    与 utils/dump_page.py 的分工：
    - utils/dump_page.py    → 采集「当前页面」层级（单页，不动导航）
    - tools/explore_page.py → 探测「点击入口后的新页面」（含导航与返回）

用法：
    # 探测设备信息页的 4 个下一级页面
    python tools/explore_page.py --reason "设备信息页下一级定位器采集" ^
        --parent jingle_device_info_page ^
        --entries layout_device_name,layout_device_scene,layout_location_manager,layout_firmware_version

    # 探测设置页本身的入口
    python tools/explore_page.py --reason "..." --parent jingle_setting_page --entries btn_reset

安全约定（探测规则，见 tools/README.md）：
    - 走项目唯一收口 ``BasePage.dump_hierarchy(reason)``，--reason 必填
    - 探测过程只执行「返回类」操作（iv_back / negativeButton / 系统返回键），
      永不点击确认类按钮（tv_confirm / positiveButton / btn_format 等）
    - 每个入口探测完必须验证父页面重新加载，验证失败立即终止后续探测
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
from pages.base_page import BasePage  # noqa: E402
from pages.page_factory import PageFactory  # noqa: E402
from utils.dump_page import (  # noqa: E402
    DUMP_DIR,
    build_summary,
    count_nodes,
    get_root,
    walk_nodes,
)
from utils.log_utils import get_logger  # noqa: E402

logger = get_logger(__name__)

# 父页面名 → 设置页上的导航方法名（新增子页面 PO 后在此登记）
NAVIGATE_MAP = {
    "jingle_setting_page": None,
    "jingle_device_info_page": "open_device_info_page",
    "jingle_bell_dnd_page": "open_bell_dnd_page",
    "jingle_ringtone_page": "open_ringtone_page",
    "jingle_device_share_page": "open_device_share_page",
    "jingle_sound_page": "open_sound_page",
    "jingle_storage_page": "open_storage_page",
    "jingle_general_page": "open_general_page",
    # 下级页面（2026-10-11 新增，两级导航：中间页名:方法名）
    "jingle_device_name_page": "jingle_device_info_page:open_device_name_page",
    "jingle_device_scene_page": "jingle_device_info_page:open_device_scene_page",
    "jingle_device_location_page": "jingle_device_info_page:open_location_manager_page",
    "jingle_device_version_page": "jingle_device_info_page:open_device_version_page",
    "jingle_sleep_time_add_page": "jingle_bell_dnd_page:open_sleep_time_add_page",
    "jingle_share_type_page": "jingle_device_share_page:open_share_type_page",
    "jingle_install_guide_page": "jingle_general_page:open_install_guide_page",
    "jingle_unbind_channel_page": "jingle_general_page:open_unbind_page",
}

# 返回类按钮优先级（探测页面上的关闭/取消控件）
BACK_BUTTONS = ("iv_back", "negativeButton", "tv_cancel")

# 被测 app 包名（用于判断 app 是否仍在前台）
APP_PACKAGE = "com.cloudedge.smarteye"


def _goto_parent(poco, udid: str, parent_name: str, settle: float) -> BasePage:
    """导航到指定的父页面。

    任意 jingle 页面 → （系统返回键循环）→ 设置页 → NAVIGATE_MAP 导航 → 父页面。

    :param poco: poco 驱动
    :param udid: 设备 UDID
    :param parent_name: 父页面 PO 名称（PageFactory key）
    :param settle: 页面切换等待秒数
    :return: 父页面 PO 实例
    :raises RuntimeError: 无法回到设置页 / 父页面未登记且未加载 / 导航失败
    """
    settings = PageFactory.create("android", "jingle_setting_page",
                                  poco=poco, udid=udid)

    if not settings.is_setting_page():
        for _ in range(6):
            activity = settings.get_current_activity() or ""
            if APP_PACKAGE not in activity:
                raise RuntimeError("app 已不在前台，请手动打开 app 后重试")
            settings.press_back()
            time.sleep(settle)
            if settings.is_setting_page():
                break
        if not settings.is_setting_page():
            raise RuntimeError("连续返回仍未回到设置页，请手动回到设置页后重试")

    if parent_name == "jingle_setting_page":
        settings.wait_for_page_loaded()
        return settings

    if parent_name not in NAVIGATE_MAP:
        page = PageFactory.create("android", parent_name, poco=poco, udid=udid)
        if not page.wait_for_page_loaded(timeout=3.0):
            raise RuntimeError(
                f"父页面 [{parent_name}] 未登记导航路径且当前未加载，"
                f"请先在 NAVIGATE_MAP 登记，或手动导航到该页面所在层级")
        return page

    # NAVIGATE_MAP 值两种形式：
    # - "open_xxx"：设置页上的方法（一级导航）
    # - "父页面名:open_xxx"：先导航到中间页，再调其上的方法（两级导航）
    value = NAVIGATE_MAP[parent_name]
    if ":" in value:
        mid_name, method_name = value.split(":", 1)
        mid_page = _goto_parent(poco, udid, mid_name, settle)
        host = mid_page
    else:
        method_name = value
        host = settings
    method = getattr(host, method_name)
    page = method()
    if not page.wait_for_page_loaded():
        raise RuntimeError(f"导航到父页面 [{parent_name}] 失败")
    logger.info(f"已导航到父页面：{parent_name}")
    return page


def _dump_target(page: BasePage, tag: str, reason: str,
                 max_retries: int, interval: float) -> int:
    """dump 探测到的下一级页面并落盘（固定文件名，重探覆盖）。

    :param page: BasePage 实例
    :param tag: 产物标签（固定命名 explore_<tag>.json）
    :param reason: 门控理由
    :param max_retries: 层级为空时最大重试次数
    :param interval: 重试间隔秒
    :return: 节点数
    :raises RuntimeError: 重试耗尽仍为空
    """
    raw = None
    count = 0
    for attempt in range(1, max_retries + 1):
        raw = page.dump_hierarchy(
            f"{reason}（explore_page.py 入口 {tag} 第 {attempt} 次尝试）")
        count = count_nodes(get_root(raw))
        if count > 1:
            break
        time.sleep(interval)
    if raw is None or count <= 1:
        raise RuntimeError(f"入口 [{tag}] dump 层级树为空，PocoService 可能未就绪")

    activity = page.get_current_activity().rstrip("}")
    nodes = []
    walk_nodes(get_root(raw), 0, nodes)

    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    json_path = DUMP_DIR / f"explore_{tag}.json"
    json_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    summary_path = DUMP_DIR / f"explore_{tag}_summary.txt"
    summary_path.write_text(
        "\n".join([f"前台 Activity：{activity or '(未知)'}",
                   f"探测入口：{tag}"] + build_summary(nodes, activity)),
        encoding="utf-8",
    )
    logger.info(f"[{tag}] 节点数 {count}，Activity {activity.split('/')[-1]}")
    logger.info(f"[{tag}] 产物：{json_path.name} / {summary_path.name}")
    return count


def _back_to_parent(poco, page: BasePage, parent: BasePage,
                    tag: str, settle: float, max_tries: int = 4) -> bool:
    """从探测页面返回父页面（只点返回类按钮，验证父页加载）。

    :param poco: poco 驱动
    :param page: BasePage 实例（用于系统返回键）
    :param parent: 父页面 PO 实例
    :param tag: 入口标签（日志用）
    :param settle: 每次返回操作后的等待秒数
    :param max_tries: 最大返回尝试次数
    :return: 父页面加载成功返回 True
    """
    for _ in range(max_tries):
        try:
            if parent.wait_for_page_loaded(timeout=2.0):
                return True
        except Exception:  # noqa: BLE001 切换动画中按未就绪处理
            pass
        for button in BACK_BUTTONS:
            node = poco(RID + button)
            try:
                if node.exists():
                    node.click()
                    break
            except Exception:  # noqa: BLE001
                continue
        else:
            page.press_back()
        time.sleep(settle)
    ok = parent.wait_for_page_loaded(timeout=3.0)
    logger.warning(f"[{tag}] 返回父页面{'成功' if ok else '失败'}")
    return ok


def main() -> int:
    """脚本入口：逐个入口探测下一级页面并 dump。

    :return: 进程退出码（0 全部成功，1 存在失败）
    """
    parser = argparse.ArgumentParser(
        description="探测父页面各入口的下一级页面并采集 UI 层级（含导航与返回）"
    )
    parser.add_argument("--reason", required=True,
                        help="探测诉求（必填，透传给 dump_hierarchy 门控）")
    parser.add_argument("--parent", required=True,
                        help="父页面 PO 名称（PageFactory key，如 jingle_device_info_page）")
    parser.add_argument("--entries", required=True,
                        help="待探测入口 resource-id，逗号分隔（如 layout_device_name,btn_add）")
    parser.add_argument("--udid", default="",
                        help="目标设备 UDID（缺省自动选第一台在线安卓设备）")
    parser.add_argument("--settle", type=float, default=3.0,
                        help="页面切换等待秒（默认 3.0）")
    parser.add_argument("--max-retries", type=int, default=5,
                        help="层级为空时最大重试次数（默认 5）")
    args = parser.parse_args()

    from utils.dump_page import _resolve_udid  # noqa: PLC0415 延迟导入避免循环

    entries = [e.strip() for e in args.entries.split(",") if e.strip()]
    results = {}
    try:
        udid = _resolve_udid(args.udid)
        device = connect_device(f"android:///{udid}")
        poco = AndroidUiautomationPoco(
            device=device,
            use_airtest_input=True,
            screenshot_each_action=False,
        )
        page = BasePage(poco=poco, udid=udid, platform="android")

        parent = _goto_parent(poco, udid, args.parent, args.settle)

        for entry in entries:
            try:
                node = poco(RID + entry)
                if not node.exists():
                    results[entry] = "入口不存在"
                    logger.error(f"[{entry}] 入口在父页面上不存在，跳过")
                    continue
                node.click()
                time.sleep(args.settle)
                count = _dump_target(page, entry, args.reason,
                                     args.max_retries, 2.0)
                results[entry] = f"成功（{count} 节点）"
                if not _back_to_parent(poco, page, parent, entry, args.settle):
                    results[entry] = "已 dump 但返回父页面失败"
                    break
            except Exception as exc:  # noqa: BLE001 单入口失败不阻断其余入口
                results[entry] = f"失败：{exc}"
                if not _back_to_parent(poco, page, parent, entry, args.settle):
                    logger.error(f"[{entry}] 返回父页面失败，终止后续探测")
                    break

        logger.info("=" * 60)
        for entry, result in results.items():
            logger.info(f"入口 {entry}: {result}")
        return 0 if all("成功" in r for r in results.values()) else 1
    except Exception as exc:  # noqa: BLE001 CLI 工具统一兜底
        logger.error(f"探测失败：{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
