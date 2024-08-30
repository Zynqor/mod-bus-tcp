import struct
from binascii import unhexlify
from crcmod import crcmod


class DataUtil:
    # 定义一个函数，接受一个八位的十六进制字符串作为参数，返回对应的浮点数
    @staticmethod
    def hex_to_float(hex_str):
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
    def get_crc(read):
        crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        data = read.replace(" ", "")
        readcrcout = hex(crc16(unhexlify(data))).upper()
        str_list = list(readcrcout)
        if len(str_list) < 6:
            str_list.insert(2, '0' * (6 - len(str_list)))  # 位数不足补0
        crc_data = "".join(str_list)
        return crc_data[4:] + crc_data[2:4]

    @staticmethod
    def check_crc(read):
        data = read.replace(" ", "")
        a = data[0:len(data) - 4]
        b = data[len(data) - 4:]
        if DataUtil.get_crc(a).upper() == b.upper():
            return True
        else:
            return False

    @staticmethod
    def bytes_to_hex_string(bytes):
        return ''.join('{:02x}'.format(byte) for byte in bytes)

    @staticmethod
    def complement_32(arr):
        ''' 将数组中的每个整数转换为32位补码表示的字符串列表'''
        expanded_array = []
        for num in arr:
            if num >= 0:
                # 正数的补码与原码相同
                expanded_array.append(bin(num)[2:].zfill(32))
            else:
                # 负数先求绝对值的二进制表示，再取反加一
                abs_num = abs(num)
                binary_str = bin(abs_num)[2:].zfill(32)
                inverted_str = "".join(['1' if bit == '0' else '0' for bit in binary_str])
                expanded_array.append(bin(int(inverted_str, 2) + 1)[2:])
        return expanded_array

    @staticmethod
    def expand_arr_2_hex(arr):
        '''
        将数组中的数转化为32位补码,并且拆成两个字节的十六进制
        '''
        res = []
        bin_32 = DataUtil.complement_32(arr)
        for i in bin_32:
            res.append(DataUtil.bin_to_hex(i[16:]))
            res.append(DataUtil.bin_to_hex(i[:16]))

        return res

    @staticmethod
    def expand_arr_2_demical(arr):
        '''
        将数组中的数转化为32位补码,并且拆成两个字节的十进制
        '''
        res = []
        tmp = DataUtil.expand_arr_2_hex(arr)
        for i in tmp:
            res.append(int(i, 16))

        return res

    # 32位二进制字符串转十六进制字符串
    @staticmethod
    def bin_to_hex(bin_str):
        hex_str = hex(int(bin_str, 2))[2:]
        return hex_str.upper()


if __name__ == '__main__':
    res = DataUtil.hex_to_float("9800")
    print(res)
    original_array = [26200, 0, 200, 205900]
    expanded_array = DataUtil.expand_arr_2_hex(original_array)
    print(expanded_array)
    expanded_array = DataUtil.expand_arr_2_demical(original_array)

    print(expanded_array)
