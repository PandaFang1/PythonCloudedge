"""Jingle 删除模块：智能门铃 Chime Base 端到端删除。

本子包聚合 CloudEdge 安卓端智能门铃（Chime Base）删除相关的端到端测试：
- test_delete.py：通用删除（SN 默认取 `DEFAULT_DEVICE_SN` 环境变量）
- test_delete_doorbell_chime_131903239.py：特定场景删除（楼顶拷机 SN=131903239）

依赖：
- 共享 conftest：testcases/android/conftest.py（android_preserved_app + Activity 等待工具）
- 模块 conftest：jingle_delete/conftest.py（前置断言：主页设备列表含目标 SN）
- Page Objects：login_page / main_page / jingle_delete_page
- 添加设备流程（前置）：testcases/android/jingle_add/（删除前需先添加）
"""
