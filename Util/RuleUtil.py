import json

from Util.DataUtil import DataUtil
from Util.log4p import log4p


class RuleUtil:
    calculate_type = ['AVG', 'RATIO', 'MAX50', 'MIN50', 'UBALA', 'AVGDIFF', 'MAX/MIN50', 'DIFF', 'None']

    @staticmethod
    def avg(data_list):
        """
        计算平均值
        :param data_list: 数据列表
        :return:
        """
        return sum(data_list) / len(data_list)

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
            return data1 / data2

    @staticmethod
    def ubala(data_list):
        """
        (MAX(arg1-avg,arg2-avg,arg3-avg)/avg)*100%
        :param data_list: 数据列表
        :return:
        """
        tmp = []
        avg = RuleUtil.avg(data_list)
        for data in data_list:
            tmp.append(abs(data - avg))

        return max(tmp) / avg

    @staticmethod
    def avgdiff(data_list):
        '''
        arg1 - (arg1+...+argn)/n
        :param data_list:
        :return:
        '''

        return data_list[0] - RuleUtil.avg(data_list)

    @staticmethod
    def max_min(data_list):
        '''
        最大值和最小值的比值
        :param data_list:
        :return:
        '''
        return max(data_list) / min(data_list)

    @staticmethod
    def diff(arg1, arg2):
        """
        相减
        :param arg1: 参数1
        :param arg2: 参数2
        :return:
        """
        return arg1 - arg2

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

            log4p.logs(
                f"data_index: {data_index}\t" + f"calculate: {calculate}" + f"data_save_index: {data_save_index}\t" + f"result_save_index: {result_save_index}\t" + f"calculate_desc: {calculate_desc}")
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
                if calculate != "None":
                    if int(result_save_index) > res_len:
                        res_len = int(result_save_index)

            if isinstance(int(result_save_index), int):
                log4p.logs("result_save_index必须为整数,错误数据为:\t" + str(item))
                return res
        result = [0] * res_len
        res['data'] = result

        for item in rule:
            data_index = item['data_index']
            calculate = item['calculate']
            data_save_index = item['data_save_index']
            result_save_index = item['result_save_index']
            calculate_desc = item['calculate_desc']
            tmp_data_list = []

            for i in range(0, len(data_save_index)):
                # 把
                result[int(result_save_index[i])] = history_data[-1][int(data_index[i])]
                tmp_data_list.append(history_data[-1][int(data_index[i])])

            if calculate == "None":
                pass
            elif calculate == RuleUtil.calculate_type[0]:
                result[int(result_save_index)] = RuleUtil.avg(tmp_data_list)
            elif calculate == RuleUtil.calculate_type[1]:
                result[int(result_save_index)] = RuleUtil.ratio(tmp_data_list[0], tmp_data_list[1])
            elif calculate == RuleUtil.calculate_type[2]:
                # MAX50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[i])])

                result[int(result_save_index)] = max(tmp_history)
            elif calculate == RuleUtil.calculate_type[3]:
                # MIN50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[i])])
                result[int(result_save_index)] = min(tmp_history)
            elif calculate == RuleUtil.calculate_type[4]:
                # UBALA
                result[int(result_save_index)] = RuleUtil.ubala(tmp_data_list)
            elif calculate == RuleUtil.calculate_type[5]:
                # AVGDIFF
                result[int(result_save_index)] = RuleUtil.avgdiff(tmp_data_list)
            elif calculate == RuleUtil.calculate_type[6]:
                # MAX/MIN50
                tmp_history = []
                for tmp_data in history_data:
                    tmp_history.append(tmp_data[int(data_index[i])])
                result[int(result_save_index)] = RuleUtil.max_min(tmp_history)
            elif calculate == RuleUtil.calculate_type[7]:
                # DIFF
                result[int(result_save_index)] = RuleUtil.diff(tmp_data_list[0], tmp_data_list[1])


if __name__ == '__main__':
    history_data = [[50, 100, 150], [51, 102, 153], [52, 104, 156], [53, 106, 159], [54, 108, 162], [55, 110, 165],
                    [56, 112, 168], [57, 114, 171], [58, 116, 174], [59, 118, 177], [60, 120, 180], [61, 122, 183],
                    [62, 124, 186], [63, 126, 189], [64, 128, 192], [65, 130, 195], [66, 132, 198], [67, 134, 201],
                    [68, 136, 204], [69, 138, 207], [70, 140, 210], [71, 142, 213], [72, 144, 216], [73, 146, 219],
                    [74, 148, 222], [75, 150, 225], [76, 152, 228], [77, 154, 231], [78, 156, 234], [79, 158, 237],
                    [80, 160, 240], [81, 162, 243], [82, 164, 246], [83, 166, 249], [84, 168, 252], [85, 170, 255],
                    [86, 172, 258], [87, 174, 261], [88, 176, 264], [89, 178, 267], [90, 180, 270], [91, 182, 273],
                    [92, 184, 276], [93, 186, 279], [94, 188, 282], [95, 190, 285], [96, 192, 288], [97, 194, 291],
                    [98, 196, 294], [99, 198, 297]]
    with open("../exec/serial.json", "r") as f:
        config_data = json.load(f)
    save_rule = config_data[1]['save_rule']
    RuleUtil.handle_rule(history_data, save_rule)
