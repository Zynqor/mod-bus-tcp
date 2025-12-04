import json
import os
import threading
from Util.log4p import log4p


class StorageManager:
    def __init__(self, filepath="lightning_cache.json"):
        self.filepath = filepath
        self.lock = threading.Lock()

        # 确保文件存在，不存在则创建空字典
        if not os.path.exists(self.filepath):
            self.save_data({})

    def load_data(self):
        """
        加载缓存数据
        :return: dict
        """
        with self.lock:
            try:
                if os.path.exists(self.filepath):
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        log4p.logs(f"✓ 成功加载雷击数据缓存: {self.filepath}")
                        return data
                return {}
            except Exception as e:
                log4p.logs(f"✗ 加载缓存失败: {e}, 将使用空数据")
                return {}

    def save_data(self, data):
        """
        原子写入数据到 eMMC
        1. 写入 .tmp 文件
        2. 调用 fsync 强制刷盘
        3. 重命名覆盖原文件
        """
        with self.lock:
            tmp_file = self.filepath + ".tmp"
            try:
                # 1. 写入临时文件
                with open(tmp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                    # 2. 强制刷入磁盘 (关键步骤：防止断电数据停留在RAM)
                    f.flush()
                    os.fsync(f.fileno())

                # 3. 原子替换 (Windows/Linux下 os.replace 也是原子的)
                os.replace(tmp_file, self.filepath)
                # log4p.logs(f"数据已安全写入磁盘") # 调试时可开启，生产环境建议注释以免刷屏
            except Exception as e:
                log4p.logs(f"✗ 严重错误：写入磁盘失败: {e}")
                # 尝试清理残余的 tmp 文件
                if os.path.exists(tmp_file):
                    os.remove(tmp_file)