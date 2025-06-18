import json
from xml.sax.saxutils import escape

from Util.DataUtil import DataUtil
from Util.log4p import log4p
import struct

class RuleUtil:
    calculate_type = ['AVG', 'RATIO', 'MAX50', 'MIN50', 'UBALA', 'AVGDIFF', 'MAX/MIN50', 'DIFF', 'None']

    @staticmethod
    def avg(data_list):
        """
        计算平均值
        :param data_list: 数据列表
        :return:
        """
        return sum(data_list) * 1.0 / len(data_list)

    @staticmethod
    def ratio(data1, data2):
        """
        计算比率
        :param data1: 被除数
        :param data2: 除数
        :return:
        """
        if data2 == 0:
            return 0
        else:
            return data1 * 1.0 / data2

    @staticmethod
    def ubala(data_list):
        """
        (MAX(arg1-avg,arg2-avg,arg3-avg)/avg)*100%
        :param data_list: 数据列表
        :return:
        """
        tmp = []
        avg = RuleUtil.avg(data_list)
        if avg == 0:
            return 0
        for data in data_list:
            tmp.append(data - avg)

        return max(tmp) * 1.0 / avg

    @staticmethod
    def avgdiff(data_list):
        '''
        arg1 - (arg1+...+argn)/n
        :param data_list:
        :return:
        '''

        return (data_list[0] - RuleUtil.avg(data_list)) * 1.0

    @staticmethod
    def max_min(data_list):
        '''
        最大值和最小值的比值
        :param data_list:
        :return:
        '''
        min_value = min(data_list)
        if min_value == 0:
            return 0
        max_value = max(data_list)
        return max_value * 1.0 / min_value

    @staticmethod
    def diff(arg1, arg2):
        """
        相减
        :param arg1: 参数1
        :param arg2: 参数2
        :return:
        """
        return (arg1 - arg2) * 1.0

    @staticmethod
    def handle_rule(history_data, save_rule):
        """
        处理规则
        :param history_data: 历史数据
        :param save_rule: 保存的规则
        :return:
        """
        res = {
            'status': False
        }
        res_len = 0

        rule = json.loads(save_rule)
        for item in rule:
            data_index = item['data_index']
            calculate = item['calculate']
            data_save_index = item['data_save_index']
            result_save_index = item['result_save_index']
            calculate_desc = item['calculate_desc']

            #log4p.logs(f"data_index: {data_index}\t" + f"calculate: {calculate}" + f"data_save_index: {data_save_index}\t" + f"result_save_index: {result_save_index}\t" + f"calculate_desc: {calculate_desc}")
            if isinstance(data_index, list) and isinstance(data_save_index, list):
                if len(data_index) < len(data_save_index):
                    log4p.logs("data_index的长度不能小于data_save_index的长度,错误数据为:\t" + str(item))
                    return res
                else:
                    for i in data_save_index:
                        if int(i) > res_len:
                            res_len = int(i)
            else:
                log4p.logs("data_index和data_save_index必须为list,错误数据为:\t" + str(item))
                return res
            if calculate not in RuleUtil.calculate_type:
                log4p.logs("calculate类型有误,错误数据为:\t" + str(item))
                return res
            else:
                if not isinstance(int(result_save_index), int):
                    log4p.logs("result_save_index必须为整数,错误数据为:\t" + str(item))
                    return res

                if calculate != "None":
                    if int(result_save_index) > res_len:
                        res_len = int(result_save_index)

        # 长度要比最大下表大1
        res_len += 1
        result = [0] * res_len

        # 记录实际使用的index,不使用的index就不记录,填充65536作为标识数据
        used_index = []

        for item in rule:
            data_index = item['data_index']
            calculate = item['calculate']
            data_save_index = item['data_save_index']
            result_save_index = item['result_save_index']
            calculate_desc = item['calculate_desc']

            # 待运算的数据
            tmp_data_list = []

            for i in range(0, len(data_save_index)):
                # 把元数据存储到目标书组的data_save_index
                result[int(data_save_index[i])] = history_data[-1][int(data_index[i])]
                used_index.append(int(data_save_index[i]))

            for i in range(0, len(data_index)):
                tmp_data_list.append(history_data[-1][int(data_index[i])])

            # 使用到的index只存在于result_save_index,data_save_index
            used_index.append(int(result_save_index))
            if calculate == "None":
                pass
            elif calculate == RuleUtil.calculate_type[0]:
                result[int(result_save_index)] = RuleUtil.avg(tmp_data_list)

            elif calculate == RuleUtil.calculate_type[1]:
                if len(tmp_data_list) != 2:
                    log4p.logs("RATIO运算数据长度必须为2,错误数据为:\t" + str(item))
                    return res
                result[int(result_save_index)] = RuleUtil.ratio(tmp_data_list[0], tmp_data_list[1])
            elif calculate == RuleUtil.calculate_type[2]:
                if len(data_index) != 1:
                    log4p.logs("MAX50运算数据长度必须为1,错误数据为:\t" + str(item))
                    return res

                # MAX50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[0])])

                result[int(result_save_index)] = max(tmp_history)
            elif calculate == RuleUtil.calculate_type[3]:
                if len(data_index) != 1:
                    log4p.logs("MIN50运算数据长度必须为1,错误数据为:\t" + str(item))
                    return res
                # MIN50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[0])])
                result[int(result_save_index)] = min(tmp_history)

            elif calculate == RuleUtil.calculate_type[4]:
                # UBALA
                result[int(result_save_index)] = RuleUtil.ubala(tmp_data_list)
            elif calculate == RuleUtil.calculate_type[5]:
                # AVGDIFF
                result[int(result_save_index)] = RuleUtil.avgdiff(tmp_data_list)
            elif calculate == RuleUtil.calculate_type[6]:
                if len(data_index) != 1:
                    log4p.logs("MAX/MIN50运算数据长度必须为1,错误数据为:\t" + str(item))
                    return res
                # MAX/MIN50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[0])])
                result[int(result_save_index)] = RuleUtil.max_min(tmp_history)
            elif calculate == RuleUtil.calculate_type[7]:
                if len(tmp_data_list) != 2:
                    log4p.logs("数据长度必须为2,错误数据为:\t" + str(item))
                    return res
                # DIFF
                result[int(result_save_index)] = RuleUtil.diff(tmp_data_list[0], tmp_data_list[1])

        for i in range(0, len(result)):
            if i in used_index:
                result[i] = result[i] * 1.0


        #log4p.logs("计算结果:\t" + str(result))
        # res['data'] = DataUtil.expand_arr_2_demical(result)
        res['status'] = True
        res['data'] = DataUtil.expand_arr_2_float32_decimal(result)
        #log4p.logs("返回的res:\t" + str(res))
        return res


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


