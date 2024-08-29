import json
import threading

from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock

from Serial import Serial
from TcpServer import TcpServer
from TcpSlave import TcpSlave
import time


def logs(string):
    # 以写模式打开文件，如果文件不存在，则创建文件
    with open('logs.txt', "a") as f:
        # 把字符串写入文件
        f.write(str(time.asctime()) + '\t' + string + "\n")
        f.flush()


def config_handle():
    # 读取本地配置文件
    with open("slave.json", "r") as f:
        Sheet3 = json.load(f)
    # 读取本地配置文件
    with open("serial.json", "r") as f:
        Sheet2 = json.load(f)
    with open("master.json", "r") as f:
        Sheet1 = json.load(f)

    logs('read config successfully!')
    logs("As Slave Read Success!\t" + str(Sheet1))
    logs("Serial Read Success!\t" + str(Sheet2))
    logs("As Master Read Success!\t" + str(Sheet3))
    return Sheet1, Sheet2, Sheet3


if __name__ == '__main__':
    Sheet1, Sheet2, Sheet3 = config_handle()

    as_slave_id = int(Sheet1['id'], 16)
    as_slave_port = str(Sheet1['port'])
    as_slave_host = Sheet1['ip']

    for reg in Sheet1['reg']:
        if reg['reg'] == 'di':
            di_start = int(reg['reg_addr'], 16)
            di_len = int(reg['len'])
        elif reg['reg'] == 'hr':
            hr_start = int(reg['reg_addr'], 16)
            hr_len = int(reg['len'])
        elif reg['reg'] == 'co':
            co_start = int(reg['reg_addr'], 16)
            co_len = int(reg['len'])
        elif reg['reg'] == 'ir':
            ir_start = int(reg['reg_addr'], 16)
            ir_len = int(reg['len'])

    context = {
        as_slave_id: ModbusSlaveContext(
            co=ModbusSequentialDataBlock(co_start, [00] * co_len),
            di=ModbusSequentialDataBlock(di_start, [00] * di_len),
            hr=ModbusSequentialDataBlock(hr_start, [00] * hr_len),
            ir=ModbusSequentialDataBlock(ir_start, [00] * ir_len),
        )
    }

    server = TcpServer(context, as_slave_host, as_slave_port)
    t = threading.Thread(target=server.run)
    t.start()
    # server.context[0x01].setValues(1, 0x11, [00] * 8)

    slaves = []
    print(Sheet3)

    for slave in Sheet3:
        s = TcpSlave(slave, server, as_slave_id)
        s.start()
        slaves.append(s)

    serials = []
    for serial_info in Sheet2:
        if serial_info['activate'] == '0':
            continue
        s = Serial(serial_info, server, as_slave_id)
        s.start()
        serials.append(s)

    while True:
        # res = slaves[0].get_slave_data()
        # print(res)
        time.sleep(0.2)
