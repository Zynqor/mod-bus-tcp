from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext, ModbusSlaveContext
from pymodbus.server import StartAsyncTcpServer
import asyncio

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
        print("Already run modbus tcp server\n")
        asyncio.run(self.server_start(), debug=True)  # pragma: no cover
