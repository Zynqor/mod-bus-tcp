import struct
import threading
from binascii import unhexlify
from crcmod import crcmod

from Util.log4p import log4p

global_data_storage = {}
data_lock = threading.Lock()
class DataUtil:
    # 定义一个函数，接受一个八位的十六进制字符串作为参数，返回对应的浮点数
    @staticmethod
    def update_global_data(thread_id, data):
        with data_lock:
            global_data_storage[thread_id] = data

    @staticmethod
    def get_global_data(thread_id):
        with data_lock:
            return global_data_storage.get(thread_id)

    @staticmethod
    def merge_data():
        """
        合并两个线程的数据
        规则：
        - 一个0，一个非0 -> 保留非0
        - 都是0 -> 输出0
        - 都非0 -> 保留第一个数组的数据

        返回：合并后的数据，如果数据不齐则返回None
        """
        with data_lock:
            if len(global_data_storage) < 2:
                return None  # 数据还没齐

            # 获取两个数组（字典中的前两个）
            data_arrays = list(global_data_storage.values())
            arr1 = data_arrays[0]
            arr2 = data_arrays[1]

            # 确保两个数组长度相同
            max_len = max(len(arr1), len(arr2))
            if len(arr1) < max_len:
                arr1 = arr1 + [0] * (max_len - len(arr1))
            if len(arr2) < max_len:
                arr2 = arr2 + [0] * (max_len - len(arr2))

            merged = []
            for i in range(max_len):
                val1, val2 = arr1[i], arr2[i]

                if val1 == 0 and val2 != 0:
                    merged.append(val2)  # 保留非0值
                elif val1 != 0 and val2 == 0:
                    merged.append(val1)  # 保留非0值
                elif val1 == 0 and val2 == 0:
                    merged.append(0)  # 都是0，输出0
                else:  # 都非0
                    merged.append(val1)  # 保留第一个数组的值

            return merged
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
        res = []
        for num in arr:
            if num < -2 ** 31 or num > 2 ** 31 - 1:
                log4p.logs(f"输入 {num} 超出了32位有符号整数的范围")
                return res
            if num >= 0:
                res.append(format(num, '032b'))
            else:
                res.append(format((1 << 32) + num, '032b'))

        return res

    @staticmethod
    def to_hex_2_digits_upper(number):
        """
        将一个整数转换为固定的两位大写十六进制字符串。
        """
        return f"{number:02X}"
    @staticmethod
    def expand_arr_2_float32_decimal(arr, little_endian=True):
        '''
        将数组中的数转化为32位浮点数,并且拆成两个16位寄存器的十进制值
        用于Modbus 32bit float显示

        Args:
            arr: 输入数组
            little_endian: False=高位在前(默认), True=低位在前
        '''
        res = []

        for num in arr:
            # 将数字转换为32位浮点数的字节表示
            float_bytes = struct.pack('>f', float(num))  # 大端序32位浮点数

            # 将4个字节拆分为2个16位值
            high_16 = struct.unpack('>H', float_bytes[:2])[0]  # 高16位
            low_16 = struct.unpack('>H', float_bytes[2:])[0]  # 低16位

            if little_endian:
                res.append(low_16)  # 低位在前
                res.append(high_16)  # 高位在后
            else:
                res.append(high_16)  # 高位在前（默认）
                res.append(low_16)  # 低位在后

        return res

    @staticmethod
    def expand_arr_2_float32_hex(arr):
        '''
        将数组中的数转化为32位浮点数,并且拆成两个16位寄存器的十六进制值
        '''
        res = []

        for num in arr:
            # 将数字转换为32位浮点数的字节表示
            float_bytes = struct.pack('>f', float(num))  # 大端序32位浮点数

            # 将4个字节拆分为2个16位值，并转换为十六进制
            high_16 = struct.unpack('>H', float_bytes[:2])[0]
            low_16 = struct.unpack('>H', float_bytes[2:])[0]

            res.append(f"{high_16:04X}")  # 转换为4位十六进制
            res.append(f"{low_16:04X}")

        return res
    @staticmethod
    def expand_arr_2_hex(arr):
        '''
        将数组中的数转化为32位补码,并且拆成两个字节的十六进制
        '''
        res = []
        bin_32 = DataUtil.complement_32(arr)
        for i in bin_32:
            res.append(DataUtil.bin_to_hex(i[:16]))
            res.append(DataUtil.bin_to_hex(i[16:]))
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
    test_numbers = [10, 20, 30, 40, 3.14159, -5.5, 0.0, 1000.123]

    print("原始数字 -> 32位浮点数 -> Modbus寄存器值")
    print("=" * 50)

    for num in test_numbers:
        # 显示原始浮点数的字节表示
        float_bytes = struct.pack('>f', float(num))
        hex_repr = float_bytes.hex().upper()

        # 获取寄存器值
        decimal_regs = DataUtil.expand_arr_2_float32_decimal([num])
        hex_regs = DataUtil.expand_arr_2_float32_hex([num])

        print(f"{num:>10} -> {hex_repr} -> 十进制: {decimal_regs} | 十六进制: {hex_regs}")

    print("\n批量转换测试:")
    input_arr = [10, 20, 30, 40]
    result = DataUtil.expand_arr_2_float32_decimal(input_arr)
    print(f"输入: {input_arr}")
    print(f"输出: {result}")

    # 验证：将结果转换回浮点数
    print("\n验证转换正确性:")
    for i in range(0, len(result), 2):
        high_16 = result[i]
        low_16 = result[i + 1]

        # 重新组合为32位浮点数
        combined_bytes = struct.pack('>HH', high_16, low_16)
        recovered_float = struct.unpack('>f', combined_bytes)[0]

        original_num = input_arr[i // 2]
        print(f"原始: {original_num} -> 恢复: {recovered_float} -> 匹配: {abs(original_num - recovered_float) < 1e-6}")

