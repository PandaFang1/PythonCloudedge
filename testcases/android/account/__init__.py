"""账号模块：登录 / 退出登录 / 账号切换 / 特定账号重登。

本子包聚合 CloudEdge 安卓端账号相关的端到端测试：

通用用例（覆盖抽象流程）：
- test_login.py：选国家 + 账号密码登录（默认 US 账号，pm clear 后从登录页开始）
- test_logout.py：我的信息页退出登录（弹窗取消 / 确定）
- test_switch.py：同一设备切换登录不同账号（US→CN，pm clear 后从登录页开始两次登录）

特定场景用例（覆盖具体设备/账号组合，硬编码参数）：
- test_login_cn_account.py：退出当前账号 → 登录中国账号（ceshi011@qq.com/56565099A）
- test_relogin_us_account.py：退出当前账号 → 重新登录美国账号
  （358632847@qq.com/82102353qweR）

依赖：
- 共享 conftest：testcases/android/conftest.py（环境清理、Activity 等待工具）
- 模块 conftest：account/conftest.py（登录态主页、我的 Tab、我的信息页 fixture
  + perform_account_switch 共用工具）
- Page Objects：login_page / main_page / my_page / account_page
"""
