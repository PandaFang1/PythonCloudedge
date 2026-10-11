"""UI 层级 dump 采集脚本（CLI 工具，Android 端）。

用途：
    新增页面 / 维护定位器时，采集当前设备前台页面的完整 UI 层级，
    输出原始 JSON 与关键信息汇总（resource-id / text / visible / pos）。

用法：
    python utils/dump_page.py --reason "jingle 设置页定位器采集"
    python utils/dump_page.py --reason "..." --udid TC55LJMR59W8ZPRK

流程：
    1. PhoneManager 按 --udid 选设备（缺省自动选第一台在线安卓设备）
    2. airtest connect_device → AndroidUiautomationPoco → BasePage
    3. 走项目唯一收口 ``BasePage.dump_hierarchy(reason)``（门控：reason 必填）
    4. PocoService 启动初期层级可能只有根节点，自动轮询重试直至非空
    5. 原始 JSON + 汇总 txt 写入 ``logs/dumps/``

约定（见 docs/reference/extension.md）：
    - 不使用 ``adb shell uiautomator dump``（与 pocoservice 抢占
      accessibility 服务，exit 137，2026-10-09 真机验证）
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

from pages.base_page import BasePage  # noqa: E402
from utils.log_utils import get_logger  # noqa: E402
from utils.phone_manager import PhoneManager  # noqa: E402

logger = get_logger(__name__)

# 汇总输出目录
DUMP_DIR = PROJECT_ROOT / "logs" / "dumps"

# Android app 包名前缀（汇总时用于区分定位器候选与系统控件）
APP_PKG_PREFIX = "com.cloudedge.smarteye:id/"

# 汇总输出行宽（超出部分截断由各字段宽度控制）
SUMMARY_WIDTH = 120


def _count_nodes(node: dict) -> int:
    """统计节点子树（含自身）的节点总数。

    :param node: poco 节点结构 ``{"name", "payload", "children"}``
    :return: 节点总数
    """
    total = 1
    for child in node.get("children", []) or []:
        total += _count_nodes(child)
    return total


def _get_root(raw: dict) -> dict:
    """从 dump_hierarchy 返回值中取根节点。

    poco 各版本返回结构存在两种形态：
    - 根节点本体（顶层直接含 ``children``）
    - ``{"payload": <根节点>}`` 包装

    :param raw: dump_hierarchy 返回的原始 dict
    :return: 根节点 dict
    """
    if "children" in raw or "name" in raw:
        return raw
    payload = raw.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _walk(node: dict, depth: int, out: list) -> None:
    """递归遍历节点树，展平为属性字典列表。

    :param node: poco 节点结构 ``{"name", "payload", "children"}``
    :param depth: 当前深度（根为 0）
    :param out: 输出列表（原地追加）
    """
    attrs = node.get("payload", {}) or {}
    out.append({
        "depth": depth,
        "id": attrs.get("name", "") or "",
        "text": (attrs.get("text", "") or "").replace("\xa0", " "),
        "type": attrs.get("type", ""),
        "visible": attrs.get("visible"),
        "pos": attrs.get("pos"),
        "size": attrs.get("size"),
        "clickable": attrs.get("clickable"),
    })
    for child in node.get("children", []) or []:
        _walk(child, depth + 1, out)


def _dump_with_retry(page: BasePage, reason: str,
                     max_retries: int, interval: float) -> dict:
    """带重试的层级抓取（PocoService 启动初期层级可能为空）。

    :param page: BasePage 实例
    :param reason: 门控理由（透传给 dump_hierarchy）
    :param max_retries: 最大尝试次数
    :param interval: 相邻两次尝试间隔（秒）
    :return: 非空层级树的原始 dict
    :raises RuntimeError: 重试耗尽仍为空时抛出
    """
    for attempt in range(1, max_retries + 1):
        raw = page.dump_hierarchy(f"{reason}（dump_page.py 第 {attempt} 次尝试）")
        count = _count_nodes(_get_root(raw))
        logger.info(f"第 {attempt}/{max_retries} 次 dump，节点数：{count}")
        if count > 1:
            return raw
        time.sleep(interval)
    raise RuntimeError(
        f"连续 {max_retries} 次 dump 层级树均为空，PocoService 可能未就绪，"
        f"请确认设备 {page.udid} 屏幕已点亮且 app 在前台"
    )


def _build_summary(nodes: list, activity: str) -> list:
    """将展平的节点列表组织为汇总文本行。

    :param nodes: _walk 输出的属性字典列表
    :param activity: dump 时的前台 Activity
    :return: 文本行列表
    """
    lines = [
        f"前台 Activity：{activity or '(未知)'}",
        f"总节点数：{len(nodes)}",
        "=" * SUMMARY_WIDTH,
        "",
        "【一、app 包名 resource-id 节点（定位器候选）】",
        f"{'dep':4s} {'resource-id':40s} {'text':24s} "
        f"{'vis':5s} {'pos':19s} {'size':19s} click",
    ]
    for n in nodes:
        if n["id"] and APP_PKG_PREFIX in n["id"]:
            short = n["id"].replace(APP_PKG_PREFIX, "")
            lines.append(
                f"d{n['depth']:02d} {short:40s} {n['text']!r:24s} "
                f"{str(n['visible']):5s} {str(n['pos']):19s} "
                f"{str(n['size']):19s} {n['clickable']}"
            )

    lines += ["", "【二、无 resource-id 但有文本的节点】"]
    for n in nodes:
        if not n["id"] and n["text"]:
            lines.append(
                f"d{n['depth']:02d} type={n['type']:24s} "
                f"text={n['text']!r} vis={n['visible']} pos={n['pos']}"
            )

    lines += ["", "【三、其他 id 节点（系统/容器，供参考）】"]
    for n in nodes:
        if n["id"] and APP_PKG_PREFIX not in n["id"]:
            lines.append(
                f"d{n['depth']:02d} {n['id']:44s} "
                f"text={n['text']!r:20s} vis={n['visible']}"
            )
    return lines


# ==================== 公开别名（供 tools/explore_page.py 等外部工具复用） ====================
count_nodes = _count_nodes
get_root = _get_root
walk_nodes = _walk
build_summary = _build_summary


def _resolve_udid(udid_arg: str) -> str:
    """解析目标设备 UDID。

    :param udid_arg: 命令行传入的 udid；为空时自动选第一台在线安卓设备
    :return: UDID
    :raises RuntimeError: 指定 udid 不在配置中 / 无在线安卓设备时抛出
    """
    manager = PhoneManager(
        config_file=str(PROJECT_ROOT / "config" / "config.yaml")
    )
    if udid_arg:
        for device in manager._devices:  # noqa: SLF001 仅脚本内读取
            if device.udid == udid_arg:
                return device.udid
        raise RuntimeError(
            f"udid [{udid_arg}] 不在 config.yaml 配置中，"
            f"已配置：{[d.udid for d in manager._devices]}"  # noqa: SLF001
        )
    device = manager.connect_first_available("android")
    return device.udid


def main() -> int:
    """脚本入口：dump 当前页面并输出 JSON + 汇总。

    :return: 进程退出码（0 成功，1 失败）
    """
    parser = argparse.ArgumentParser(
        description="采集 Android 设备当前页面 UI 层级（走 BasePage.dump_hierarchy 门控）"
    )
    parser.add_argument("--reason", required=True,
                        help="抓取诉求（必填，透传给 dump_hierarchy 门控）")
    parser.add_argument("--udid", default="",
                        help="目标设备 UDID（缺省自动选第一台在线安卓设备）")
    parser.add_argument("--max-retries", type=int, default=10,
                        help="层级为空时最大重试次数（默认 10）")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="重试间隔秒（默认 2.0）")
    args = parser.parse_args()

    try:
        udid = _resolve_udid(args.udid)
        device = connect_device(f"android:///{udid}")
        poco = AndroidUiautomationPoco(
            device=device,
            use_airtest_input=True,
            screenshot_each_action=False,
        )
        page = BasePage(poco=poco, udid=udid, platform="android")

        activity = page.get_current_activity()
        logger.info(f"当前前台 Activity：{activity or '(未知)'}")

        raw = _dump_with_retry(page, args.reason, args.max_retries, args.interval)
        nodes = []
        _walk(_get_root(raw), 0, nodes)

        DUMP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        json_path = DUMP_DIR / f"dump_{stamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=1)

        summary_path = DUMP_DIR / f"dump_{stamp}_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("\n".join(_build_summary(nodes, activity)))

        logger.info(f"原始层级已保存：{json_path}")
        logger.info(f"关键信息汇总已保存：{summary_path}")
        return 0
    except Exception as exc:  # noqa: BLE001 CLI 工具统一兜底
        logger.error(f"dump 失败：{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
