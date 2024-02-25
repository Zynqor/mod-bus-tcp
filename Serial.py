import traceback

import serial.tools.list_ports
import time
import threading
from binascii import *
from crcmod import *
import struct


class Serial(threading.Thread):
    def __init__(self, serial_info):
        # 创建 UI 界面
        super().__init__()
        self.running = True
        self.port = serial_info[0]
        self.band = int(serial_info[1])
        self.save_reg = serial_info[3]
        self.cmd = serial_info[4]
        self.read_start = int(serial_info[5], 16)
        self.read_len = int(serial_info[6])
        self.save_start = int(serial_info[7], 16)
        self.save_len = int(serial_info[8])
        self.freq = float(serial_info[9])
        self.serial = serial.Serial(port=self.port, baudrate=self.band, timeout=0.2)

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
            info = self.bytes_to_hex_string(data).upper().replace(" ", "")
            if self.check_crc(info):
                self.handle_res(info)

    def send_serial(self):
        self.serial.write(bytes.fromhex(self.cmd + self.get_crc(self.cmd)))

    def handle_res(self, res):
        print(res)

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
