# -*- coding: UTF-8 -*
import pandas as pd


class ExcelUtil:
    """
    pip install pandas
    pip install xlrd
    pip install openpyxl
    pip install pyxlsb
    """

    # 读取Excel文件
    @staticmethod
    def read_all_lines(filename, sheet="Sheet1"):
        df = pd.read_excel(filename, sheet_name=sheet)
        # 将读取的数据按行转换成list
        rows = df.values.tolist()
        return rows


    # 读取Excel文件
    @staticmethod
    def read_lines(filename, start, num, sheet="Sheet1"):
        """
        读取第start行开始,之后的num行
        :param filename: 文件名
        :param start: 起始行
        :param num: 读取行数
        :param sheet: 表单,默认为sheet1
        :return:
        """
        # 使用skiprows参数跳过前面的行数
        # 使用nrows参数读取指定的行数
        df = pd.read_excel(filename, skiprows=start - 1, nrows=num, sheet_name=sheet)
        # 将读取的数据按行转换成list
        rows = df.values.tolist()
        return rows

    @staticmethod
    def get_column_name(filename, sheet="Sheet1"):
        """
        获取列名
        :param filename:
        :param sheet:
        :return:
        """
        df = pd.read_excel(filename, sheet_name=sheet)
        columns = df.columns.tolist()
        return columns

    @staticmethod
    def get_column_by_name(filename, columnName, sheet="Sheet1"):
        """
        根据列名获取列的数据
        :param filename:
        :param sheet:
        :return:
        """
        df = pd.read_excel(filename, sheet_name=sheet)
        columns = df[columnName].values.tolist()
        return columns

    @staticmethod
    def get_column_by_index(filename, index, sheet="Sheet1"):
        """
        根据index获取列的数据
        :param filename:
        :param sheet:
        :param index: 可以是list,可以是字符串,可以是int,字符串和int表示列的index,list表示你想要哪些列的index
        :return: 返回结果是二维数组,每个列组装为一维数组,多个列拼在一起
        """
        indices = []
        if isinstance(index, str):
            indices.append(int(index))
        if isinstance(index, int):
            indices.append(index)
        if isinstance(index, list):
            indices = index
        df = pd.read_excel(filename, sheet_name=sheet)
        columns = df.iloc[:, indices].transpose()
        return columns.values.tolist()

    @staticmethod
    def del_row_by_index(filename, index, sheet="Sheet1"):
        """

        :param filename:
        :param sheet:
        :param index: int
        :return:
        """

        if not isinstance(index, int):
            raise TypeError("Parameter index must be an int.")
        df = pd.read_excel(filename, sheet_name=sheet)
        df.drop(index, inplace=True)
        if "xls" in filename and "xlsx" not in filename:
            filename = filename + "x"
        df.to_excel(filename, index=False)

    @staticmethod
    def del_column_by_index(filename, index, sheet="Sheet1"):
        """

        :param filename:
        :param sheet:
        :param index: int
        :return:
        """
        if not isinstance(index, int):
            raise TypeError("Parameter index must be an int.")
        df = pd.read_excel(filename, sheet_name=sheet)
        df.drop(df.columns[index], axis=1, inplace=True)
        # 不支持xls写出
        if "xls" in filename and "xlsx" not in filename:
            filename = filename + "x"
        df.to_excel(filename, index=False)

    # 读取Excel文件
    @staticmethod
    def read_lines(filename, start, num, sheet="Sheet1"):
        """
        读取第start行开始,之后的num行
        :param filename: 文件名
        :param start: 起始行
        :param num: 读取行数
        :param sheet: 表单,默认为sheet1
        :return:
        """
        # 使用skiprows参数跳过前面的行数
        # 使用nrows参数读取指定的行数
        df = pd.read_excel(filename, skiprows=start - 1, nrows=num, sheet_name=sheet)
        # 将读取的数据按行转换成list
        rows = df.values.tolist()
        return rows
