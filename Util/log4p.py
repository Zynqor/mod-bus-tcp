import os
import threading
import time
import datetime

lock = threading.Lock()


class log4p:
    file_name = None

    @staticmethod
    def delete_exist_file_list(file_list):
        for file_path in file_list:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted.")
            else:
                print(f"File {file_path} does not exist.")

    @staticmethod
    def logs(string):
        now = datetime.datetime.now()
        if log4p.file_name is None or log4p.file_name == '':
            date_string = now.strftime("%Y-%m-%d")
            log4p.file_name = f"log_{date_string}.txt"
        if now.hour == 18 and now.minute == 51:
            date_string = now.strftime("%Y-%m-%d")
            log4p.file_name = f"log_{date_string}.txt"
            file_paths = []
            for i in range(3, 6):
                past_date_string = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                file_path = f"log_{past_date_string}.txt"
                file_paths.append(file_path)

            log4p.delete_exist_file_list(file_paths)

        with open(log4p.file_name, "a") as f:
            log = str(time.asctime()) + '\t' + string + "\n"
            print(log)
            with lock:
                f.write(log)
                f.flush()


if __name__ == '__main__':
    log4p.logs("hello")
