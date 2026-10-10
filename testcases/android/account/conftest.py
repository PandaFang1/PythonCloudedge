"""账号模块 conftest：登录态主页 → 我的 Tab → 我的信息页 系列 fixture +
账号切换 / 重登共用工具（perform_account_switch）。

依赖关系（fixture 链）：
    android_logged_in（testcases/android/conftest.py）
        ↓
    android_my_page（本文件）：登录态主页 → 我的 Tab
        ↓
    android_account_page（本文件）：我的 Tab → 点击账号入口 → 我的信息页

设计原则：
- 本文件只定义账号模块特有 fixture
- 跨模块共享 fixture（android_logged_in 等）由 testcases/android/conftest.py 提供
- 禁止反向依赖：本文件不依赖 jingle_add / jingle_delete 任何 fixture

共用工具（普通函数，不作为 fixture）：
- perform_account_switch(...)：保留登录态 → 若已登录则退出 → 登录到指定账号
  用于 test_login_cn_account / test_relogin_us_account 等"重新登录"类用例
"""

from __future__ import annotations

import time
from typing import Iterator, Tuple

import allure
import pytest

from pages.android.account_page import CloudEdgeAccountPage
from pages.android.my_page import CloudEdgeMyPage
from pages.page_factory import PageFactory
from testcases.android.conftest import (
    LOGIN_ACTIVITY_KEYWORD,
    MAIN_ACTIVITY_KEYWORD,
    MY_INFO_ACTIVITY_KEYWORD,
    wait_for_activity,
    wait_for_main_activity,
)


@pytest.fixture
def android_my_page(android_logged_in, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """登录态主页 → 切到「我的」Tab → 等待稳定。

    yield (login_page, main_page, my_page) 给用例使用。
    """
    login_page, main_page = android_logged_in
    my_page = CloudEdgeMyPage(poco=poco_driver, udid=device_info.udid)

    with allure.step("切到「我的」页并等待稳定"):
        time.sleep(2.0)  # 登录后主页渲染稳定再切换
        main_page.open_my_page()
        assert my_page.wait_for_page_loaded(timeout=15), \
            "[android] 未进入「我的」页"

    yield login_page, main_page, my_page


@pytest.fixture
def android_account_page(android_my_page, platform, poco_driver, device_info) \
        -> Iterator[Tuple]:
    """我的 Tab → 点击账号入口 → 「我的信息」页（带重试）。

    登录后立即点击账号入口偶发不生效，故带 3 次重试。

    yield (login_page, main_page, my_page, account_page) 给用例使用。
    """
    login_page, main_page, my_page = android_my_page
    account_page = PageFactory.create(
        platform, "account_page", poco=poco_driver, udid=device_info.udid
    )

    with allure.step("点击账号入口 tv_account → 进入「我的信息」页"):
        jumped = False
        for attempt in range(1, 4):
            my_page.open_account_page()
            if wait_for_activity(login_page, MY_INFO_ACTIVITY_KEYWORD, timeout=8):
                jumped = True
                break
        assert jumped, (
            "[android] 点击账号入口 tv_account 3 次后仍未跳转"
            "「我的信息」页（当前 Activity="
            f"{login_page.get_current_activity().strip()}）"
        )
        assert account_page.wait_for_page_loaded(timeout=15), \
            "[android] 未进入「我的信息」页"

    yield login_page, main_page, my_page, account_page


# ==================== 共用工具函数（非 fixture）====================

def perform_account_switch(
    login_page, main_page, my_page, account_page,
    target_region: str, target_account: str, target_password: str,
) -> None:
    """账号切换 / 重登共用工具：若当前已登录则退出，再登录到指定账号。

    适用场景：
        - 「登录到指定账号」类用例（保留当前登录态 → 退出 → 登录）
        - 「重新登录」类用例（同上流程）

    流程：
        1. 检测当前 Activity
        2. 若已登录（MainActivity）：我的 → 我的信息 → 退出登录 → 回到登录页
        3. 登录到 target_region/账户/密码
        4. 断言进入 MainActivity

    :param login_page: CloudEdgeLoginPage 实例
    :param main_page: CloudEdgeMainPage 实例
    :param my_page: CloudEdgeMyPage 实例
    :param account_page: CloudEdgeAccountPage 实例
    :param target_region: 目标国家/地区（如 "中国"）
    :param target_account: 目标账号
    :param target_password: 目标密码
    """
    current = login_page.get_current_activity().strip()

    # 1. 若已登录则先退出
    if LOGIN_ACTIVITY_KEYWORD not in current:
        assert MAIN_ACTIVITY_KEYWORD in current, (
            f"前置：应处于登录态主页或登录页（当前 Activity={current}）"
        )
        with allure.step("退出当前账号：我的 → 我的信息 → 退出登录"):
            time.sleep(2.0)  # 等待主页渲染稳定
            main_page.open_my_page()
            assert my_page.wait_for_page_loaded(timeout=15), \
                "[android] 未进入「我的」页"

            jumped = False
            for attempt in range(1, 4):
                my_page.open_account_page()
                if wait_for_activity(login_page, MY_INFO_ACTIVITY_KEYWORD, timeout=8):
                    jumped = True
                    break
            assert jumped, (
                "[android] 3 次尝试后仍未进入「我的信息」页"
                f"（当前 Activity={login_page.get_current_activity().strip()}）"
            )

            assert account_page.wait_for_page_loaded(timeout=15), \
                "[android] 「我的信息」页识别点未出现"
            account_page.logout(confirm=True)
            assert login_page.wait_for_page_loaded(timeout=20), \
                "[android] 退出后未回到登录页"

    # 2. 登录到目标账号
    with allure.step(f"登录 {target_region} 账号 {target_account}"):
        login_page.login_with_region(
            region_text=target_region,
            account=target_account,
            password=target_password,
            remember_password=True,
        )
        assert wait_for_main_activity(login_page, timeout=60), (
            f"[android] 登录 {target_account} 后未进入 MainActivity"
            f"（当前={login_page.get_current_activity().strip()}）"
        )
