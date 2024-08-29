import threading
import time

lock = threading.Lock()

class log4p:

    @staticmethod
    def logs(string):
        with open('logs.txt', "a") as f:
            log = str(time.asctime()) + '\t' + string + "\n"
            print(log)
            with lock:
                f.write(log)
                f.flush()