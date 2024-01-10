import struct
from binascii import unhexlify
from crcmod import crcmod

class DataUtil:
    # 定义一个函数，接受一个八位的十六进制字符串作为参数，返回对应的浮点数
    @staticmethod
    def hex_to_float(self, hex_str):
        # 将十六进制字符串转换为整数
        hex_int = int(hex_str, 16)
        # 将整数转换为四个字节的二进制数据
        hex_bytes = hex_int.to_bytes(4, "big")
        # 将二进制数据解析为浮点数
        hex_float = struct.unpack(">f", hex_bytes)[0]
        # 返回浮点数
        return hex_float


    # CRC16-MODBUS
    @staticmethod
    def get_crc(self, read):
        crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        data = read.replace(" ", "")
        readcrcout = hex(crc16(unhexlify(data))).upper()
        str_list = list(readcrcout)
        if len(str_list) < 6:
            str_list.insert(2, '0' * (6 - len(str_list)))  # 位数不足补0
        crc_data = "".join(str_list)
        return crc_data[4:] + crc_data[2:4]

    @staticmethod
    def check_crc(self, read):
        data = read.replace(" ", "")
        a = data[0:len(data) - 4]
        b = data[len(data) - 4:]
        if self.get_crc(a).upper() == b.upper():
            return True
        else:
            return False

    @staticmethod
    def bytes_to_hex_string(self, bytes):
        return ''.join('{:02x}'.format(byte) for byte in bytes)
