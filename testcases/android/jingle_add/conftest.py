"""Jingle 添加模块 conftest：依赖共享的 android_preserved_app + 模块内导航 fixture。

依赖关系（fixture 链）：
    android_preserved_app（testcases/android/conftest.py）
        ↓
    jingle_category_page（本文件）：登录态主页 → 「选择设备类别」页

设计原则：
- 本文件只定义 jingle_add 模块特有 fixture
- 跨模块共享的「保持登录态」逻辑从 testcases.android.conftest 复用
  （jingle_delete 同样需要，避免重复实现）
- 禁止反向依赖：不依赖 account / jingle_delete 任何 fixture
"""

from __future__ import annotations

import time
from typing import Iterator, Tuple

import allure
import pytest

from pages.page_factory import PageFactory
from testcases.android.conftest import (
    ADD_DEVICE_ACTIVITY_KEYWORD,
    wait_for_activity,
)


@pytest.fixture
def jingle_category_page(android_preserved_app, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """登录态主页 → 「选择设备类别」页。

    yield (login_page, main_page, add_device_page, jingle_add_page) 给用例使用。
    """
    login_page, main_page = android_preserved_app
    add_device_page = PageFactory.create(
        platform, "add_device_category_page",
        poco=poco_driver, udid=device_info.udid,
    )
    jingle_add_page = PageFactory.create(
        platform, "jingle_add_page",
        poco=poco_driver, udid=device_info.udid,
    )

    with allure.step("主页 → 添加设备 → 进入「选择设备类别」页"):
        # 登录后等待主页稳定（设备列表/引导浮层渲染），避免过早点击
        time.sleep(3.0)
        # 登录后可能出现新手引导浮层，需逐页点击「下一步」直至消失
        main_page.handle_guide()
        time.sleep(2.0)
        main_page.open_add_device_category_page()
        jumped = False
        for _ in range(3):
            if wait_for_activity(login_page, ADD_DEVICE_ACTIVITY_KEYWORD, timeout=8):
                jumped = True
                break
            main_page.open_add_device_category_page()  # 重试
        assert jumped, (
            f"[android] 3 次尝试后仍未进入「选择设备类别」页（Activity="
            f"{login_page.get_current_activity().strip()}）"
        )
        assert add_device_page.wait_for_page_loaded(timeout=15), \
            "[android] 进入「选择设备类别」页后识别点未出现"

    yield login_page, main_page, add_device_page, jingle_add_page
