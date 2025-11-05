# MQTT 数据上传功能说明

## 功能概述

本项目已集成 MQTT 客户端功能，可以将传感器数据实时上传到云平台。主要特性包括：

- ✅ 支持 TLS/SSL 加密连接（可选择性使用 CA 证书）
- ✅ 自动重连机制，连接断开后自动尝试重连
- ✅ 命令控制，收到 `startUpload` 命令后才开始上传数据
- ✅ 完全兼容现有功能，不影响原有数据处理逻辑

## 配置说明

### 1. MQTT 配置文件

配置文件位置：`install/mqtt.json`

配置文件示例：

```json
{
    "broker": "mqtt.example.com",          // MQTT服务器地址
    "port": 8883,                          // MQTT服务器端口 (TLS通常使用8883, 非加密使用1883)
    "client_id": "gateway_client_001",     // 客户端ID (必须唯一)
    "username": "your_username",           // MQTT用户名
    "password": "your_password",           // MQTT密码
    "use_tls": true,                       // 是否使用TLS加密 (true/false)
    "ca_cert": "/path/to/ca.crt",         // CA证书路径 (use_tls=true时需要，或留空)
    "reconnect_interval": 5,               // 重连间隔(秒)
    "command_topic": "gateway/command",    // 命令接收topic
    "data_topic": "gateway/data",          // 数据发送topic
    "response_topic": "gateway/response"   // 命令响应topic
}
```

### 2. 配置参数详解

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| broker | MQTT服务器地址 | 是 | localhost |
| port | MQTT服务器端口 | 是 | 1883 |
| client_id | 客户端唯一标识 | 是 | gateway_client |
| username | MQTT用户名 | 否 | 空 |
| password | MQTT密码 | 否 | 空 |
| use_tls | 是否启用TLS加密 | 否 | false |
| ca_cert | CA证书文件路径 | 否 | 空 |
| reconnect_interval | 断线重连间隔(秒) | 否 | 5 |
| command_topic | 接收命令的topic | 是 | gateway/command |
| data_topic | 发送数据的topic | 是 | gateway/data |
| response_topic | 命令响应的topic | 是 | gateway/response |

### 3. TLS/SSL 配置

#### 使用自签名证书

如果使用自建 MQTT 服务器并配置了 TLS，需要：

1. 将 CA 证书文件（通常是 `ca.crt`）上传到网关设备
2. 在 `mqtt.json` 中设置：
   ```json
   {
       "use_tls": true,
       "ca_cert": "/path/to/ca.crt"
   }
   ```

#### 不验证证书（仅测试环境）

如果希望跳过证书验证（不推荐生产环境）：

```json
{
    "use_tls": true,
    "ca_cert": ""
}
```

## 使用流程

### 1. 启动系统

系统启动后，如果检测到 `mqtt.json` 配置文件，会自动：

1. 初始化 MQTT 客户端
2. 尝试连接到 MQTT 服务器
3. 订阅命令 topic (`gateway/command`)
4. 如果连接失败，每隔 5 秒自动重试

### 2. 开始数据上传

MQTT 客户端连接成功后，需要发送 `startUpload` 命令才会开始上传数据。

#### 命令格式

发送到 `gateway/command` topic：

```json
{
  "commandId": "cmd-start-upload-12345",
  "commandName": "startUpload",
  "timestamp": 1730491500000
}
```

#### 命令响应

网关会回复到 `gateway/response` topic：

```json
{
  "commandId": "cmd-start-upload-12345",
  "status": "success",
  "timestamp": 1730491501800
}
```

### 3. 数据格式

传感器数据会自动发送到 `gateway/data` topic，格式如下：

```json
{
  "deviceId": "01",
  "timestamp": 1730491502000,
  "payload": [
    {
      "name": "temperature",
      "value": 25.5,
      "unit": ""
    },
    {
      "name": "pressure",
      "value": 1.2,
      "unit": ""
    },
    {
      "name": "moisture",
      "value": 150.0,
      "unit": ""
    },
    {
      "name": "dewPoint",
      "value": -20.5,
      "unit": ""
    },
    {
      "name": "rawPressure",
      "value": 1.18,
      "unit": ""
    },
    {
      "name": "humidity",
      "value": 45.2,
      "unit": ""
    }
  ]
}
```

### 4. 停止数据上传

发送 `stopUpload` 命令可以停止数据上传：

```json
{
  "commandId": "cmd-stop-upload-67890",
  "commandName": "stopUpload",
  "timestamp": 1730491600000
}
```

## 日志查看

MQTT 相关日志会输出到系统日志文件中，可以查看：

- 连接状态
- 命令接收情况
- 数据发送状态
- 错误信息

日志示例：

```
MQTT配置加载成功: mqtt.json
MQTT客户端初始化完成: mqtt.example.com:8883
✓ MQTT连接成功: mqtt.example.com:8883
✓ MQTT已订阅命令topic: gateway/command
收到MQTT命令: {"commandId":"cmd-start-upload-12345","commandName":"startUpload","timestamp":1730491500000}
✓ 收到startUpload命令，开始上传数据
发送命令响应: {"commandId":"cmd-start-upload-12345","status":"success","timestamp":1730491501800}
✓ MQTT数据发送成功: Addr=01
```

## 故障排查

### 1. MQTT 客户端未启动

**现象**：日志中没有 MQTT 相关信息

**解决方法**：
- 检查 `install/mqtt.json` 文件是否存在
- 检查配置文件格式是否正确（JSON 格式）

### 2. 连接失败

**现象**：日志显示 "MQTT连接失败"

**解决方法**：
- 检查网络连接
- 确认 broker 地址和端口正确
- 检查用户名密码是否正确
- 如果使用 TLS，检查证书路径是否正确

### 3. 数据未上传

**现象**：连接成功但没有数据发送

**解决方法**：
- 确认是否已发送 `startUpload` 命令
- 检查串口数据是否正常接收
- 查看日志中是否有错误信息

## 依赖安装

本功能需要安装 `paho-mqtt` 库，已添加到 `requirements.txt` 中：

```bash
pip install paho-mqtt
```

或安装所有依赖：

```bash
pip install -r requirements.txt
```

## 注意事项

1. **安全性**：生产环境建议启用 TLS 加密
2. **证书管理**：妥善保管 CA 证书文件
3. **Client ID**：确保每个网关的 client_id 唯一
4. **性能影响**：MQTT 功能在后台独立线程运行，不影响原有数据采集性能
5. **兼容性**：如果不需要 MQTT 功能，删除或重命名 `mqtt.json` 即可禁用

## 技术支持

如有问题，请查看系统日志文件获取详细错误信息。
