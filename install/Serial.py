import serial.tools.list_ports
import time
import threading
from binascii import *
from crcmod import *
import struct

from Util.RuleUtil import RuleUtil
from Util.log4p import log4p


class Serial(threading.Thread):
    def __init__(self, serial_info, server, as_slave_id):
        # 创建 UI 界面
        super().__init__()
        self.running = True
        self.as_slave_id = as_slave_id
        self.server = server
        self.port = serial_info['com']
        self.band = int(serial_info['band'])
        self.save_reg = serial_info['save_reg']
        self.cmd = serial_info['cmd']
        self.read_start = int(serial_info['read_start'], 16)
        self.read_len = int(serial_info['read_len'])
        self.save_start = int(serial_info['save_start'], 16)
        self.save_rule = serial_info['save_rule']
        self.freq = float(serial_info['freq'])
        self.serial = serial.Serial(port=self.port, baudrate=self.band, timeout=0.2)
        self.history_data = []

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            self.send_serial()
            self.read_serial()
            time.sleep(self.freq)

    def read_serial(self):
        if self.serial.in_waiting:
            data = self.serial.read(self.serial.in_waiting)
            #log4p.logs("收到串口数据:\t" + str(data))
            info = self.bytes_to_hex_string(data).upper().replace(" ", "")
            if self.check_crc(info):
                self.handle_res(info)

    def send_serial(self):
        self.serial.write(bytes.fromhex(self.cmd + self.get_crc(self.cmd)))

    def convert_two_byte(self, hex_str):
        result = []
        for i in range(0, len(hex_str), 4):
            group = hex_str[i:i + 4]
            if len(group) == 4:
                value = int(group, 16)
                result.append(value)
        return result

    def convert_each_digit(self, hex_str):
        binary_result = []
        for char in hex_str:
            if char.isdigit():
                decimal_value = int(char)
            elif char.lower() in 'abcdef':
                decimal_value = ord(char.lower()) - 87
            binary_value = bin(decimal_value)[2:].zfill(4)
            for bit in binary_value:
                binary_result.append(int(bit))
        return binary_result

    def handle_res(self, result):
        log4p.logs("接收到的数据：" + str(result))
        reg = self.save_reg
        if len(result) < self.read_start + self.read_len:
            result = result + '0' * (self.read_start + self.read_len - len(result))
        log4p.logs("读取的数据长度：" + str(len(result)))
        result = result[self.read_start:self.read_start + self.read_len]
        if reg == 'co':
            res = self.convert_each_digit(result)
            if self.save_rule == "[]":
                self.server.context[self.as_slave_id].setValues(1, self.save_start, res)
            else:
                self.add_data(res)
                handle_res = RuleUtil.handle_rule(self.history_data, self.save_rule)
                if not handle_res['status']:
                    log4p.logs("结果处理失败...,失败数据:\t" + str(self.history_data))

                datas = handle_res['data']
                if 32768 in datas:
                    self.process_data(datas, 1)
                else:
                    self.server.context[self.as_slave_id].setValues(1, self.save_start, datas)

        elif reg == 'di':
            res = self.convert_each_digit(result)
            if self.save_rule == "[]":
                self.server.context[self.as_slave_id].setValues(2, self.save_start, res)
            else:
                self.add_data(res)
                handle_res = RuleUtil.handle_rule(self.history_data, self.save_rule)
                if not handle_res['status']:
                    log4p.logs("结果处理失败...,失败数据:\t" + str(self.history_data))
                datas = handle_res['data']

                if 32768 in datas:
                    self.process_data(datas, 2)
                else:
                    self.server.context[self.as_slave_id].setValues(2, self.save_start, datas)

        elif reg == 'hr':
            res = self.convert_two_byte(result)
            if self.save_rule == "[]":
                self.server.context[self.as_slave_id].setValues(3, self.save_start, res)
            else:
                self.add_data(res)
                handle_res = RuleUtil.handle_rule(self.history_data, self.save_rule)
                if not handle_res['status']:
                    log4p.logs("结果处理失败...,失败数据:\t" + str(self.history_data))
                datas = handle_res['data']
                if 32768 in datas:
                    self.process_data(datas, 3)
                else:
                    self.server.context[self.as_slave_id].setValues(3, self.save_start, datas)

        elif reg == 'ir':
            res = self.convert_two_byte(result)
            if self.save_rule == "[]":
                self.server.context[self.as_slave_id].setValues(4, self.save_start, res)
            else:
                self.add_data(res)
                handle_res = RuleUtil.handle_rule(self.history_data, self.save_rule)
                if not handle_res['status']:
                    log4p.logs("结果处理失败...,失败数据:\t" + str(self.history_data))
                datas = handle_res['data']
                if 32768 in datas:
                    self.process_data(datas, 4)
                else:
                    self.server.context[self.as_slave_id].setValues(4, self.save_start, datas)

    # 定义一个函数，接受一个八位的十六进制字符串作为参数，返回对应的浮点数
    def hex_to_float(self, hex_str):
        # 将十六进制字符串转换为整数
        hex_int = int(hex_str, 16)
        # 将整数转换为四个字节的二进制数据
        hex_bytes = hex_int.to_bytes(4, "big")
        # 将二进制数据解析为浮点数
        hex_float = struct.unpack(">f", hex_bytes)[0]
        # 返回浮点数
        return hex_float

    def process_data(self, datas, reg):
        i = 0
        while i < len(datas):
            if i != len(datas) - 1 and i % 2 == 0 and datas[i + 1] == 0 and datas[i] == 32768:
                i += 2
                continue

            # log4p.logs(f"write to address:\tid={self.save_start + i}\tvalue={datas[i]}")
            self.server.context[self.as_slave_id].setValues(reg, self.save_start + i, [datas[i]])
            i += 1

    def split_cmd(self, cmd):
        if len(cmd) % 2 == 1:
            return "cmd len error"
        # 初始化一个空字符串，用来存储结果
        result = ""
        # 遍历字符串的每个字符
        for i in range(len(cmd)):
            # 把字符添加到结果字符串中
            result += cmd[i]
            # 如果是偶数位置的字符，且不是最后一个字符，就在后面添加一个空格
            if i % 2 == 1 and i < len(cmd) - 1:
                result += " "
        # 返回结果字符串
        return result

    # CRC16-MODBUS
    def get_crc(self, read):
        crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        data = read.replace(" ", "")
        readcrcout = hex(crc16(unhexlify(data))).upper()
        str_list = list(readcrcout)
        if len(str_list) < 6:
            str_list.insert(2, '0' * (6 - len(str_list)))  # 位数不足补0
        crc_data = "".join(str_list)
        return crc_data[4:] + crc_data[2:4]

    def check_crc(self, read):
        data = read.replace(" ", "")
        a = data[0:len(data) - 4]
        b = data[len(data) - 4:]
        if self.get_crc(a).upper() == b.upper():
            return True
        else:
            return False

    def bytes_to_hex_string(self, bytes):
        return ''.join('{:02x}'.format(byte) for byte in bytes)

    def add_data(self, new_data):
        self.history_data.append(new_data)
        if len(self.history_data) > 50:
            self.history_data.pop(0)
