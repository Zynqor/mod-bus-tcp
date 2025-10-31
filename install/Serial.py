import json
import sys
from platform import system
import random
import serial.tools.list_ports
import time
import threading
from binascii import *
from crcmod import *
import struct

from Util.RuleUtil import RuleUtil
from Util.log4p import log4p
from Util.DataUtil import DataUtil


class Serial(threading.Thread):
    def __init__(self, serial_info, context, as_slave_id):
        super().__init__()
        self.running = True
        self.as_slave_id = as_slave_id
        self.context = context  # <-- 直接保存共享的 context

        # --- 您其他的初始化代码保持不变 ---
        self.port = serial_info['com']
        self.band = int(serial_info['band'])
        self.save_reg = serial_info['save_reg']
        self.cmd = serial_info['cmd']
        self.read_start = int(serial_info['read_start'], 16)
        self.read_len = int(serial_info['read_len'])
        self.save_start = int(serial_info['save_start'], 16)
        self.save_rule = serial_info['save_rule']
        self.freq = float(serial_info['freq'])
        try:
            self.serial = serial.Serial(port=self.port, baudrate=self.band, timeout=0.2)
            log4p.logs(f"✓ 串口 {self.port} 打开成功")
        except Exception as e:
            log4p.logs(f"✗ 串口 {self.port} 打开失败: {e}")
            self.running = False  # 标记为不运行
            raise  # 重新抛出异常
        self.history_data = []
        log4p.logs(f"启动串口主机轮询服务 on {self.port}...")
        with open("correct_data.json", "r") as f:
            self.correct_data = json.load(f)
        self.counter = 0

    def stop(self):
        self.running = False

    def run(self):
        log4p.logs(f"串口线程开始运行: {self.port}")
        while self.running:
            self.send_serial()
            self.read_serial()
            time.sleep(self.freq)

    def read_serial(self):
        if self.serial.in_waiting:
            data = self.serial.read(self.serial.in_waiting)
            # log4p.logs("收到串口数据:\t" + str(data))
            info = self.bytes_to_hex_string(data).upper().replace(" ", "")

            # 计算info的长度，并以58为步长进行遍历
            info_len = len(info)
            for i in range(0, info_len, 58):
                # 切割出长度为58的子字符串
                chunk = info[i:i + 58]

                # 确保切割出的部分长度正好是58
                if len(chunk) == 58:
                    # 对每一个切割后的部分进行CRC校验和处理
                    if self.check_crc(chunk):
                        self.handle_res(chunk)

    def send_serial(self):
        cmds = self.cmd.split(';')
        for cmd in cmds:
            send_cmd = cmd + self.get_crc(cmd)
            log4p.logs("Tx:\t" + str(send_cmd))
            self.serial.write(bytes.fromhex(send_cmd))
            time.sleep(0.8)
        # self.counter += 1
        # if self.counter == 33:
        #     self.counter = 0
        # self.handle_res(
        #     DataUtil.to_hex_2_digits_upper(self.counter) + "0418CCCD41CC3D713F0A000042C43333C235E3543F05999A419141F4")

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

    def convert2Tcp(self, raw_data, config):

        # log4p.logs("收到串口数据:\t" + str(raw_data))

        temp = self.hex_to_float(raw_data[10:14] + raw_data[6:10])
        pressure = self.hex_to_float(raw_data[18:22] + raw_data[14:18])
        weishui = self.hex_to_float(raw_data[26:30] + raw_data[22:26])
        ludian = self.hex_to_float(raw_data[34:38] + raw_data[30:34])
        raw_press = self.hex_to_float(raw_data[42:46] + raw_data[38:42])
        humid = self.hex_to_float(raw_data[50:54] + raw_data[46:50])

        log4p.logs("Addr:" + raw_data[0:2] + "\t温度:" + str(temp) + "\t压力:" + str(pressure) + "\t微水:" + str(
            weishui) + "\t露点:" + str(
            ludian) + "\t原始压力:" + str(raw_press) + "\t湿度:" + str(humid))

        temp = float(config['tempature']['k']) * temp + float(config['tempature']['b'])
        pressure = float(config['pressure']['k']) * pressure + float(config['pressure']['b'])
        weishui = float(config['weishui']['k']) * weishui + float(config['weishui']['b'])
        ludian = float(config['ludian']['k']) * ludian + float(config['ludian']['b'])
        raw_press = float(config['raw_press']['k']) * raw_press + float(config['raw_press']['b'])
        humid = float(config['humid']['k']) * humid + float(config['humid']['b'])
        log4p.logs(
            "Addr:" + raw_data[0:2] + "\t基础修正后 温度1:" + str(temp) + "\t压力1:" + str(pressure) + "\t微水1:" + str(
                weishui) + "\t露点1:" + str(ludian) + "\t原始压力1:" + str(raw_press) + "\t湿度1:" + str(humid))
        # 微水校正
        if config['correct_weishui']['mode'] == 1:
            if pressure >= 0.1:
                if weishui <= 200:
                    print()
                elif weishui > 200 and weishui <= 1000:
                    log4p.logs("压力大于0.1Mpa,微水大于200ppm小于1000ppm,设定值 + 基础处理值 × 0.1")
                    weishui = weishui * 0.1 + float(config['correct_weishui']['target1'])
                elif weishui > 1000 and weishui <= 10000:
                    
                    weishui = weishui * 0.01 + float(config['correct_weishui']['target1'])
                elif weishui > 10000 and weishui <= 100000:
                    
                    weishui = weishui * 0.001 + float(config['correct_weishui']['target1'])
                elif weishui > 100000 and weishui <= 1000000:
                    
                    weishui = weishui * 0.0001 + float(config['correct_weishui']['target1'])
        if config['correct_weishui']['mode'] == 2:
            weishui = random.uniform(int(config['correct_weishui']['corr_start']),
                                     int(config['correct_weishui']['corr_end'])) + float(
                config['correct_weishui']['target2'])
        log4p.logs("Addr:" + raw_data[0:2] + "\t高级修正后的微水:" + str(
            weishui))
        res = DataUtil.expand_arr_2_float32_decimal([temp, pressure, weishui, ludian, raw_press, humid])

        slave_context = self.context[self.as_slave_id]
        slave_context.setValues(3, int(config['tempature']['addr'], 16), res[0:2])
        slave_context.setValues(3, int(config['pressure']['addr'], 16), res[2:4])
        slave_context.setValues(3, int(config['weishui']['addr'], 16), res[4:6])
        slave_context.setValues(3, int(config['ludian']['addr'], 16), res[6:8])
        slave_context.setValues(3, int(config['raw_press']['addr'], 16), res[8:10])
        slave_context.setValues(3, int(config['humid']['addr'], 16), res[10:12])

    def handle_res(self, result):
        self.convert2Tcp(result, self.correct_data[result[0:2]])

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
