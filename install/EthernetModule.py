import os
import json
import re
import socket
import threading
import time
import queue
from datetime import datetime
import tornado.web
from Util.log4p import log4p


class NetworkConnection:
    """网络连接类 - 处理TCP/UDP连接"""

    def __init__(self, config, data_callback=None):
        self.config = config
        self.socket = None
        self.thread = None
        self.is_connected = False
        self.is_connecting = False
        self.send_queue = queue.Queue()
        self.data_callback = data_callback  # 数据回调函数
        self.should_stop = False

        # ⚠️ 关键修复：增强回调函数验证
        connection_name = config.get('name', 'Unknown')
        log4p.logs(f"创建NetworkConnection: {connection_name}")
        log4p.logs(f"回调函数参数: {data_callback is not None}")
        log4p.logs(f"回调函数类型: {type(data_callback)}")

        if self.data_callback is None:
            log4p.logs(f"警告: 连接 {connection_name} 没有设置数据回调函数")
        else:
            log4p.logs(f"✓ 连接 {connection_name} 回调函数设置成功")
            # 测试回调函数是否可调用
            if callable(self.data_callback):
                log4p.logs(f"✓ 回调函数可调用")
            else:
                log4p.logs(f"✗ 回调函数不可调用: {type(self.data_callback)}")

    def connect(self):
        """建立连接"""
        if self.is_connected or self.is_connecting:
            return False, "连接已存在或正在连接中"

        try:
            self.is_connecting = True
            self.should_stop = False

            protocol = self.config['protocol'].upper()
            mode = self.config['mode'].capitalize()

            if protocol == 'TCP' and mode == 'Client':
                return self._connect_tcp_client()
            elif protocol == 'TCP' and mode == 'Server':
                return self._connect_tcp_server()
            elif protocol == 'UDP' and mode == 'Client':
                return self._connect_udp_client()
            elif protocol == 'UDP' and mode == 'Server':
                return self._connect_udp_server()
            else:
                return False, f"暂不支持 {protocol} {mode} 模式"

        except Exception as e:
            self.is_connecting = False
            log4p.logs(f"连接失败: {str(e)}")
            return False, f"连接失败: {str(e)}"

    def _connect_tcp_client(self):
        """TCP客户端连接"""
        try:
            # 创建TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10秒连接超时

            # 绑定本地IP（如果指定）
            if self.config['local_ip'] and self.config['local_ip'] != '0.0.0.0':
                try:
                    self.socket.bind((self.config['local_ip'], 0))  # 0表示系统分配端口
                    log4p.logs(f"绑定本地IP: {self.config['local_ip']}")
                except Exception as e:
                    log4p.logs(f"绑定本地IP失败: {str(e)}")

            # 连接到远程服务器
            remote_ip = self.config['remote_ip']
            remote_port = int(self.config['remote_port'])

            log4p.logs(f"正在连接到 {remote_ip}:{remote_port}")
            self.socket.connect((remote_ip, remote_port))

            # 连接成功
            self.is_connected = True
            self.is_connecting = False
            self.socket.settimeout(0.1)  # 设置较短的接收超时，避免阻塞

            # 启动接收线程
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

            log4p.logs(f"TCP客户端连接成功: {remote_ip}:{remote_port}")
            self._notify_callback("status", "connected", f"TCP连接已建立: {remote_ip}:{remote_port}")

            return True, "连接成功"

        except socket.timeout:
            self.is_connecting = False
            return False, "连接超时"
        except ConnectionRefusedError:
            self.is_connecting = False
            return False, "连接被拒绝，请检查目标地址和端口"
        except Exception as e:
            self.is_connecting = False
            return False, f"连接失败: {str(e)}"

    def _connect_tcp_server(self):
        """TCP服务器连接"""
        try:
            # 创建TCP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # 绑定本地地址
            local_ip = self.config['local_ip'] if self.config['local_ip'] else '0.0.0.0'
            local_port = int(self.config['local_port'])

            self.socket.bind((local_ip, local_port))
            self.socket.listen(5)  # 最多5个连接
            self.socket.settimeout(0.1)  # 设置accept超时

            # 连接成功
            self.is_connected = True
            self.is_connecting = False

            # 启动接收线程
            self.thread = threading.Thread(target=self._tcp_server_loop, daemon=True)
            self.thread.start()

            log4p.logs(f"TCP服务器启动成功: {local_ip}:{local_port}")
            self._notify_callback("status", "connected", f"TCP服务器已启动: {local_ip}:{local_port}")

            return True, "TCP服务器启动成功"

        except Exception as e:
            self.is_connecting = False
            return False, f"TCP服务器启动失败: {str(e)}"

    def _connect_udp_client(self):
        """UDP客户端连接"""
        try:
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # 绑定本地IP（如果指定）
            if self.config['local_ip'] and self.config['local_ip'] != '0.0.0.0':
                try:
                    self.socket.bind((self.config['local_ip'], 0))
                    log4p.logs(f"UDP客户端绑定本地IP: {self.config['local_ip']}")
                except Exception as e:
                    log4p.logs(f"绑定本地IP失败: {str(e)}")

            # 连接成功
            self.is_connected = True
            self.is_connecting = False
            self.socket.settimeout(0.1)

            # 启动接收线程
            self.thread = threading.Thread(target=self._udp_receive_loop, daemon=True)
            self.thread.start()

            log4p.logs(f"UDP客户端已就绪")
            self._notify_callback("status", "connected", f"UDP客户端已就绪")

            return True, "UDP客户端就绪"

        except Exception as e:
            self.is_connecting = False
            return False, f"UDP客户端启动失败: {str(e)}"

    def _connect_udp_server(self):
        """UDP服务器连接"""
        try:
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # 绑定本地地址
            local_ip = self.config['local_ip'] if self.config['local_ip'] else '0.0.0.0'
            local_port = int(self.config['local_port'])

            self.socket.bind((local_ip, local_port))
            self.socket.settimeout(0.1)

            # 连接成功
            self.is_connected = True
            self.is_connecting = False

            # 启动接收线程
            self.thread = threading.Thread(target=self._udp_receive_loop, daemon=True)
            self.thread.start()

            log4p.logs(f"UDP服务器启动成功: {local_ip}:{local_port}")
            self._notify_callback("status", "connected", f"UDP服务器已启动: {local_ip}:{local_port}")

            return True, "UDP服务器启动成功"

        except Exception as e:
            self.is_connecting = False
            return False, f"UDP服务器启动失败: {str(e)}"

    def disconnect(self):
        """断开连接"""
        try:
            self.should_stop = True
            self.is_connected = False

            if self.socket:
                self.socket.close()
                self.socket = None

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)

            log4p.logs(f"连接已断开: {self.config['name']}")
            self._notify_callback("status", "disconnected", "连接已断开")

            return True, "断开成功"

        except Exception as e:
            log4p.logs(f"断开连接时出错: {str(e)}")
            return False, f"断开失败: {str(e)}"

    def send_data(self, data):
        """发送数据"""
        if not self.is_connected or not self.socket:
            return False, "连接未建立"

        try:
            # 数据格式转换
            if self.config['data_format'].upper() == 'HEX':
                # 十六进制格式：移除空格并转换为字节
                hex_data = data.replace(' ', '').replace('\n', '').replace('\r', '')
                if len(hex_data) % 2 != 0:
                    return False, "十六进制数据长度必须为偶数"
                send_bytes = bytes.fromhex(hex_data)
            else:
                # ASCII格式：直接编码为UTF-8字节
                send_bytes = data.encode('utf-8')

            # 根据协议发送数据
            protocol = self.config['protocol'].upper()
            mode = self.config['mode'].capitalize()

            if protocol == 'TCP':
                if hasattr(self, 'client_socket') and self.client_socket:
                    # TCP服务器模式，向客户端发送
                    self.client_socket.send(send_bytes)
                else:
                    # TCP客户端模式
                    self.socket.send(send_bytes)
            elif protocol == 'UDP':
                if mode == 'Client':
                    # UDP客户端：发送到指定的远程地址
                    remote_ip = self.config['remote_ip']
                    remote_port = int(self.config['remote_port'])
                    self.socket.sendto(send_bytes, (remote_ip, remote_port))
                else:
                    # UDP服务器：发送到最后通信的客户端
                    if hasattr(self, 'last_client_addr') and self.last_client_addr:
                        self.socket.sendto(send_bytes, self.last_client_addr)
                    else:
                        return False, "没有可发送的目标地址"

            # 记录发送的数据
            log4p.logs(f"发送数据到 {self.config['name']}: {data}")

            # 立即通过回调推送发送的数据到前端
            self._notify_callback("send", data, f"发送: {data}")

            return True, "发送成功"

        except Exception as e:
            log4p.logs(f"发送数据失败: {str(e)}")
            self._notify_callback("error", str(e), f"发送失败: {str(e)}")
            return False, f"发送失败: {str(e)}"

    def _tcp_server_loop(self):
        """TCP服务器循环，处理客户端连接"""
        log4p.logs(f"TCP服务器开始监听: {self.config['name']}")

        while not self.should_stop and self.is_connected:
            try:
                # 接受客户端连接
                client_socket, client_addr = self.socket.accept()
                log4p.logs(f"客户端连接: {client_addr}")
                self._notify_callback("status", "client_connected", f"客户端已连接: {client_addr}")

                # 保存客户端socket用于发送数据
                self.client_socket = client_socket
                self.client_socket.settimeout(0.1)

                # 启动客户端数据接收循环
                client_thread = threading.Thread(
                    target=self._tcp_client_receive_loop,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if not self.should_stop:
                    log4p.logs(f"TCP服务器错误: {str(e)}")
                    self._notify_callback("error", str(e), f"服务器错误: {str(e)}")
                break

        log4p.logs(f"TCP服务器循环结束: {self.config['name']}")

    def _tcp_client_receive_loop(self, client_socket, client_addr):
        """TCP服务器端处理单个客户端的接收循环"""
        log4p.logs(f"开始接收客户端数据: {client_addr}")

        while not self.should_stop and self.is_connected:
            try:
                # 接收数据
                data = client_socket.recv(1024)

                if not data:
                    # 客户端断开连接
                    log4p.logs(f"客户端断开连接: {client_addr}")
                    self._notify_callback("status", "client_disconnected", f"客户端已断开: {client_addr}")
                    break

                # 处理接收到的数据
                self._process_received_data(data)

            except socket.timeout:
                continue
            except Exception as e:
                if not self.should_stop:
                    log4p.logs(f"接收客户端数据错误: {str(e)}")
                    self._notify_callback("error", str(e), f"接收错误: {str(e)}")
                break

        # 清理客户端连接
        try:
            client_socket.close()
        except:
            pass

        if hasattr(self, 'client_socket') and self.client_socket == client_socket:
            self.client_socket = None

    def _receive_loop(self):
        """TCP客户端接收数据循环"""
        log4p.logs(f"开始接收数据循环: {self.config['name']}")

        while not self.should_stop and self.is_connected:
            try:
                if not self.socket:
                    break

                # 接收数据
                data = self.socket.recv(1024)

                if not data:
                    # 连接被对端关闭
                    log4p.logs(f"对端关闭连接: {self.config['name']}")
                    self._notify_callback("status", "disconnected", "对端关闭连接")
                    break

                # 处理接收到的数据
                self._process_received_data(data)

            except socket.timeout:
                # 接收超时，继续循环
                continue
            except Exception as e:
                if not self.should_stop:
                    log4p.logs(f"接收数据时出错: {str(e)}")
                    self._notify_callback("error", str(e), f"接收错误: {str(e)}")
                break

        # 清理连接状态
        self.is_connected = False
        log4p.logs(f"接收数据循环结束: {self.config['name']}")

    def _udp_receive_loop(self):
        """UDP接收数据循环"""
        log4p.logs(f"开始UDP接收数据循环: {self.config['name']}")

        while not self.should_stop and self.is_connected:
            try:
                if not self.socket:
                    break

                # 接收数据和地址
                data, addr = self.socket.recvfrom(1024)

                # 记录发送方地址（用于UDP服务器回复）
                self.last_client_addr = addr

                log4p.logs(f"UDP接收数据来自 {addr}: {len(data)} bytes")

                # 处理接收到的数据
                self._process_received_data(data)

            except socket.timeout:
                continue
            except Exception as e:
                if not self.should_stop:
                    log4p.logs(f"UDP接收数据时出错: {str(e)}")
                    self._notify_callback("error", str(e), f"UDP接收错误: {str(e)}")
                break

        log4p.logs(f"UDP接收数据循环结束: {self.config['name']}")

    def _process_received_data(self, data):
        """处理接收到的数据"""
        try:
            # 数据格式转换
            if self.config['data_format'].upper() == 'HEX':
                # 转换为十六进制字符串
                hex_data = ' '.join(f'{b:02X}' for b in data)
                display_data = hex_data
            else:
                # 尝试解码为UTF-8字符串
                try:
                    display_data = data.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果解码失败，显示为十六进制
                    display_data = ' '.join(f'{b:02X}' for b in data)

            # 记录接收的数据
            log4p.logs(f"接收数据从 {self.config['name']}: {display_data}")

            # 立即通过回调推送接收的数据到前端
            self._notify_callback("receive", display_data, f"接收: {display_data}")

        except Exception as e:
            log4p.logs(f"处理接收数据时出错: {str(e)}")
            self._notify_callback("error", str(e), f"数据处理错误: {str(e)}")

    def _notify_callback(self, data_type, data, message):
        """通知回调函数"""
        log4p.logs(f"准备推送数据: {self.config['name']} - {data_type} - {message}")

        if self.data_callback:
            try:
                self.data_callback(self.config['name'], data_type, data, message)
                log4p.logs(f"数据推送成功: {self.config['name']} - {data_type}")
            except Exception as e:
                log4p.logs(f"回调函数执行失败: {str(e)}")
        else:
            log4p.logs(f"警告: 没有设置回调函数，无法推送数据")

    def get_status(self):
        """获取连接状态"""
        if self.is_connecting:
            return "connecting"
        elif self.is_connected:
            return "connected"
        else:
            return "disconnected"


class EthernetModule:
    """以太网调试模块 - 负责TCP/UDP连接配置管理"""

    CONFIG_FILE = "ethernet.json"
    active_connections = {}  # 存储活动连接: {name: NetworkConnection}
    data_callback = None  # 全局数据回调函数

    @staticmethod
    def set_data_callback(callback):
        """设置数据回调函数"""
        EthernetModule.data_callback = callback
        log4p.logs("以太网模块数据回调已设置")

    @staticmethod
    def init_config_file():
        """初始化以太网配置文件"""
        default_config = [
            {
                "name": "TCP客户端测试",
                "protocol": "TCP",
                "mode": "Client",
                "local_ip": "192.168.1.230",
                "local_port": "8001",
                "remote_ip": "192.168.1.100",
                "remote_port": "8000",
                "auto_connect": "1",
                "data_format": "HEX"
            },
            {
                "name": "TCP服务器测试",
                "protocol": "TCP",
                "mode": "Server",
                "local_ip": "192.168.1.230",
                "local_port": "9000",
                "remote_ip": "",
                "remote_port": "",
                "auto_connect": "0",
                "data_format": "ASCII"
            },
            {
                "name": "UDP服务器测试",
                "protocol": "UDP",
                "mode": "Server",
                "local_ip": "192.168.1.230",
                "local_port": "9001",
                "remote_ip": "",
                "remote_port": "",
                "auto_connect": "0",
                "data_format": "ASCII"
            }
        ]

        if not os.path.exists(EthernetModule.CONFIG_FILE):
            try:
                with open(EthernetModule.CONFIG_FILE, 'w', encoding='utf-8') as file:
                    json.dump(default_config, file, indent=4, ensure_ascii=False)
                log4p.logs(f"File '{EthernetModule.CONFIG_FILE}' created with default values.")
            except Exception as e:
                log4p.logs(f"创建{EthernetModule.CONFIG_FILE}失败: {str(e)}")
        else:
            try:
                with open(EthernetModule.CONFIG_FILE, 'r', encoding='utf-8') as file:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        log4p.logs(f"{EthernetModule.CONFIG_FILE}格式错误，重新初始化")
                        with open(EthernetModule.CONFIG_FILE, 'w', encoding='utf-8') as file:
                            json.dump(default_config, file, indent=4, ensure_ascii=False)
                    else:
                        log4p.logs(f"File '{EthernetModule.CONFIG_FILE}' exists with {len(existing_data)} connections.")
            except (json.JSONDecodeError, Exception) as e:
                log4p.logs(f"读取{EthernetModule.CONFIG_FILE}失败，重新创建: {str(e)}")
                with open(EthernetModule.CONFIG_FILE, 'w', encoding='utf-8') as file:
                    json.dump(default_config, file, indent=4, ensure_ascii=False)

    @staticmethod
    def load_config():
        """加载以太网配置"""
        try:
            with open(EthernetModule.CONFIG_FILE, "r", encoding='utf-8') as f:
                config_data = json.load(f)
            log4p.logs(f"读取以太网配置成功，共{len(config_data)}个连接")
            return config_data
        except FileNotFoundError:
            log4p.logs(f"{EthernetModule.CONFIG_FILE}不存在，返回空配置")
            return []
        except json.JSONDecodeError:
            log4p.logs(f"{EthernetModule.CONFIG_FILE}格式错误，返回空配置")
            return []
        except Exception as e:
            log4p.logs(f"读取配置文件时发生错误: {str(e)}")
            return []

    @staticmethod
    def save_config(config_data):
        """保存以太网配置"""
        try:
            with open(EthernetModule.CONFIG_FILE, 'w', encoding='utf-8') as json_file:
                json.dump(config_data, json_file, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            log4p.logs(f"保存配置文件失败: {str(e)}")
            return False

    @staticmethod
    def validate_ip(ip_address):
        """验证IP地址格式"""
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, ip_address):
            return False

        # 验证每个数字段是否在0-255范围内
        parts = ip_address.split('.')
        for part in parts:
            if not (0 <= int(part) <= 255):
                return False
        return True

    @staticmethod
    def validate_port(port):
        """验证端口号"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False

    @staticmethod
    def validate_connection_data(data):
        """验证连接配置数据"""
        errors = []

        # 验证必填字段
        if not data.get('name', '').strip():
            errors.append("连接名称不能为空")

        if not data.get('local_ip', '').strip():
            errors.append("本地IP不能为空")
        elif not EthernetModule.validate_ip(data['local_ip']):
            errors.append("本地IP地址格式无效")

        if not data.get('local_port', '').strip():
            errors.append("本地端口不能为空")
        elif not EthernetModule.validate_port(data['local_port']):
            errors.append("本地端口必须在1-65535范围内")

        # 根据协议和模式验证远程配置
        protocol = data.get('protocol', '').upper()
        mode = data.get('mode', '').capitalize()

        if mode == 'Client':
            if not data.get('remote_ip', '').strip():
                errors.append("客户端模式必须指定远程IP")
            elif not EthernetModule.validate_ip(data['remote_ip']):
                errors.append("远程IP地址格式无效")

            if not data.get('remote_port', '').strip():
                errors.append("客户端模式必须指定远程端口")
            elif not EthernetModule.validate_port(data['remote_port']):
                errors.append("远程端口必须在1-65535范围内")

        return errors

    @staticmethod
    def add_connection(connection_data):
        """添加新连接配置"""
        try:
            # 加载现有配置
            config_data = EthernetModule.load_config()

            # 检查名称是否重复
            for existing in config_data:
                if existing.get('name') == connection_data['name']:
                    return False, f"连接名称'{connection_data['name']}'已存在"

            # 验证数据
            errors = EthernetModule.validate_connection_data(connection_data)
            if errors:
                return False, "; ".join(errors)

            # 添加新配置
            config_data.append(connection_data)

            # 保存配置
            if EthernetModule.save_config(config_data):
                log4p.logs(f"以太网配置添加成功: {connection_data['name']}")
                return True, "配置添加成功"
            else:
                return False, "保存配置文件失败"

        except Exception as e:
            log4p.logs(f"添加以太网配置时发生错误: {str(e)}")
            return False, f"服务器错误: {str(e)}"

    @staticmethod
    def delete_connection(connection_name):
        """删除连接配置"""
        try:
            # 先断开连接（如果存在）
            EthernetModule.disconnect_network(connection_name)

            # 加载现有配置
            config_data = EthernetModule.load_config()

            # 查找并删除指定配置
            original_length = len(config_data)
            config_data = [item for item in config_data if item.get('name') != connection_name]

            if len(config_data) == original_length:
                return False, f"未找到名称为'{connection_name}'的配置"

            # 保存配置
            if EthernetModule.save_config(config_data):
                log4p.logs(f"删除以太网配置成功: {connection_name}")
                return True, "配置删除成功"
            else:
                return False, "保存配置文件失败"

        except Exception as e:
            log4p.logs(f"删除以太网配置时发生错误: {str(e)}")
            return False, f"服务器错误: {str(e)}"

    @staticmethod
    def edit_connection(connection_name, updated_data):
        """编辑连接配置"""
        try:
            # 先断开连接（如果存在）
            EthernetModule.disconnect_network(connection_name)

            # 加载现有配置
            config_data = EthernetModule.load_config()

            # 验证数据
            errors = EthernetModule.validate_connection_data(updated_data)
            if errors:
                return False, "; ".join(errors)

            # 查找并更新指定配置
            found = False
            for i, item in enumerate(config_data):
                if item.get('name') == connection_name:
                    config_data[i] = updated_data
                    found = True
                    break

            if not found:
                return False, f"未找到名称为'{connection_name}'的配置"

            # 保存配置
            if EthernetModule.save_config(config_data):
                log4p.logs(f"编辑以太网配置成功: {connection_name}")
                return True, "配置更新成功"
            else:
                return False, "保存配置文件失败"

        except Exception as e:
            log4p.logs(f"编辑以太网配置时发生错误: {str(e)}")
            return False, f"服务器错误: {str(e)}"

    @staticmethod
    def connect_network(connection_name):
        """建立网络连接"""
        try:
            # 检查是否已连接
            if connection_name in EthernetModule.active_connections:
                conn = EthernetModule.active_connections[connection_name]
                if conn.is_connected:
                    return False, "连接已存在"
                if conn.is_connecting:
                    return False, "正在连接中"

            # 获取配置
            configs = EthernetModule.load_config()
            config = None
            for cfg in configs:
                if cfg['name'] == connection_name:
                    config = cfg
                    break

            if not config:
                return False, "未找到连接配置"

            # ⚠️ 关键修复：确保回调函数正确传递
            log4p.logs(f"创建网络连接，回调函数状态: {EthernetModule.data_callback is not None}")

            if EthernetModule.data_callback is None:
                log4p.logs("错误: 以太网模块的回调函数未设置!")
                return False, "回调函数未设置，无法创建连接"

            # 创建连接对象，确保传递回调函数
            connection = NetworkConnection(config, EthernetModule.data_callback)

            # 验证连接对象的回调函数
            if connection.data_callback is None:
                log4p.logs("错误: NetworkConnection 的回调函数为空!")
                return False, "连接对象回调函数设置失败"
            else:
                log4p.logs("✓ NetworkConnection 回调函数设置成功")

            EthernetModule.active_connections[connection_name] = connection

            # 建立连接
            success, message = connection.connect()

            if not success:
                # 连接失败，清理
                del EthernetModule.active_connections[connection_name]

            return success, message

        except Exception as e:
            log4p.logs(f"建立网络连接时发生错误: {str(e)}")
            import traceback
            log4p.logs(f"详细错误信息: {traceback.format_exc()}")
            return False, f"连接错误: {str(e)}"

    @staticmethod
    def disconnect_network(connection_name):
        """断开网络连接"""
        try:
            if connection_name not in EthernetModule.active_connections:
                return False, "连接不存在"

            connection = EthernetModule.active_connections[connection_name]
            success, message = connection.disconnect()

            # 清理连接对象
            del EthernetModule.active_connections[connection_name]

            return success, message

        except Exception as e:
            log4p.logs(f"断开网络连接时发生错误: {str(e)}")
            return False, f"断开错误: {str(e)}"

    @staticmethod
    def send_network_data(connection_name, data):
        """发送网络数据"""
        try:
            if connection_name not in EthernetModule.active_connections:
                return False, "连接不存在"

            connection = EthernetModule.active_connections[connection_name]
            return connection.send_data(data)

        except Exception as e:
            log4p.logs(f"发送网络数据时发生错误: {str(e)}")
            return False, f"发送错误: {str(e)}"

    @staticmethod
    def get_connection_status(connection_name):
        """获取连接状态"""
        if connection_name in EthernetModule.active_connections:
            return EthernetModule.active_connections[connection_name].get_status()
        return "disconnected"

    @staticmethod
    def get_all_connection_status():
        """获取所有连接状态"""
        status = {}
        for name, connection in EthernetModule.active_connections.items():
            status[name] = connection.get_status()
        return status


class EthernetHandler(tornado.web.RequestHandler):
    """以太网调试页面处理器"""

    def get(self):
        config_data = EthernetModule.load_config()
        self.render("ethernet.html", data=config_data)


class SubmitEthernetHandler(tornado.web.RequestHandler):
    """以太网配置提交处理器"""

    def post(self):
        try:
            data = json.loads(self.request.body)
            operation_type = data.get('type')

            log4p.logs(f"以太网配置操作: {operation_type}")

            if operation_type == 'add':
                self._handle_add(data)
            elif operation_type == 'del':
                self._handle_delete(data)
            elif operation_type == 'edit':
                self._handle_edit(data)
            elif operation_type == 'connect':
                self._handle_connect(data)
            elif operation_type == 'disconnect':
                self._handle_disconnect(data)
            elif operation_type == 'send':
                self._handle_send(data)
            elif operation_type == 'status':
                self._handle_status(data)
            else:
                log4p.logs(f"未知的操作类型: {operation_type}")
                self.set_status(400)
                self.write({"error": f"未知的操作类型: {operation_type}"})

        except json.JSONDecodeError:
            log4p.logs("JSON解析错误")
            self.set_status(400)
            self.write({"error": "请求数据格式错误"})
        except Exception as e:
            log4p.logs(f"处理以太网配置请求时发生错误: {str(e)}")
            self.set_status(500)
            self.write({"error": f"服务器错误: {str(e)}"})

    def _handle_add(self, data):
        """处理添加操作"""
        info = data.get('data', [])

        if len(info) < 9:
            self.set_status(400)
            self.write({"error": "数据不完整"})
            return

        # 构建连接数据
        connection_data = {
            "name": str(info[0]).strip(),
            "protocol": str(info[1]).upper(),
            "mode": str(info[2]).capitalize(),
            "local_ip": str(info[3]).strip(),
            "local_port": str(info[4]).strip(),
            "remote_ip": str(info[5]).strip() if info[5] else "",
            "remote_port": str(info[6]).strip() if info[6] else "",
            "auto_connect": str(info[7]),
            "data_format": str(info[8]).upper()
        }

        success, message = EthernetModule.add_connection(connection_data)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(400)
            self.write({"error": message})

    def _handle_delete(self, data):
        """处理删除操作"""
        info = data.get('data', [])

        if len(info) < 1:
            self.set_status(400)
            self.write({"error": "删除数据不完整"})
            return

        connection_name = str(info[0]).strip()
        success, message = EthernetModule.delete_connection(connection_name)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(404 if "未找到" in message else 400)
            self.write({"error": message})

    def _handle_edit(self, data):
        """处理编辑操作"""
        info = data.get('data', [])

        if len(info) < 9:
            self.set_status(400)
            self.write({"error": "编辑数据不完整"})
            return

        connection_name = str(info[0]).strip()

        # 构建更新数据
        updated_data = {
            "name": connection_name,
            "protocol": str(info[1]).upper(),
            "mode": str(info[2]).capitalize(),
            "local_ip": str(info[3]).strip(),
            "local_port": str(info[4]).strip(),
            "remote_ip": str(info[5]).strip() if info[5] else "",
            "remote_port": str(info[6]).strip() if info[6] else "",
            "auto_connect": str(info[7]),
            "data_format": str(info[8]).upper()
        }

        success, message = EthernetModule.edit_connection(connection_name, updated_data)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(404 if "未找到" in message else 400)
            self.write({"error": message})

    def _handle_connect(self, data):
        """处理连接操作"""
        connection_name = data.get('name', '')
        if not connection_name:
            self.set_status(400)
            self.write({"error": "连接名称不能为空"})
            return

        success, message = EthernetModule.connect_network(connection_name)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(400)
            self.write({"error": message})

    def _handle_disconnect(self, data):
        """处理断开操作"""
        connection_name = data.get('name', '')
        if not connection_name:
            self.set_status(400)
            self.write({"error": "连接名称不能为空"})
            return

        success, message = EthernetModule.disconnect_network(connection_name)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(400)
            self.write({"error": message})

    def _handle_send(self, data):
        """处理发送数据操作"""
        connection_name = data.get('name', '')
        send_data = data.get('data', '')

        if not connection_name:
            self.set_status(400)
            self.write({"error": "连接名称不能为空"})
            return

        if not send_data:
            self.set_status(400)
            self.write({"error": "发送数据不能为空"})
            return

        success, message = EthernetModule.send_network_data(connection_name, send_data)

        if success:
            self.write({"success": True, "message": message})
        else:
            self.set_status(400)
            self.write({"error": message})

    def _handle_status(self, data):
        """处理状态查询操作"""
        connection_name = data.get('name', '')

        if connection_name:
            status = EthernetModule.get_connection_status(connection_name)
            self.write({"status": status})
        else:
            status = EthernetModule.get_all_connection_status()
            self.write({"status": status})