# 连接到从机
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.137.117', port=15020)
# 读取输入寄存器
result = client.read_coils(address=0x11, count=8, slave=0x01)
print(result)


# 关闭连接
client.close()