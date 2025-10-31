from pymodbus.server import StartSerialServer
from pymodbus.datastore import ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer

class SerialServer:
    """
    一个同步阻塞的 Modbus RTU (RS485) 服务器。
    它的 run() 方法会永久阻塞，因此必须在一个独立的线程中运行。
    """
    def __init__(self, context, port, baudrate):
        # 将传入的原始 context 字典包装成 pymodbus 需要的 Server Context
        self.context = ModbusServerContext(slaves=context, single=False)
        self.port = port
        self.baudrate = baudrate

    def run(self):
        """
        启动服务器并永远运行。
        """
        print(f"================[Threaded] SerialServer (RTU) is running on {self.port}====================")
        StartSerialServer(
            context=self.context,
            framer=ModbusRtuFramer, # 串口 RTU 模式必须使用 RtuFramer
            port=self.port,
            baudrate=self.baudrate,
            timeout=1
        )