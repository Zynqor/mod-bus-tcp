# -*- coding: UTF-8 -*
import json
class ConfigUtil:

    # 读取文件,返回值是字典
    @staticmethod
    def get_config_json(fileName):
        if 'json' not in fileName:
            return '格式错误'
        # 读取JSON文件
        with open(fileName) as f:
            data = json.load(f)
            return data

    # 获取json文件的所有的key
    @staticmethod
    def get_json_key(fileName):
        data = ConfigUtil.get_config_json(fileName)
        if '格式错误' == data:
            return '格式错误'
        return data.keys()

    # 修改或新增键值到文件中,key是字符串,value是值
    @staticmethod
    def add_update_info(fileName, key, value):
        data = ConfigUtil.get_config_json(fileName)
        if '格式错误' == data:
            return '格式错误'
        data[key] = value
        with open(fileName, 'w') as f:
            f.write(json.dumps(data))

    # 删除文件中key对应的值
    @staticmethod
    def add_update_info(fileName, key):
        data = ConfigUtil.get_config_json(fileName)
        if '格式错误' == data:
            return '格式错误'
        keys = ConfigUtil.get_json_key(fileName)
        if key not in keys:
            return '不存在的key'
        del data[key]
        with open(fileName, 'w') as f:
            f.write(json.dumps(data))
