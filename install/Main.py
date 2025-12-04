import asyncio
import json
import threading
from SerialServer import SerialServer
from pymodbus.datastore import ModbusSlaveContext, ModbusSequentialDataBlock

from Serial import Serial
from TcpServer import TcpServer

from Util.log4p import log4p


def config_handle():
    # 读取本地配置文件
    with open("slave.json", "r") as f:
        Sheet3 = json.load(f)
    # 读取本地配置文件
    with open("serial.json", "r") as f:
        Sheet2 = json.load(f)
    with open("master.json", "r") as f:
        Sheet1 = json.load(f)

    log4p.logs('Config Read Success!')
    log4p.logs("As Slave Read Success!\t" + str(Sheet1))
    log4p.logs("Serial Read Success!\t" + str(Sheet2))
    log4p.logs("As Master Read Success!\t" + str(Sheet3))
    return Sheet1, Sheet2, Sheet3


if __name__ == '__main__':
    ## 避雷器分支
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

    # --- 2. 创建唯一的、共享的“中央数据仓库” (Context) ---
    shared_context = {
        as_slave_id: ModbusSlaveContext(
            co=ModbusSequentialDataBlock(co_start, [0] * co_len),
            di=ModbusSequentialDataBlock(di_start, [0] * di_len),
            hr=ModbusSequentialDataBlock(hr_start, [0] * hr_len),
            ir=ModbusSequentialDataBlock(ir_start, [0] * ir_len),
        )
    }

    # --- 3. 启动所有数据采集/主机轮询线程 ---
    # 这些线程都将数据写入上面创建的 shared_context

    # a) 启动 TCP 主机轮询线程 (TcpSlave)
    # log4p.logs("Starting TCP Master (TcpSlave) polling threads...")
    # slaves = []
    # for slave_config in Sheet3:  # Sheet3 是 master.json
    #     # 【重要】将 shared_context 传递给 TcpSlave 实例
    #     # 您需要像修改 Serial.py 一样，修改 TcpSlave.py 来接收 context
    #     s = TcpSlave(slave_config, shared_context, as_slave_id)
    #     s.start()
    #     slaves.append(s)

    # b) 启动 Serial 主机轮询线程 (Serial)
    log4p.logs("Starting Serial Master (Serial) polling threads...")
    serials = []
    for serial_info in Sheet2:  # Sheet2 是 serial.json
        if serial_info['activate'] == '0':
            continue
        # 将共享的 context 传递给 Serial 实例
        s = Serial(serial_info, shared_context, as_slave_id)
        s.start()
        serials.append(s)

    # --- 4. 启动所有作为【从机】的服务器 ---

    # a) 启动 RTU (RS485) 从机服务器 (放入后台线程)

    serial_slave_server = SerialServer(shared_context, Sheet2[3]['com'], Sheet2[3]['band'])
    serial_slave_thread = threading.Thread(target=serial_slave_server.run)
    serial_slave_thread.daemon = True
    serial_slave_thread.start()

    # b) 实例化您的 TCP 从机服务器
    tcp_slave_server = TcpServer(shared_context, as_slave_host, as_slave_port)

    # --- 5. 在主线程中运行您的 TCP 从机服务器并保持程序运行 ---
    log4p.logs(f"Starting SLAVE TCP Server on {as_slave_host}:{as_slave_port} in the main thread...")
    try:
        # 使用 asyncio.run() 启动并运行您的异步 TCP 服务器
        asyncio.run(tcp_slave_server.run())
    except KeyboardInterrupt:
        log4p.logs("Shutting down all services...")
    except Exception as e:
        log4p.logs(f"An error occurred in the main loop: {e}")
