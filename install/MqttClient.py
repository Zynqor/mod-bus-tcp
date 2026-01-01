"""
MqttClient.py - 线程安全的 MQTT 上报客户端

功能：
1. 心跳包定期发送
2. 数据上报（采集即上报，跟随回调频率）
3. 命令监听与响应
4. 上报开关控制
"""

import json
import time
import threading
from typing import Optional, Dict, Any, List, Callable

import paho.mqtt.client as mqtt

from Util.log4p import log4p


class MqttClient:
    """
    线程安全的 MQTT 客户端
    
    使用方式：
        # 在 Main.py 中初始化
        mqtt_client = MqttClient("mqtt_config.json")
        mqtt_client.start()
        
        # 在 Serial.py 中调用（采集即上报）
        mqtt_client.publish_data([
            {"name": "temperature", "value": 22.5, "unit": "°C"},
            {"name": "humidity", "value": 65.2, "unit": "%"}
        ])
    """
    
    def __init__(self, config_path: str = "mqtt_config.json"):
        """
        初始化 MQTT 客户端
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        # 提取配置项
        self.broker = self.config["broker"]
        self.device = self.config["device"]
        self.topics = self.config["topics"]
        self.intervals = self.config["intervals"]
        
        # 运行状态
        self._running = False
        self._connected = False
        self._lock = threading.Lock()  # 用于线程安全的数据发布
        
        # 心跳间隔（可通过命令动态调整）
        self._heartbeat_interval = self.intervals["heartbeat_seconds"]
        
        # 上报开关（默认开启）
        self._data_upload_enabled = True
        self._upload_lock = threading.Lock()
        
        # 命令处理器注册表
        self._command_handlers: Dict[str, Callable] = {
            "setHeartbeatintervalSeconds": self._handle_set_heartbeat_interval,
            "enableDataUpload": self._handle_enable_data_upload,
            "disableDataUpload": self._handle_disable_data_upload,
            "getStatus": self._handle_get_status,
            "rebootDevice": self._handle_reboot_device,
        }
        
        # 创建 MQTT 客户端
        self._client = mqtt.Client(client_id=self.broker["client_id"])
        self._setup_callbacks()
        
        # 心跳线程
        self._heartbeat_thread: Optional[threading.Thread] = None
        
        log4p.logs(f"[MQTT] 客户端初始化完成, DeviceId: {self.device['deviceId']}")
    
    def _setup_callbacks(self):
        """设置 MQTT 回调函数"""
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self._connected = True
            log4p.logs(f"[MQTT] 连接成功: {self.broker['host']}:{self.broker['port']}")
            
            # 订阅命令主题
            cmd_topic = self.topics["command_request"]
            client.subscribe(cmd_topic)
            log4p.logs(f"[MQTT] 已订阅命令主题: {cmd_topic}")
        else:
            log4p.logs(f"[MQTT] 连接失败, 错误码: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self._connected = False
        if rc != 0:
            log4p.logs(f"[MQTT] 意外断开连接, 错误码: {rc}, 将尝试重连...")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode("utf-8"))
            log4p.logs(f"[MQTT] 收到消息 [{topic}]: {payload}")
            
            # 处理命令请求
            if topic == self.topics["command_request"]:
                self._handle_command(payload)
                
        except json.JSONDecodeError as e:
            log4p.logs(f"[MQTT] 消息解析失败: {e}")
        except Exception as e:
            log4p.logs(f"[MQTT] 消息处理异常: {e}")
    
    def _handle_command(self, command: Dict):
        """
        处理命令请求
        
        Args:
            command: 命令请求字典
        """
        command_id = command.get("commandId", "unknown")
        command_name = command.get("commandName", "")
        params = command.get("params", {})
        
        log4p.logs(f"[MQTT] 处理命令: {command_name}, ID: {command_id}")
        
        # 查找并执行命令处理器
        handler = self._command_handlers.get(command_name)
        
        if handler:
            try:
                result = handler(params)
                self._send_command_response(command_id, "success", result=result)
            except Exception as e:
                self._send_command_response(command_id, "error", error_message=str(e))
        else:
            self._send_command_response(
                command_id, 
                "error", 
                error_message=f"Unknown command: {command_name}"
            )
    
    def _send_command_response(
        self, 
        command_id: str, 
        status: str, 
        error_message: str = None, 
        result: Dict = None
    ):
        """
        发送命令响应
        
        Args:
            command_id: 命令ID
            status: 执行状态 ("success" 或 "error")
            error_message: 错误信息（可选）
            result: 返回结果（可选）
        """
        response = {
            "commandId": command_id,
            "status": status,
            "timestamp": int(time.time() * 1000)
        }
        
        if error_message:
            response["errorMessage"] = error_message
        if result:
            response["result"] = result
        
        topic = self.topics["command_response"]
        self._publish(topic, response)
        log4p.logs(f"[MQTT] 命令响应已发送: {status}")
    
    # ==================== 命令处理器 ====================
    
    def _handle_set_heartbeat_interval(self, params: Dict) -> Dict:
        """设置心跳间隔"""
        interval = params.get("intervalSeconds") or params.get("interval")
        if interval is None:
            raise ValueError("Missing 'intervalSeconds' parameter")
        
        # 支持字符串或数字
        try:
            interval = int(float(str(interval)))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid interval value: {interval}")
        
        if interval < 5 or interval > 3600:
            raise ValueError("Interval must be between 5 and 3600 seconds")
        
        self._heartbeat_interval = interval
        log4p.logs(f"[MQTT] 心跳间隔已更新为: {self._heartbeat_interval} 秒")
        return {"newIntervalSeconds": self._heartbeat_interval}
    
    def _handle_enable_data_upload(self, params: Dict) -> Dict:
        """开启数据上报"""
        with self._upload_lock:
            self._data_upload_enabled = True
        log4p.logs(f"[MQTT] 数据上报已开启")
        return {"uploadEnabled": True}
    
    def _handle_disable_data_upload(self, params: Dict) -> Dict:
        """关闭数据上报"""
        with self._upload_lock:
            self._data_upload_enabled = False
        log4p.logs(f"[MQTT] 数据上报已关闭")
        return {"uploadEnabled": False}
    
    def _handle_reboot_device(self, params: Dict) -> Dict:
        """重启设备（这里仅作示例，实际需要根据硬件实现）"""
        log4p.logs("[MQTT] 收到重启命令，设备将在 5 秒后重启...")
        # 这里可以调用实际的重启逻辑
        # os.system("reboot") 或其他方式
        return {"message": "Device will reboot in 5 seconds"}
    
    def _handle_get_status(self, params: Dict) -> Dict:
        """获取设备状态"""
        with self._upload_lock:
            upload_enabled = self._data_upload_enabled
        return {
            "connected": self._connected,
            "heartbeatInterval": self._heartbeat_interval,
            "uploadEnabled": upload_enabled
        }
    
    # ==================== 核心功能 ====================
    
    def _publish(self, topic: str, payload: Dict) -> bool:
        """
        线程安全的消息发布
        
        Args:
            topic: 主题
            payload: 消息内容
            
        Returns:
            是否发送成功
        """
        if not self._connected:
            log4p.logs(f"[MQTT] 未连接，消息丢弃: {topic}")
            return False
        
        with self._lock:
            try:
                message = json.dumps(payload, ensure_ascii=False)
                result = self._client.publish(topic, message, qos=1)
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            except Exception as e:
                log4p.logs(f"[MQTT] 发布失败: {e}")
                return False
    
    def _send_heartbeat(self):
        """发送心跳包"""
        heartbeat = {
            "deviceId": self.device["deviceId"],
            "dataTopic": self.topics["data"],
            "deviceName": self.device["deviceName"],
            "deviceType": self.device["deviceType"],
            "timestamp": int(time.time() * 1000)
        }
        
        topic = self.topics["heartbeat"]
        if self._publish(topic, heartbeat):
            log4p.logs(f"[MQTT] 心跳发送成功")
        else:
            log4p.logs(f"[MQTT] 心跳发送失败")
    
    def _heartbeat_loop(self):
        """心跳发送循环"""
        log4p.logs(f"[MQTT] 心跳线程启动, 间隔: {self._heartbeat_interval} 秒")
        
        while self._running:
            if self._connected:
                self._send_heartbeat()
            
            # 使用短间隔循环检查，以便能够响应间隔变化
            elapsed = 0
            while elapsed < self._heartbeat_interval and self._running:
                time.sleep(1)
                elapsed += 1
    
    # ==================== 公开接口 ====================
    
    def start(self):
        """启动 MQTT 客户端"""
        if self._running:
            log4p.logs("[MQTT] 客户端已在运行")
            return
        
        self._running = True
        
        # 设置认证（如果配置了用户名密码）
        if self.broker.get("username"):
            self._client.username_pw_set(
                self.broker["username"], 
                self.broker.get("password", "")
            )
        
        # 连接 Broker
        try:
            self._client.connect(
                self.broker["host"],
                self.broker["port"],
                self.broker["keepalive"]
            )
        except Exception as e:
            log4p.logs(f"[MQTT] 连接失败: {e}")
            self._running = False
            raise
        
        # 启动网络循环（后台线程）
        self._client.loop_start()
        
        # 等待连接建立
        timeout = 10
        while not self._connected and timeout > 0:
            time.sleep(0.5)
            timeout -= 0.5
        
        if not self._connected:
            log4p.logs("[MQTT] 连接超时")
            self.stop()
            raise ConnectionError("MQTT connection timeout")
        
        # 启动心跳线程
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, 
            name="MQTT-Heartbeat",
            daemon=True
        )
        self._heartbeat_thread.start()
        
        log4p.logs("[MQTT] 客户端启动完成")
    
    def stop(self):
        """停止 MQTT 客户端"""
        log4p.logs("[MQTT] 正在停止客户端...")
        self._running = False
        
        # 停止网络循环
        self._client.loop_stop()
        self._client.disconnect()
        
        # 等待线程结束
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=5)
        
        log4p.logs("[MQTT] 客户端已停止")
    
    def publish_data(self, data_points: List[Dict]) -> bool:
        """
        发布数据（采集即上报，供 Serial 线程调用）
        
        此方法是线程安全的，调用后立即发送（如果上报已开启）。
        
        Args:
            data_points: 数据点列表，每个数据点格式为:
                {
                    "name": "temperature",
                    "value": 22.5,
                    "unit": "°C"
                }
        
        Returns:
            是否发送成功（上报关闭时返回 False）
        
        示例:
            mqtt_client.publish_data([
                {"name": "A_Total_Current", "value": 0.123, "unit": "mA"},
                {"name": "A_Resistive_Current", "value": 0.112, "unit": "mA"}
            ])
        """
        if not data_points:
            return False
        
        # 检查上报开关
        with self._upload_lock:
            if not self._data_upload_enabled:
                return False
        
        # 构造消息并立即发送
        payload = {
            "deviceId": self.device["deviceId"],
            "timestamp": int(time.time() * 1000),
            "payload": data_points
        }
        
        topic = self.topics["data"]
        success = self._publish(topic, payload)
        
        if success:
            log4p.logs(f"[MQTT] 数据上报成功, 数据点数: {len(data_points)}")
        
        return success
    
    def set_upload_enabled(self, enabled: bool):
        """
        设置上报开关
        
        Args:
            enabled: True 开启上报, False 关闭上报
        """
        with self._upload_lock:
            self._data_upload_enabled = enabled
        log4p.logs(f"[MQTT] 数据上报已{'开启' if enabled else '关闭'}")
    
    def register_command_handler(self, command_name: str, handler: Callable):
        """
        注册自定义命令处理器
        
        Args:
            command_name: 命令名称
            handler: 处理函数，签名为 (params: Dict) -> Dict
        """
        self._command_handlers[command_name] = handler
        log4p.logs(f"[MQTT] 注册命令处理器: {command_name}")
    
    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    @property
    def heartbeat_interval(self) -> int:
        """获取当前心跳间隔"""
        return self._heartbeat_interval
    
    @property
    def is_upload_enabled(self) -> bool:
        """检查上报是否开启"""
        with self._upload_lock:
            return self._data_upload_enabled
