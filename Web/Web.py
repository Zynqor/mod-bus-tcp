import tornado.ioloop
import tornado.web
import subprocess
from tornado import httpserver, ioloop
import json


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

    print("数据已追加写入JSON文件:", file_path)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("config.json", "r") as f:
            config_data = json.load(f)
        self.render("index.html", data=config_data)


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
        print(config_data[0])
        self.render("slave.html", data=config_data)


class SerialHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("config.json", "r") as f:
            config_data = json.load(f)
        self.render("serial.html", data=config_data)


class MasterHandler(tornado.web.RequestHandler):
    def get(self):
        # 读取本地配置文件
        with open("config.json", "r") as f:
            config_data = json.load(f)
        self.render("master.html", data=config_data)


class AddSlaveHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        print(data)
        # # 获取参数
        # param1 = data.get("param1")
        # param2 = data.get("param2")
        #
        # # 处理参数
        # # ...
        #
        # # 返回响应
        # self.write("Received param1: {} and param2: {}".format(param1, param2))
        # # 读取本地配置文件
        # with open("config.json", "r") as f:
        #     config_data = json.load(f)


class FormSubmitHandler(tornado.web.RequestHandler):
    def ip_handle(self):
        eth = self.get_body_argument("eth")
        info = {}
        if eth == '1':
            ip1 = self.get_body_argument("ip1")
            mask1 = self.get_body_argument("mask1")
            gate1 = self.get_body_argument("gate1")
            subprocess.run(['./modify_net1_conf.sh', ip1, mask1, gate1])
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
            subprocess.run(['./modify_net2_conf.sh', ip2, mask2, gate2])
            data = {
                "ip2": ip2,
                "mask2": mask2,
                "gate2": gate2
            }
            info['ip'] = ip2
            append_to_json("config.json", data)
        append_to_json("config.json", info)

    def serial_handle(self):
        print("处理serial")

    def slave_handle(self):

        print("处理slave")

    def master_handle(self):
        print("处理master")

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
        (r"/addSlave", AddSlaveHandler),
    ], debug=True)


if __name__ == "__main__":
    with open("config.json", "r") as f:
        config_data = json.load(f)
    app = make_app()
    address = config_data['ip']
    port = config_data['port']
    http_server = httpserver.HTTPServer(app)
    http_server.listen(port=port, address=address)
    print("URL:http://{}:{}/".format(address, port))
    ioloop.IOLoop.instance().start()
