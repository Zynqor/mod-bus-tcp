import threading

import os
import pandas as pd
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock

from Serial import Serial
from TcpServer import TcpServer
from TcpSlave import TcpSlave
from Util import ExcelUtil
import serial.tools.list_ports
import time


def logs(string):
    # 以写模式打开文件，如果文件不存在，则创建文件
    with open('logs.txt', "a") as f:
        # 把字符串写入文件
        f.write(str(time.asctime()) + '\t' + string + "\n")
        f.flush()


def config_handle():
    '''
    如果没有文件就创建文件
    有文件就读取ip和端口返回
    '''
    if not os.path.exists("config.xlsx"):
        # 创建一个简单的DataFrame
        data1 = {'ip': ['192.168.0.230'],
                 'port': [10086],
                 'id': ['0x21'],
                 'di_start': ['0x00'],
                 'di_len': [10],
                 'hr_start': ['0x00'],
                 'hr_len': [10],
                 'co_start': ['0x00'],
                 'co_len': [10],
                 'ir_start': ['0x00'],
                 'ir_len': [10]
                 }
        df1 = pd.DataFrame(data1)

        data2 = {'COM': ['/dev/ttyS1', '/dev/ttyS2', '/dev/ttyS3', '/dev/ttyS4'],
                 'band': ['9600', '9600', '9600', '9600'],
                 'activate': [1, 0, 0, 1],
                 'save_reg': ['co', 'ir', 'hr', 'di'],
                 'cmd': ['FF01030002', 'FF01030002', 'FF01030002', 'FF01030002'],
                 'read_start': [2, 2, 2, 2],
                 'read_len': [6, 6, 6, 6],
                 'save_start': ['0x10', '0x20', '0x30', '0x40'],
                 'save_len': [2, 2, 2, 2],
                 'freq': ['0.2', '0.1', '0.1', '0.1']
                 }
        df2 = pd.DataFrame(data2)

        data3 = {'ip': ['192.168.0.1'],
                 'port': ['10012'],
                 'id': ['0x01'],
                 'reg': ['co,di'],
                 'reg_len': ['2,2'],
                 'reg_addr': ['0x10,0x20'],
                 'save_start': ['0x10,0x20'],
                 'save_len': ['2,2'],
                 'freq': ['0.2']
                 }
        df3 = pd.DataFrame(data3)

        # 创建一个 Pandas Excel writer 使用 XlsxWriter 引擎
        with pd.ExcelWriter('config.xlsx', engine='xlsxwriter') as writer:
            # 将 DataFrame 写入 sheet1
            df1.to_excel(writer, sheet_name='AsSlave', index=False,
                         columns=['ip', 'port', 'id', 'di_start', 'di_len', 'hr_start', 'hr_len', 'co_start', 'co_len',
                                  'ir_start', 'ir_len'])
            # 将 DataFrame 写入 sheet2
            df2.to_excel(writer, sheet_name='Serial', index=False)

            df3.to_excel(writer, sheet_name='AsMaster', index=False)

        logs("already create config util")

    Sheet1 = ExcelUtil.ExcelUtil.read_all_lines('config.xlsx', sheet='AsSlave')
    Sheet2 = ExcelUtil.ExcelUtil.read_all_lines('config.xlsx', sheet='Serial')
    Sheet3 = ExcelUtil.ExcelUtil.read_all_lines('config.xlsx', sheet='AsMaster')

    logs('read config successfully!')
    logs(str(Sheet1))
    logs(str(Sheet2))
    logs(str(Sheet3))
    return Sheet1, Sheet2, Sheet3


if __name__ == '__main__':
    Sheet1, Sheet2, Sheet3 = config_handle()

    as_slave_id = int(Sheet1[0][2], 16)
    as_slave_port = str(Sheet1[0][1])
    as_slave_host = Sheet1[0][0]
    di_start = int(Sheet1[0][3], 16)
    di_len = int(Sheet1[0][4])
    hr_start = int(Sheet1[0][5], 16)
    hr_len = int(Sheet1[0][6])
    co_start = int(Sheet1[0][7], 16)
    co_len = int(Sheet1[0][8])
    ir_start = int(Sheet1[0][9], 16)
    ir_len = int(Sheet1[0][10])

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
        if serial_info[2] == '0':
            continue
        s = Serial(serial_info)
        s.start()
        serials.append(s)

    while True:
        # res = slaves[0].get_slave_data()
        # print(res)
        time.sleep(0.2)
    slaves[0].stop()
