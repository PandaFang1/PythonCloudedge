"""Android 平台页面包（CloudEdge）。

本包存放 CloudEdge 安卓端的页面类，定位器基于安卓 UI 结构维护。
与 pages/ios 包中的页面类实现相同业务接口，供 PageFactory 按平台分发。
"""

from pages.android.main_page import CloudEdgeMainPage
from pages.android.message_page import CloudEdgeMessagePage
from pages.android.my_page import CloudEdgeMyPage

__all__ = ["CloudEdgeMainPage", "CloudEdgeMessagePage", "CloudEdgeMyPage"]
