import asyncio
import threading
import time

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartAsyncTcpServer
from pymodbus.client import ModbusTcpClient


class TcpServer:

    def __init__(self, context, host, port):
        self.context = context
        self.host = host
        self.port = port

    async def server_create(self):
        self.server = await StartAsyncTcpServer(
            context=ModbusServerContext(slaves=self.context, single=False),
            address=(self.host, self.port)
        )

    async def server_start(self):
        await self.server_create()

    def run(self):
        asyncio.run(self.server_start(), debug=True)  # pragma: no cover


if __name__ == '__main__':
    context = {
        0x01: ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0x01, [17] * 10),

            hr=ModbusSequentialDataBlock(0x21, [17] * 10),
            co=ModbusSequentialDataBlock(0x11, [17] * 10),
            ir=ModbusSequentialDataBlock(0x31, [17] * 10),
        )
    }

    server = TcpServer(context, '127.0.0.1', 5020)
    t = threading.Thread(target=server.run)
    t.start()

    # 连接到从机
    client = ModbusTcpClient('127.0.0.1', port=5020)

    # 读取输入寄存器
    result = client.read_coils(address=0x11, count=8, slave=0x01)
    print(result.getBit(0))

    server.context[0x01].setValues(1, 0x11, [00] * 8)

    # 读取输入寄存器
    result = client.read_coils(address=0x11, count=8, slave=0x01)
    print(result.getBit(0))

    # 关闭连接
    client.close()
