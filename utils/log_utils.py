"""日志工具模块。

功能：
1. 日志同时输出到控制台和文件
2. 文件按天命名、按大小自动分割（TimedRotatingFileHandler 风格）
3. 日志统一保存在项目的 operater_logs 文件夹中
4. 每行日志包含时间（精确到毫秒）、文件名、方法名、级别、信息
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 创建日志存储文件夹（基于项目根目录的绝对路径）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = os.path.join(PROJECT_ROOT, "logs", "operater_logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式：时间 - 文件名|方法名 - logger名 - 级别 - 信息
FORMATTER = logging.Formatter(
    "%(asctime)s - %(filename)s|%(funcName)s - %(name)s - %(levelname)s - %(message)s"
)

# 单个日志文件上限：200MB，最多保留 5 个备份（总量上限 1GB）
MAX_BYTES = 200 * 1024 * 1024
BACKUP_COUNT = 5

LOGGER_NAME = "po_project"


def _build_file_path() -> str:
    """按当天日期生成日志文件路径。"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"{current_date}.log")


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """获取全局单例 logger。

    重复调用不会重复添加 handler，避免日志重复输出。

    :param name: logger 名称，默认 "po_project"
    :return: logging.Logger 实例
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # 控制台处理器：INFO 及以上
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(FORMATTER)
    logger.addHandler(console_handler)

    # 文件处理器：DEBUG 及以上，按大小分割，超限自动轮转
    try:
        file_handler = RotatingFileHandler(
            _build_file_path(),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FORMATTER)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as exc:
        logger.warning(f"日志文件创建失败，仅使用控制台输出：{exc}")

    return logger
