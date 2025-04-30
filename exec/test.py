import json
import time
import random
from collections import deque
import os

# 日志文件路径
LOG_FILE_PATH = "application_log.json"

# 维护最近的日志，使用双端队列限制大小
log_queue = deque(maxlen=100)


# 生成随机日志内容的函数
def generate_log_entries():
    log_types = ["INFO", "WARNING", "ERROR", "DEBUG"]
    components = ["数据采集", "网络通信", "存储系统", "处理引擎"]
    messages = [
        "正常运行中...",
        "收到数据包",
        "处理完成",
        "连接断开",
        "重新连接",
        "数据存储成功",
        "缓存刷新",
        "内存使用率: {}%".format(random.randint(10, 95))
    ]

    # 生成四条随机日志
    logs = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    for _ in range(4):
        log_type = random.choice(log_types)
        component = random.choice(components)
        message = random.choice(messages)

        log_entry = f"[{timestamp}] [{log_type}] [{component}] {message}"
        logs.append(log_entry)

    return logs


# 写入日志到文件
def write_logs_to_file(logs):
    try:
        # 将日志添加到队列
        for log in logs:
            if log not in log_queue:
                log_queue.append(log)

        # 写入文件
        with open(LOG_FILE_PATH, 'w') as f:
            json.dump(list(log_queue), f)
    except Exception as e:
        print(f"写入日志文件时出错: {e}")


# 主循环
def main():
    print(f"开始生成日志，将写入到 {LOG_FILE_PATH}")

    try:
        while True:
            # 生成新的日志
            logs = generate_log_entries()

            # 写入到文件
            write_logs_to_file(logs)

            # 每秒生成一次
            time.sleep(1)
    except KeyboardInterrupt:
        print("日志生成程序已停止")


if __name__ == "__main__":
    main()