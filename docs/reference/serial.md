# 串口测试

框架集成 **pyserial**，支持通过串口「控制硬件/设备」与「采集串口日志」两类场景，作为 UI 自动化的可选并行能力。

## 1. 配置串口

串口配置统一在 `config/config.yaml` 的 `serial_ports` 节点，详见
[配置说明](../getting-started/configuration.md#2-串口配置serial_ports)。

## 2. fixture

| fixture | 作用域 | 说明 |
|---|---|---|
| `serial_manager` | session | 串口管理器，统一建立/关闭所有串口连接 |
| `serial_port` | function | 按 `serial_name` 参数获取串口连接 |
| `serial_control_port` | function | 按 `purpose=control` 选取控制串口 |
| `serial_log_port` | function | 按 `purpose=log` 选取日志采集串口 |

核心能力（封装于 `utils/serial_utils.py`）：
- `send(data, newline=True)`：发送命令
- `wait_for_keyword(keyword, timeout=10)`：阻塞等待关键字，返回命中行
- `extract_info(pattern, group=1, timeout=10)`：正则提取关键信息
- `list_ports()`：枚举可用串口

## 3. 编写串口用例

```python
import allure
import pytest

@pytest.mark.serial
@allure.epic("串口")
@allure.feature("串口控制")
@pytest.mark.parametrize("serial_name", ["camera_console"])
def test_send_and_wait(serial_name, serial_port):
    serial_port.send("version")
    line = serial_port.wait_for_keyword("version", timeout=10)
    assert line
```

## 4. 运行

```bash
pytest -m serial                       # 仅串口用例
python run.py --pytest-args "-m serial"  # 通过 run.py 运行串口用例
```

> **说明**：未配置串口（`serial_ports` 为空或缺省）或串口连接失败时，
> 串口用例会 `pytest.skip`，**不影响 UI 用例**。

---

## 文档导航

- 上一篇：[页面识别文档 ←](./page-identification.md)
- 下一篇：[代码规范 →](../rules/coding.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
