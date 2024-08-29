import json


class RuleUtil:

    @staticmethod
    def avg(data_list):
        """
        计算平均值
        :param data_list: 数据列表
        :return:
        """
        return sum(data_list) / len(data_list)

    @staticmethod
    def ratio(data1,data2):
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

        return max(tmp) / avg * 100

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
        最大值和最小值的差
        :param data_list:
        :return:
        '''
        return max(data_list) - min(data_list)

    @staticmethod
    def diff(arg1,arg2):
        """
        相减
        :param arg1: 参数1
        :param arg2: 参数2
        :return:
        """
        return arg1 - arg2

    
    @staticmethod
    def handle_rule(history_data,save_rule):
        """
        处理规则
        :param history_data: 历史数据
        :param save_rule: 保存的规则
        :return:
        """
        res = []
        rule = json.loads(save_rule)
        for item in rule:
            print(f"data_index: {item['data_index']}")
            print(f"calculate: {item['calculate']}")
            print(f"data_save_index: {item['data_save_index']}")
            print(f"result_save_index: {item['result_save_index']}")
            print(f"calculate_desc: {item['calculate_desc']}")
            print()

if __name__ == '__main__':
    history_data = [[50, 100, 150], [51, 102, 153], [52, 104, 156], [53, 106, 159], [54, 108, 162], [55, 110, 165], [56, 112, 168], [57, 114, 171], [58, 116, 174], [59, 118, 177], [60, 120, 180], [61, 122, 183], [62, 124, 186], [63, 126, 189], [64, 128, 192], [65, 130, 195], [66, 132, 198], [67, 134, 201], [68, 136, 204], [69, 138, 207], [70, 140, 210], [71, 142, 213], [72, 144, 216], [73, 146, 219], [74, 148, 222], [75, 150, 225], [76, 152, 228], [77, 154, 231], [78, 156, 234], [79, 158, 237], [80, 160, 240], [81, 162, 243], [82, 164, 246], [83, 166, 249], [84, 168, 252], [85, 170, 255], [86, 172, 258], [87, 174, 261], [88, 176, 264], [89, 178, 267], [90, 180, 270], [91, 182, 273], [92, 184, 276], [93, 186, 279], [94, 188, 282], [95, 190, 285], [96, 192, 288], [97, 194, 291], [98, 196, 294], [99, 198, 297]]
    with open("../exec/serial.json", "r") as f:
        config_data = json.load(f)
    save_rule = config_data[1]['save_rule']
    RuleUtil.handle_rule(history_data, save_rule)
