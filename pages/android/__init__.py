"""Android 平台页面包（CloudEdge）。

本包存放 CloudEdge 安卓端的页面类，定位器基于安卓 UI 结构维护。
与 pages/ios 包中的页面类实现相同业务接口，供 PageFactory 按平台分发。
"""

from pages.android.account_page import CloudEdgeAccountPage
from pages.android.add_device_category_page import CloudEdgeAddDeviceCategoryPage
from pages.android.login_page import CloudEdgeLoginPage
from pages.android.main_page import CloudEdgeMainPage
from pages.android.message_page import CloudEdgeMessagePage
from pages.android.my_page import CloudEdgeMyPage

__all__ = [
    "CloudEdgeAccountPage",
    "CloudEdgeAddDeviceCategoryPage",
    "CloudEdgeLoginPage",
    "CloudEdgeMainPage",
    "CloudEdgeMessagePage",
    "CloudEdgeMyPage",
]
