import asyncio
import threading
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartAsyncTcpServer
from pymodbus.client import ModbusTcpClient


def write_to_txt(filename, string):
    # 以写模式打开文件，如果文件不存在，则创建文件
    with open(filename, "w") as f:
        # 把字符串写入文件
        f.write(string)

class TcpServer:

    def __init__(self, context, host, port):
        self.context = context
        self.host = host
        self.port = port
        self.server = None

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



