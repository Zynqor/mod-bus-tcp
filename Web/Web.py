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
            "save_len": info[7],
            "freq": info[8]
        }
        config_data.append(data)
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

                print("删除成功")
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
            "save_len": info[7],
            "freq": info[8]
        }
        res = []
        for i in range(0, len(config_data)):
            tmp = config_data[i]
            if str(tmp['ip']) == str(info[0]) and str(tmp['port']) == str(info[1]) and str(tmp['id']) == str(info[2]):
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
            "save_len": info[8],
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
            "save_len": info[8],
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

                print("删除成功")
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
        (r"/subSlave", SubmitSlaveHandler),
        (r"/subSerial", SubmitSerialHandler),
        (r"/subMaster", SubmitMasterHandler),
        (r"/subMaster1", SubmitMasterHandler1),
        (r"/refresh", RefreshHandler)
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
