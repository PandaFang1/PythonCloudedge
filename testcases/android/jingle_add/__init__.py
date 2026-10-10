"""Jingle 添加模块：智能门铃 Chime Base 完整配网 + 快捷配网 + 特定场景。

本子包聚合 CloudEdge 安卓端智能门铃（Chime Base）添加相关的端到端测试：
- test_full.py：通用完整配网（SN/WiFi 默认取环境变量 `CLOUDEDGE_*`）
- test_quick.py：通用快捷配网（蓝牙区域点 SN → 直达 WiFi 输入）
- test_add_doorbell_chime_131903227.py：特定场景完整配网（楼顶拷机 SN=131903227
  + WiFi=xiaoMI-楼顶拷机IPC/56565099，硬编码）

依赖：
- 共享 conftest：testcases/android/conftest.py（Activity 等待工具）
- 模块 conftest：jingle_add/conftest.py（保留登录态 + 已进入选择设备类别页 fixture）
- Page Objects：login_page / main_page / add_device_category_page / jingle_add_page
- 添加设备流程：pages/android/add_device_flow/（DoorbellChimeBaseFlow）
- 测试基础设施：testcases/android/test_add_device.py（按类别 / 蓝牙两种添加方式）
"""
