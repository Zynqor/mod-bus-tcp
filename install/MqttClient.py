import json
import time
import threading
import ssl
from datetime import datetime
import paho.mqtt.client as mqtt

from Util.log4p import log4p


class MqttClient(threading.Thread):
    """MQTT客户端，用于连接云平台并上传数据"""

    def __init__(self, config_file='mqtt.json'):
        super().__init__()
        self.daemon = True
        self.running = True
        self.connected = False
        self.upload_enabled = False  # 是否允许上传数据（收到startUpload命令后才允许）

        # 加载配置
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                log4p.logs(f"MQTT配置加载成功: {config_file}")
        except Exception as e:
            log4p.logs(f"MQTT配置加载失败: {e}")
            self.config = {}
            self.running = False
            return

        # 提取配置参数
        self.broker = self.config.get('broker', 'localhost')
        self.port = self.config.get('port', 1883)
        self.client_id = self.config.get('client_id', 'gateway_client')
        self.username = self.config.get('username', '')
        self.password = self.config.get('password', '')
        self.use_tls = self.config.get('use_tls', False)
        self.ca_cert = self.config.get('ca_cert', '')
        self.reconnect_interval = self.config.get('reconnect_interval', 5)

        # Topic配置
        self.command_topic = self.config.get('command_topic', 'gateway/command')
        self.data_topic = self.config.get('data_topic', 'gateway/data')
        self.response_topic = self.config.get('response_topic', 'gateway/response')

        # 创建MQTT客户端
        self.client = mqtt.Client(client_id=self.client_id)

        # 设置回调函数
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # 设置用户名和密码
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # 设置TLS
        if self.use_tls:
            try:
                if self.ca_cert:
                    self.client.tls_set(ca_certs=self.ca_cert, cert_reqs=ssl.CERT_REQUIRED)
                else:
                    self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(False)
                log4p.logs("MQTT TLS配置成功")
            except Exception as e:
                log4p.logs(f"MQTT TLS配置失败: {e}")

        log4p.logs(f"MQTT客户端初始化完成: {self.broker}:{self.port}")

    def on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self.connected = True
            log4p.logs(f"✓ MQTT连接成功: {self.broker}:{self.port}")

            # 订阅命令topic
            self.client.subscribe(self.command_topic)
            log4p.logs(f"✓ MQTT已订阅命令topic: {self.command_topic}")
        else:
            self.connected = False
            log4p.logs(f"✗ MQTT连接失败, 返回码: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """连接断开回调"""
        self.connected = False
        self.upload_enabled = False  # 断开连接时禁用上传
        if rc != 0:
            log4p.logs(f"✗ MQTT意外断开连接, 返回码: {rc}")
        else:
            log4p.logs("MQTT连接已断开")

    def on_message(self, client, userdata, msg):
        """接收消息回调"""
        try:
            payload = msg.payload.decode('utf-8')
            log4p.logs(f"收到MQTT命令: {payload}")

            # 解析命令
            cmd = json.loads(payload)
            command_id = cmd.get('commandId', '')
            command_name = cmd.get('commandName', '')

            # 处理startUpload命令
            if command_name == 'startUpload':
                self.upload_enabled = True
                log4p.logs(f"✓ 收到startUpload命令，开始上传数据")

                # 发送响应
                response = {
                    "commandId": command_id,
                    "status": "success",
                    "timestamp": int(time.time() * 1000)
                }
                self.publish_response(response)
            elif command_name == 'stopUpload':
                self.upload_enabled = False
                log4p.logs(f"✓ 收到stopUpload命令，停止上传数据")

                # 发送响应
                response = {
                    "commandId": command_id,
                    "status": "success",
                    "timestamp": int(time.time() * 1000)
                }
                self.publish_response(response)
            else:
                log4p.logs(f"未知命令: {command_name}")

        except Exception as e:
            log4p.logs(f"处理MQTT消息失败: {e}")

    def publish_response(self, response):
        """发送命令响应"""
        try:
            if self.connected:
                payload = json.dumps(response, ensure_ascii=False)
                self.client.publish(self.response_topic, payload, qos=1)
                log4p.logs(f"发送命令响应: {payload}")
            else:
                log4p.logs("MQTT未连接，无法发送响应")
        except Exception as e:
            log4p.logs(f"发送命令响应失败: {e}")

    def publish_data(self, addr, temp, pressure, weishui, ludian, raw_press, humid):
        """发送传感器数据"""
        if not self.connected:
            # log4p.logs("MQTT未连接，跳过数据发送")
            return

        if not self.upload_enabled:
            # log4p.logs("未收到startUpload命令，跳过数据发送")
            return

        try:
            # 构建数据格式
            data = {
                "deviceId": addr,
                "timestamp": int(time.time() * 1000),
                "data": {
                    "temperature": {
                        "value": round(temp, 2),
                        "unit": ""
                    },
                    "pressure": {
                        "value": round(pressure, 2),
                        "unit": ""
                    },
                    "moisture": {
                        "value": round(weishui, 2),
                        "unit": ""
                    },
                    "dewPoint": {
                        "value": round(ludian, 2),
                        "unit": ""
                    },
                    "rawPressure": {
                        "value": round(raw_press, 2),
                        "unit": ""
                    },
                    "humidity": {
                        "value": round(humid, 2),
                        "unit": ""
                    }
                }
            }

            # 发送数据
            payload = json.dumps(data, ensure_ascii=False)
            result = self.client.publish(self.data_topic, payload, qos=1)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log4p.logs(f"✓ MQTT数据发送成功: Addr={addr}")
            else:
                log4p.logs(f"✗ MQTT数据发送失败: {result.rc}")

        except Exception as e:
            log4p.logs(f"发送MQTT数据异常: {e}")

    def connect_mqtt(self):
        """连接MQTT服务器"""
        try:
            log4p.logs(f"正在连接MQTT服务器: {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            return True
        except Exception as e:
            log4p.logs(f"MQTT连接失败: {e}")
            return False

    def run(self):
        """线程运行函数"""
        log4p.logs("MQTT客户端线程启动")

        # 首次连接
        if not self.connect_mqtt():
            log4p.logs(f"MQTT初始连接失败，{self.reconnect_interval}秒后重试...")

        # 启动网络循环
        self.client.loop_start()

        # 重连循环
        while self.running:
            if not self.connected:
                log4p.logs(f"MQTT未连接，{self.reconnect_interval}秒后尝试重连...")
                time.sleep(self.reconnect_interval)

                try:
                    self.connect_mqtt()
                except Exception as e:
                    log4p.logs(f"MQTT重连异常: {e}")
            else:
                time.sleep(1)

        # 清理
        self.client.loop_stop()
        self.client.disconnect()
        log4p.logs("MQTT客户端线程结束")

    def stop(self):
        """停止客户端"""
        self.running = False
        self.connected = False
        log4p.logs("正在停止MQTT客户端...")
