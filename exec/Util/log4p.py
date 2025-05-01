import os
import threading
import time
import datetime

lock = threading.Lock()


class log4p:
    file_name = None

    @staticmethod
    def delete_exist_file_list(file_list):
        """删除指定的文件列表"""
        for file_path in file_list:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"File {file_path} deleted.")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
            else:
                print(f"File {file_path} does not exist.")

    @staticmethod
    def clean_old_logs():
        """清理当前目录下除今天以外的所有日志文件"""
        now = datetime.datetime.now()
        today = now.strftime("%Y-%m-%d")
        today_log = f"log_{today}.txt"

        # 获取当前目录下的所有以log_开头且以.txt结尾的文件
        log_files = [f for f in os.listdir('.') if f.startswith('log_') and f.endswith('.txt')]

        # 筛选出不是今天的日志文件
        old_logs = [f for f in log_files if f != today_log]

        if old_logs:
            print(f"Found {len(old_logs)} old log files to delete.")
            log4p.delete_exist_file_list(old_logs)

    @staticmethod
    def logs(string):
        """写入日志，并清理旧日志文件"""
        # 每次写日志时都检查并清理旧日志
        log4p.clean_old_logs()

        now = datetime.datetime.now()
        if log4p.file_name is None or log4p.file_name == '':
            date_string = now.strftime("%Y-%m-%d")
            log4p.file_name = f"log_{date_string}.txt"

        # 检查是否需要更新日志文件名（新的一天）
        current_date = now.strftime("%Y-%m-%d")
        current_log_name = f"log_{current_date}.txt"
        if log4p.file_name != current_log_name:
            log4p.file_name = current_log_name

        with open(log4p.file_name, "a") as f:
            log = str(time.asctime()) + '\t' + string + "\n"
            print(log)
            with lock:
                f.write(log)
                f.flush()


if __name__ == '__main__':
    log4p.logs("hello")