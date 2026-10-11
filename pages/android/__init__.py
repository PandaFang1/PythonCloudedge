"""Android 平台页面包（CloudEdge）。

本包存放 CloudEdge 安卓端的页面类，定位器基于安卓 UI 结构维护。
与 pages/ios 包中的页面类实现相同业务接口，供 PageFactory 按平台分发。
"""

from pages.android.account_page import CloudEdgeAccountPage
from pages.android.add_device_category_page import CloudEdgeAddDeviceCategoryPage
from pages.android.jingle_add_page import JingleAddPage
from pages.android.jingle_bell_dnd_page import JingleBellDndPage
from pages.android.jingle_delete_page import JingleDeletePage
from pages.android.jingle_device_info_page import JingleDeviceInfoPage
from pages.android.jingle_device_location_page import JingleDeviceLocationPage
from pages.android.jingle_device_name_page import JingleDeviceNamePage
from pages.android.jingle_device_scene_page import JingleDeviceScenePage
from pages.android.jingle_device_share_page import JingleDeviceSharePage
from pages.android.jingle_device_version_page import JingleDeviceVersionPage
from pages.android.jingle_general_page import JingleGeneralPage
from pages.android.jingle_install_guide_page import JingleInstallGuidePage
from pages.android.jingle_ringtone_page import JingleRingtonePage
from pages.android.jingle_setting_page import JingleSettingPage
from pages.android.jingle_share_type_page import JingleShareTypePage
from pages.android.jingle_sleep_time_add_page import JingleSleepTimeAddPage
from pages.android.jingle_sound_page import JingleSoundPage
from pages.android.jingle_storage_page import JingleStoragePage
from pages.android.jingle_sub_page_base import JingleSubPageBase
from pages.android.jingle_unbind_channel_page import JingleUnbindChannelPage
from pages.android.login_page import CloudEdgeLoginPage
from pages.android.main_page import CloudEdgeMainPage
from pages.android.message_page import CloudEdgeMessagePage
from pages.android.my_page import CloudEdgeMyPage

__all__ = [
    "CloudEdgeAccountPage",
    "CloudEdgeAddDeviceCategoryPage",
    "JingleAddPage",
    "JingleBellDndPage",
    "JingleDeletePage",
    "JingleDeviceInfoPage",
    "JingleDeviceLocationPage",
    "JingleDeviceNamePage",
    "JingleDeviceScenePage",
    "JingleDeviceSharePage",
    "JingleDeviceVersionPage",
    "JingleGeneralPage",
    "JingleInstallGuidePage",
    "JingleRingtonePage",
    "JingleSettingPage",
    "JingleShareTypePage",
    "JingleSleepTimeAddPage",
    "JingleSoundPage",
    "JingleStoragePage",
    "JingleSubPageBase",
    "JingleUnbindChannelPage",
    "CloudEdgeLoginPage",
    "CloudEdgeMainPage",
    "CloudEdgeMessagePage",
    "CloudEdgeMyPage",
]
