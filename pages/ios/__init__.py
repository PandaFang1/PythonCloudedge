"""iOS 平台页面包（云际）。

本包存放云际 iOS 端的页面类，定位器基于 iOS UI 结构维护。
与 pages/android 包中的页面类实现相同业务接口，供 PageFactory 按平台分发。
"""

from pages.ios.main_page import YunjiMainPage

__all__ = ["YunjiMainPage"]
