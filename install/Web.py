import os
import threading
from datetime import datetime
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import httpserver, ioloop
import json
import subprocess
from collections import deque

from Util.log4p import log4p

# 全局变量，用于存储所有WebSocket客户端连接
websocket_clients = set()
# 使用双端队列存储最近的日志，限制最大长度
log_queue = deque(maxlen=100)


def get_current_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"log_{today}.txt"


class LogsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("logs.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket连接已建立")
        # 将新客户端添加到客户端集合中
        websocket_clients.add(self)

        # 如果有历史日志，立即发送给新连接的客户端
        if log_queue:
            self.write_message(json.dumps(list(log_queue)))

    def on_message(self, message):
        # 本例中客户端不需要发送消息给服务器
        pass

    def on_close(self):
        print("WebSocket连接已关闭")
        # 从客户端集合中移除断开连接的客户端
        websocket_clients.remove(self)


# 用于检查日志文件更新并广播给所有WebSocket客户端的函数
# 替换原有的check_log_updates函数
def check_log_updates():
    try:
        # 获取当前日期的日志文件
        current_log_file = get_current_log_file()

        # 检查日志文件是否存在
        if not os.path.exists(current_log_file):
            print(f"日志文件不存在: {current_log_file}")
            return

        # 获取文件大小来检测变化，比修改时间更可靠
        current_size = os.path.getsize(current_log_file)

        # 如果文件大小未变化，则返回
        if hasattr(check_log_updates, 'last_size') and current_size == check_log_updates.last_size:
            return

        # 更新大小记录
        check_log_updates.last_size = current_size

        # 读取日志文件
        with open(current_log_file, 'r') as f:
            try:
                # 读取最后100行
                logs = deque(f, maxlen=100)

                # 更新日志队列
                new_logs = []
                for log in logs:
                    if log not in log_queue:
                        log_queue.append(log)
                        new_logs.append(log)

                # 只广播新的日志内容给所有连接的客户端
                if websocket_clients and new_logs:
                    for client in websocket_clients:
                        client.write_message(json.dumps(new_logs))
            except Exception as e:
                print(f"处理日志文件时出错: {e}")

    except Exception as e:
        print(f"检查日志更新时出错: {e}")


# 初始化上次修改时间
check_log_updates.last_mtime = 0


# 将此函数添加到Tornado的周期性回调中
def setup_periodic_log_check():
    tornado.ioloop.PeriodicCallback(
        check_log_updates,
        1000  # 每1000毫秒(1秒)检查一次
    ).start()


def append_to_json(file_path, new_data):
    """
    追加写入JSON文件，并根据需要覆盖重复项或新增不存在的项。

    Args:
    - file_path: JSON文件路径
    - new_data: 要追加写入的新数据，字典格式

    Returns:
    无
    """
    # 读取现有JSON文件内容或初始化为空字典
    try:
        with open(file_path, 'r') as json_file:
            existing_data = json.load(json_file)
    except FileNotFoundError:
        existing_data = {}

    # 合并数据
    for key, value in new_data.items():
        existing_data[key] = value

    # 写入JSON文件
    with open(file_path, 'w') as json_file:
        json.dump(existing_data, json_file, indent=4)

    log4p.logs("数据已追加写入JSON文件:", file_path)


class MainHandler(tornado.web.RequestHandler):
    process = None

    def get(self):
        # 读取本地配置文件
        with open("config.json", "r") as f:
            config_data = json.load(f)
        self.render("index.html", data=config_data)

    @staticmethod
    def run_script():
        if MainHandler.process != None:
            # 检查是否有正在运行的进程，如果没有或已结束，则启动新的Python脚本
            log4p.logs("已有一个脚本在运行")
            return
        # 启动新的Python脚本
        MainHandler.process = subprocess.Popen(['python', 'Main.py'])
        log4p.logs("已启动脚本")

    @staticmethod
    def restart_script():

        if MainHandler.process is not None:
            MainHandler.process.terminate()
            # 启动新的Python脚本
            MainHandler.process = subprocess.Popen(['python', 'Main.py'])
        else:
            log4p.logs("没有找到正在运行的进程，无法重启。")


class RefreshHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        if data['type'] == 'slave':
            # 读取本地配置文件
            with open("slave.json", "r") as f:
                config_data = json.load(f)
        if data['type'] == 'serial':
            # 读取本地配置文件
            with open("serial.json", "r") as f:
                config_data = json.load(f)
                for item in config_data:
                    if "\\\"" in item['save_rule']:
                        item['save_rule'] = item['save_rule'].replace("\\\"", "\"")
            log4p.logs(config_data)
        if data['type'] == 'master':
            # 读取本地配置文件
            with open("master.json", "r") as f:
                config_data = json.load(f)

        info = {"data": config_data}
        self.write(info)


class IpHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("config.json", "r") as f:
            config_data = json.load(f)
        self.render("ip.html", data=config_data)


class SlaveHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("slave.json", "r") as f:
            config_data = json.load(f)
        # to be continue
        self.render("slave.html", data=config_data)


class SerialHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("serial.json", "r") as f:
            config_data = json.load(f)
        self.render("serial.html", data=config_data)


class MasterHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("master.json", "r") as f:
            config_data = json.load(f)
        self.render("master.html", data=config_data)


class RestartHandler(tornado.web.RequestHandler):
    def get(self):
        log4p.logs("重启服务")
        MainHandler.restart_script()
        self.render("index.html", data=config_data)


class RestartHandler1(tornado.web.RequestHandler):
    def get(self):
        log4p.logs("重启机器")
        subprocess.run(['/data/restart.sh'])
        self.render("index.html", data=config_data)


class SubmitSlaveHandler(tornado.web.RequestHandler):
    def add(self, datas):
        info = datas['data']
        # 读取本地配置文件
        with open("slave.json", "r") as f:
            config_data = json.load(f)
        data = {
            "ip": info[0],
            "port": info[1],
            "id": info[2],
            "reg": info[3],
            "reg_len": info[4],
            "reg_addr": info[5],
            "save_start": info[6],
            "save_rule": str(info[7]),
            "freq": info[8]
        }
        config_data.append(data)
        log4p.logs("写入成功,", config_data)
        # 写入JSON文件
        with open("slave.json", 'w') as json_file:
            json.dump(config_data, json_file, indent=4)

    def delete(self, datas):
        info = datas['data']
        # 读取本地配置文件
        with open("slave.json", "r") as f:
            config_data = json.load(f)
        res = []
        for i in range(0, len(config_data)):
            tmp = config_data[i]
            if str(tmp['ip']) == str(info[0]) and str(tmp['port']) == str(info[1]) and str(tmp['id']) == str(info[2]):
                log4p.logs("删除成功")
            else:
                res.append(config_data[i])
        if len(res) == 0:
            res = config_data
        # 写入JSON文件
        with open("slave.json", 'w') as json_file:
            json.dump(res, json_file, indent=4)

    def edit(self, datas):
        info = datas['data']

        # 读取本地配置文件
        with open("slave.json", "r") as f:
            config_data = json.load(f)
        data = {
            "ip": info[0],
            "port": info[1],
            "id": info[2],
            "reg": info[3],
            "reg_len": info[4],
            "reg_addr": info[5],
            "save_start": info[6],
            "save_rule": str(info[7]),
            "freq": info[8]
        }
        res = []
        for i in range(0, len(config_data)):
            tmp = config_data[i]
            if str(tmp['ip']) == str(info[0]):
                res.append(data)
            else:
                res.append(config_data[i])
        with open("slave.json", 'w') as json_file:
            json.dump(res, json_file, indent=4)
        # config_data.append(data)
        # # 写入JSON文件
        # with open("slave.json", 'w') as json_file:
        #     json.dump(config_data, json_file, indent=4)

    def post(self):
        data = json.loads(self.request.body)
        if data['type'] == 'add':
            self.add(data)
        elif data['type'] == 'del':
            self.delete(data)
        elif data['type'] == 'edit':
            self.edit(data)
    # # 获取参数
    # param1 = data.get("param1")
    # param2 = data.get("param2")
    #
    # # 处理参数
    # # ...
    #
    # # 返回响应
    # self.write("Received param1: {} and param2: {}".format(param1, param2))


class SubmitSerialHandler(tornado.web.RequestHandler):
    def add(self, datas):
        info = datas['data']
        # 读取本地配置文件
        with open("serial.json", "r") as f:
            config_data = json.load(f)
        data = {
            "com": info[0],
            "band": info[1],
            "activate": info[2],
            "save_reg": info[3],
            "cmd": info[4],
            "read_start": info[5],
            "read_len": info[6],
            "save_start": info[7],
            "save_rule": str(info[8]),
            "freq": info[9]
        }
        config_data.append(data)
        # 写入JSON文件
        with open("serial.json", 'w') as json_file:
            json.dump(config_data, json_file, indent=4)

    def edit(self, datas):
        info = datas['data']

        # 读取本地配置文件
        with open("serial.json", "r") as f:
            config_data = json.load(f)
        data = {
            "com": info[0],
            "band": info[1],
            "activate": info[2],
            "save_reg": info[3],
            "cmd": info[4],
            "read_start": info[5],
            "read_len": info[6],
            "save_start": info[7],
            "save_rule": str(info[8]).replace("&quot;", "\""),
            "freq": info[9]
        }

        res = []
        for i in range(0, len(config_data)):
            tmp = config_data[i]
            if str(tmp['com']) == str(info[0]):
                res.append(data)
            else:
                res.append(config_data[i])
        with open("serial.json", 'w') as json_file:
            json.dump(res, json_file, indent=4)
        # config_data.append(data)
        # # 写入JSON文件
        # with open("slave.json", 'w') as json_file:
        #     json.dump(config_data, json_file, indent=4)

    def delete(self, datas):
        info = datas['data']
        # 读取本地配置文件
        with open("slave.json", "r") as f:
            config_data = json.load(f)
        res = []
        for i in range(0, len(config_data)):
            tmp = config_data[i]
            if str(tmp['ip']) == str(info[0]) and str(tmp['port']) == str(info[1]) and str(tmp['id']) == str(info[2]):

                log4p.logs("删除成功")
            else:
                res.append(config_data[i])
        if len(res) == 0:
            res = config_data
        # 写入JSON文件
        with open("slave.json", 'w') as json_file:
            json.dump(res, json_file, indent=4)

    def post(self):
        data = json.loads(self.request.body)
        if data['type'] == 'add':
            self.add(data)
        elif data['type'] == 'del':
            self.delete(data)
        elif data['type'] == 'edit':
            self.edit(data)


class SubmitMasterHandler(tornado.web.RequestHandler):

    def edit(self, datas):
        info = datas['data']
        # 读取本地配置文件
        with open("master.json", "r") as f:
            config_data = json.load(f)
        data = {
            "reg": info[0],
            "reg_addr": info[1],
            "len": info[2],
        }
        reg = config_data['reg']

        res = []
        for i in range(0, len(config_data)):
            tmp = reg[i]
            if str(tmp['reg']) == str(info[0]):
                res.append(data)
            else:
                res.append(reg[i])
        config_data['reg'] = res
        with open("master.json", 'w') as json_file:
            json.dump(config_data, json_file, indent=4)
        # config_data.append(data)
        # # 写入JSON文件
        # with open("slave.json", 'w') as json_file:
        #     json.dump(config_data, json_file, indent=4)

    def post(self):
        data = json.loads(self.request.body)
        if data['type'] == 'edit':
            self.edit(data)


class SubmitMasterHandler1(tornado.web.RequestHandler):

    def post(self):
        ip = self.get_body_argument("ip")
        port = self.get_body_argument("port")
        id = self.get_body_argument("id")

        # 读取本地配置文件
        with open("master.json", "r") as f:
            config_data = json.load(f)
        config_data['ip'] = ip
        config_data['port'] = port
        config_data['id'] = id
        with open("master.json", 'w') as json_file:
            json.dump(config_data, json_file, indent=4)
        self.render("master.html", data=config_data)


class FormSubmitHandler(tornado.web.RequestHandler):
    def ip_handle(self):
        eth = self.get_body_argument("eth")
        info = {}
        if eth == '1':
            ip1 = self.get_body_argument("ip1")
            mask1 = self.get_body_argument("mask1")
            gate1 = self.get_body_argument("gate1")
            subprocess.run(['/data/modify_net1_conf.sh', ip1, mask1, gate1])
            data = {
                "ip1": ip1,
                "mask1": mask1,
                "gate1": gate1
            }
            info['ip'] = ip1
            append_to_json("config.json", data)
        else:
            ip2 = self.get_body_argument("ip2")
            mask2 = self.get_body_argument("mask2")
            gate2 = self.get_body_argument("gate2")
            subprocess.run(['/data/modify_net2_conf.sh', ip2, mask2, gate2])
            data = {
                "ip2": ip2,
                "mask2": mask2,
                "gate2": gate2
            }
            info['ip'] = ip2
            append_to_json("config.json", data)
        append_to_json("config.json", info)

    def serial_handle(self):
        log4p.logs("处理serial")

    def slave_handle(self):

        log4p.logs("处理slave")

    def master_handle(self):
        log4p.logs("处理master")

    def post(self):
        type = self.get_body_argument("type")
        if type == 'ip':
            self.ip_handle()
        elif type == 'serial':
            self.serial_handle()
        elif type == 'slave':
            self.slave_handle()
        elif type == 'master':
            self.master_handle()


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/submit", FormSubmitHandler),
        (r"/ip", IpHandler),
        (r"/serial", SerialHandler),
        (r"/slave", SlaveHandler),
        (r"/master", MasterHandler),
        (r"/restartService", RestartHandler),
        (r"/restart", RestartHandler1),
        (r"/subSlave", SubmitSlaveHandler),
        (r"/subSerial", SubmitSerialHandler),
        (r"/subMaster", SubmitMasterHandler),
        (r"/subMaster1", SubmitMasterHandler1),
        (r"/refresh", RefreshHandler),
        # 新增路由
        (r"/logs", LogsHandler),
        (r"/ws", WebSocketHandler),
    ], debug=True)


def default_json_data():
    # 默认的config
    config = {"ip1": "192.168.1.230", "mask1": "255.255.255.0", "gate1": "192.168.1.10", "ip2": "192.168.0.230",
              "mask2": "255.255.255.0", "gate2": "192.168.0.10", "ip": "127.0.0.1", "port": 8889}
    # 检查文件是否存在
    if not os.path.exists('config.json'):
        # 文件不存在，创建并写入默认值
        with open('config.json', 'w') as file:
            json.dump(config, file)
        log4p.logs(f"File '{'config.json'}' created and initialized with default values.")
    else:
        # 文件已存在，不执行任何操作
        log4p.logs(f"File '{'config.json'}' already exists. No action taken.")

    # 默认的serial
    serial = [{"com": "/dev/ttyS1", "band": "115200", "activate": "0", "save_reg": "co", "cmd": "FF06000000021DD5",
               "read_start": "2", "read_len": "8", "save_start": "0x00", "save_rule": "[]", "freq": "5"},
              {"com": "/dev/ttyS2", "band": "9600", "activate": "0", "save_reg": "co", "cmd": "FF06000000021DD5",
               "read_start": "2", "read_len": "8", "save_start": "0x00",
               "save_rule": '[]',
               "freq": "0.5"},
              {"com": "/dev/ttyS3", "band": "9600", "activate": "0", "save_reg": "co", "cmd": "FF06000000021DD5",
               "read_start": "2", "read_len": "8", "save_start": "0x00", "save_rule": "[]", "freq": "5"},
              {"com": "/dev/ttyS4", "band": "9600", "activate": "0", "save_reg": "co", "cmd": "FF06000000021DD5",
               "read_start": "2", "read_len": "8", "save_start": "0x00", "save_rule": "[]", "freq": "5"}]
    # 检查文件是否存在
    if not os.path.exists('serial.json'):
        # 文件不存在，创建并写入默认值
        with open('serial.json', 'w') as file:
            json.dump(serial, file)
        log4p.logs(f"File '{'serial.json'}' created and initialized with default values.")
    else:
        # 文件已存在，不执行任何操作
        log4p.logs(f"File '{'serial.json'}' already exists. No action taken.")

    # 默认的slave
    slave = [{"ip": "127.0.0.1", "port": "10086", "id": "0x01", "reg": "co", "reg_len": "22", "reg_addr": "0x01",
              "save_start": "0x0F", "save_rule": "[]", "freq": "0.2"}]
    # 检查文件是否存在
    if not os.path.exists('slave.json'):
        # 文件不存在，创建并写入默认值
        with open('slave.json', 'w') as file:
            json.dump(slave, file)
        log4p.logs(f"File '{'slave.json'}' created and initialized with default values.")
    else:
        # 文件已存在，不执行任何操作
        log4p.logs(f"File '{'slave.json'}' already exists. No action taken.")

    # 默认的master
    master = {"reg": [{"reg": "co", "reg_addr": "0x0F", "len": "16"}, {"reg": "di", "reg_addr": "0x1F", "len": "16"},
                      {"reg": "ir", "reg_addr": "0x2F", "len": "16"}, {"reg": "hr", "reg_addr": "0x3F", "len": "16"}],
              "ip": "192.168.1.230", "port": "20000", "id": "0x0a"}
    # 检查文件是否存在
    if not os.path.exists('master.json'):
        # 文件不存在，创建并写入默认值
        with open('master.json', 'w') as file:
            json.dump(master, file)
        log4p.logs(f"File '{'master.json'}' created and initialized with default values.")
    else:
        # 文件已存在，不执行任何操作
        log4p.logs(f"File '{'master.json'}' already exists. No action taken.")


# 模拟生成日志的线程函数
def generate_test_logs():
    counter = 0
    while True:
        log4p.logs(f"测试日志 #{counter}")
        counter += 1
        import time
        time.sleep(0.1)  # 每秒生成一条日志


if __name__ == "__main__":
    default_json_data()
    with open("config.json", "r") as f:
        config_data = json.load(f)

    MainHandler.run_script()
    app = make_app()
    address = config_data['ip1']
    # address = '127.0.0.1'
    port = config_data['port']
    http_server = httpserver.HTTPServer(app)
    http_server.listen(port=port, address=address)
    print("URL:http://{}:{}/".format(address, port))
    # 可选：启动测试日志生成线程（实际使用时可以注释掉）

    # 设置周期性日志检查
    io_loop = ioloop.IOLoop.instance()
    setup_periodic_log_check()

    io_loop.start()
