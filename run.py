"""测试运行入口。

用法：
    python run.py                          # 双端全跑
    python run.py --platform android       # 仅安卓端（CloudEdge）
    python run.py --platform ios           # 仅 iOS 端（云际）
    python run.py --report                 # 运行后生成并打开 allure 报告
    python run.py --collect-only           # 仅收集用例（不执行）

说明：
    底层调用 pytest，自定义参数原样透传；
    allure 结果输出至 allure-results/ 目录。
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# allure 结果目录与报告目录
ALLURE_RESULTS_DIR = PROJECT_ROOT / "allure-results"
ALLURE_REPORT_DIR = PROJECT_ROOT / "reports" / "allure-report"


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="poco+pytest+allure 测试运行入口")
    parser.add_argument(
        "--platform",
        default="all",
        choices=["android", "ios", "all"],
        help="运行平台：android / ios / all（默认 all）",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="运行结束后生成 allure 报告并尝试打开",
    )
    parser.add_argument(
        "--pytest-args",
        default="",
        help="透传给 pytest 的额外参数（如 '-k smoke -m regression'）",
    )
    return parser.parse_args()


def build_pytest_command(args: argparse.Namespace) -> list:
    """组装 pytest 命令。

    :param args: 命令行参数
    :return: pytest 命令参数列表
    """
    pytest_args = [
        sys.executable, "-m", "pytest",
        "--platform", args.platform,
    ]

    if args.pytest_args:
        pytest_args.extend(args.pytest_args.split())

    return pytest_args


def generate_allure_report() -> bool:
    """生成 allure html 报告。

    :return: 生成成功返回 True；allure 命令不可用时返回 False
    """
    result = subprocess.run(
        ["allure", "generate", str(ALLURE_RESULTS_DIR),
         "-o", str(ALLURE_REPORT_DIR), "--clean"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print(f"[警告] allure 报告生成失败：{result.stderr.strip()}\n"
              f"请确认已安装 allure 命令行工具（brew install allure）")
        return False

    print(f"[信息] allure 报告已生成：{ALLURE_REPORT_DIR}")
    return True


def main() -> int:
    """主入口：运行 pytest 并按需生成报告。

    :return: pytest 退出码
    """
    args = parse_args()
    print(f"[信息] 运行平台：{args.platform}")

    pytest_command = build_pytest_command(args)
    print(f"[信息] 执行命令：{' '.join(pytest_command)}")

    exit_code = subprocess.run(pytest_command, cwd=PROJECT_ROOT).returncode

    if args.report and exit_code in (0, 1):  # 用例失败也生成报告
        generate_allure_report()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
