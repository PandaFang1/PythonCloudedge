# 配置说明

设备、app 信息与串口配置统一在 `config/config.yaml` 中维护。

## 1. 设备与 app 配置（devices）

```yaml
devices:
  - user_name: "肥猪阿熊"                 # 用户名（connect 按此查找设备）
    phone_model: "Redmi Note 11 5G"      # 机型（仅备注）
    platform: Android                     # 平台：Android / iOS
    udid: "TC55LJMR59W8ZPRK"             # 设备 UDID（安卓真机序列号 / iOS UDID）
    app_package: "com.cloudedge.smarteye"  # 被测 app 包名或 Bundle ID

  - user_name: "阿熊"
    platform: iOS
    udid: "00008110-000130AA1A05401E"
    app_package: "com.meari.smartcamera"
    wda_port: 8100                        # iOS 专用：WebDriverAgent 端口（默认 8100）
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `user_name` | 是 | 设备别名，`PhoneManager.connect()` 按此连接 |
| `platform` | 是 | `Android` / `iOS`（忽略大小写） |
| `udid` | 是 | 安卓真机为序列号，模拟器为 `127.0.0.1:端口`，iOS 为 UDID |
| `app_package` | 是 | 安卓包名 / iOS Bundle ID |
| `wda_port` | iOS 多设备必填 | WDA 端口，多台 iOS 需手动分配不同端口 |

## 2. 串口配置（serial_ports）

框架集成 **pyserial**，支持通过串口「控制硬件/设备」与「采集串口日志」两类场景，作为 UI 自动化的可选并行能力。

在 `config/config.yaml` 中新增 `serial_ports` 节点：

```yaml
serial_ports:
  - name: "camera_console"              # 唯一标识（fixture 按此名称获取）
    port: "/dev/cu.usbserial-1140"      # 串口设备路径（Windows 如 COM3）
    baudrate: 115200                    # 波特率，默认 115200
    timeout: 1                          # 读写超时（秒），默认 1
    purpose: control                    # control（控制）/ log（日志采集）
    device: "肥猪阿熊"                   # 可选：关联设备 user_name

  - name: "camera_log"
    port: "/dev/cu.usbserial-1141"
    baudrate: 115200
    timeout: 1
    purpose: log
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 串口唯一标识，用例通过 `parametrize` 引用 |
| `port` | 是 | 串口设备路径 |
| `baudrate` | 否 | 波特率，默认 `115200` |
| `timeout` | 否 | 读写超时（秒），默认 `1` |
| `purpose` | 否 | `control` / `log`，默认 `log` |
| `device` | 否 | 关联设备的 `user_name`（仅备注） |

---

## 文档导航

- 上一篇：[环境准备 ←](./installation.md)
- 下一篇：[快速开始 →](./quickstart.md)

[返回文档中心](../README.md) · [返回项目首页](../../README.md)
