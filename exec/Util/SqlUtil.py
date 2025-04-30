# -*- coding: UTF-8 -*
import mysql.connector

# pip install mysql-connector-python
class MySQLUtil:
    def __init__(self, user, password, host, database):
        self.user = user
        self.password = password
        self.host = host
        self.database = database
        self.cnx = mysql.connector.connect(user=self.user, password=self.password, host=self.host,
                                           database=self.database)
        self.cursor = self.cnx.cursor()

    def query(self, table, column, condition):
        """

        :param table: 字符串,表名
        :param column: list,查询列名
        :param condition:condition对象
        :return:
        """
        query = self._get_query_sql(table, column, condition)
        print("执行语句:", query)
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print("查询出错：", e)

    def insert(self, table, data):
        """

        :param table: 表名
        :param data: 字典类型,标识插入的数据,key为列名value为值
        :return:
        """
        # 生成和数据等长的 "%s,%s"
        placeholders = ', '.join(['%s'] * len(data))
        # 将data的key用,连接起来
        columns = ', '.join(data.keys())
        # 将数据生成元组
        values = tuple(data.values())
        query = "INSERT INTO {} ({}) VALUES ({})".format(table, columns, placeholders)
        print("执行语句:", query)
        try:
            self.cursor.execute(query, values)
            self.cnx.commit()
        except Exception as e:
            print("插入出错：", e)

    def update(self, table, data, condition):
        """

        :param table: 表名
        :param data:  数据和列名的字典
        :param condition: 条件
        :return:
        """
        set_clause = ', '.join(['{} = %s'.format(k) for k in data.keys()])
        condition_clause = condition.builder()
        values = tuple(list(data.values()) + list(condition.values()))
        query = "UPDATE {} SET {} {}".format(table, set_clause, condition_clause)
        print("执行语句:", query)
        try:
            self.cursor.execute(query, values)
            self.cnx.commit()
        except Exception as e:
            print("更新出错：", e)

    def delete(self, table, condition):
        """

        :param table:表名
        :param condition:条件
        :return:
        """
        condition_clause = condition.builder()
        values = tuple(condition.values())
        query = "DELETE FROM {} {}".format(table, condition_clause)
        print("执行语句:", query)
        try:
            self.cursor.execute(query, values)
            self.cnx.commit()
        except Exception as e:
            print("删除出错：", e)

    def close(self):
        self.cursor.close()
        self.cnx.close()

    def _get_query_sql(self, table, column, condition):
        col = ""
        if isinstance(column, list):
            if len(column) == 0:
                col = "*"
            else:
                col = ",".join(column)
        else:
            raise TypeError("Parameter value must be list.")
        query = "SELECT {} FROM {} ".format(col, table)
        query = query + condition.builder()
        return query

    def describe(self, table):
        self.cursor.execute(r"DESCRIBE {}".format(table))
        result = self.cursor.fetchall()
        return result


class Condition:

    def __init__(self):
        self._gt = []
        self._gte = []
        self._lt = []
        self._lte = []
        self._in = []
        self._eq = []
        self._like = []

    def gt(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._gt.append({"column": column, "value": value})

    def gte(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._gte.append({"column": column, "value": value})

    def lt(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._lt.append({"column": column, "value": value})

    def lte(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._lte.append({"column": column, "value": value})

    def like(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._like.append({"column": column, "value": value})

    def eq(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, str):
            raise TypeError("Parameter value must be str.")
        self._eq.append({"column": column, "value": value})

    def inn(self, column, value):
        if not isinstance(column, str):
            raise TypeError("Parameter column must be str.")
        if not isinstance(value, list):
            raise TypeError("Parameter value must be list.")
        self._in.append({"column": column, "value": value})

    def builder(self):
        res = r'WHERE 1=1'
        if len(self._gt) != 0:
            for i in self._gt:
                res = res + r' AND ' + i["column"] + r' > ' + r"'" + i["value"] + r"'"
        if len(self._gte) != 0:
            for i in self._gte:
                res = res + r' AND ' + i["column"] + r' >= ' + r"'" + i["value"] + r"'"
        if len(self._lt) != 0:
            for i in self._lt:
                res = res + r' AND ' + i["column"] + r' < ' + r"'" + i["value"] + r"'"
        if len(self._lte) != 0:
            for i in self._lte:
                res = res + r' AND ' + i["column"] + r' <= ' + r"'" + i["value"] + r"'"
        if len(self._eq) != 0:
            for i in self._eq:
                res = res + r' AND ' + i["column"] + r' = ' + r"'" + i["value"] + r"'"
        if len(self._in) != 0:
            for j in self._in:
                res = res + r' AND ' + j["column"] + r' in ('
                for i in j["value"]:
                    res = res + r"'" + i + r"',"
                res = res[0:len(res) - 1] + ")"
        if len(self._like) != 0:
            for i in self._like:
                res = res + r' AND ' + i["column"] + r' like ' + r"'" + i["value"] + r"'"
        return res
