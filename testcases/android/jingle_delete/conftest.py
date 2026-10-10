"""Jingle 删除模块 conftest：依赖共享的 android_preserved_app + 前置 SN 检查 fixture。

依赖关系（fixture 链）：
    android_preserved_app（testcases/android/conftest.py）
        ↓
    jingle_main_with_target（本文件）：登录态主页 + 断言设备列表含目标 SN

设计原则：
- 本文件只定义 jingle_delete 模块特有 fixture
- 跨模块共享的「保持登录态」逻辑从 testcases.android.conftest 复用
- 禁止反向依赖：不依赖 account / jingle_add 任何 fixture
"""

from __future__ import annotations

from typing import Iterator, Tuple

import pytest

from pages.page_factory import PageFactory


@pytest.fixture
def jingle_main_with_target(android_preserved_app, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """登录态主页 + 前置断言「主页设备列表含目标 SN」。

    用法：
        def test_delete(android_preserved_app, sn=...):
            ...

    注：本 fixture 不接收 sn 参数（避免 fixture 参数化复杂化），
    实际 SN 断言在用例内通过 main_page.get_device_list() 完成。
    若需要更严格的「fixture 即断言」，可在本文件内扩展 fixture 工厂。

    yield (login_page, main_page, jingle_delete_page) 给用例使用。
    """
    login_page, main_page = android_preserved_app
    jingle_delete_page = PageFactory.create(
        platform, "jingle_delete_page",
        poco=poco_driver, udid=device_info.udid,
    )

    yield login_page, main_page, jingle_delete_page
