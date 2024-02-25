# 连接到从机
from pymodbus.client import ModbusTcpClient
import threading
import time


class TcpSlave(threading.Thread):
    def __init__(self, slave, server, as_slave_id):
        super().__init__()
        self.server = server
        self.running = True
        self.host = slave[0]
        self.port = int(slave[1])
        self.as_slave_id = as_slave_id
        self.id = slave[2]
        if ',' in str(slave[3]):
            self.reg_type = slave[3].split(',')
        else:
            self.reg_type = []
            self.reg_type.append(slave[3])

        if ',' in str(slave[4]):
            self.reg_len = slave[4].split(',')
        else:
            self.reg_len = []
            self.reg_len.append(slave[4])

        if ',' in str(slave[5]):
            self.reg_addr = slave[5].split(',')
        else:
            self.reg_addr = []
            self.reg_addr.append(slave[5])

        # 保存寄存器与长度
        if ',' in str(slave[6]):
            self.save_start = slave[6].split(',')
        else:
            self.save_start = []
            self.save_start.append(slave[6])

        if ',' in str(slave[7]):
            self.save_len = slave[7].split(',')
        else:
            self.save_len = []
            self.save_len.append(slave[7])

        self.freq = slave[8]

        self.co = None
        self.di = None
        self.hr = None
        self.ir = None
        self.client = ModbusTcpClient(host=self.host, port=self.port)

    def get_slave_data(self):
        co = self.co if self.co is not None else ''
        di = self.di if self.di is not None else ''
        hr = self.hr if self.hr is not None else ''
        ir = self.ir if self.ir is not None else ''
        return {
            'co': co,
            'di': di,
            'ir': ir,
            'hr': hr
        }

    def close_slave(self):
        self.client.close()

    def run(self):
        while self.running:

            for i in range(0, len(self.reg_type)):
                reg = self.reg_type[i]
                if reg == 'co':
                    self.co = self.client.read_coils(address=int(self.reg_addr[i], 16), count=int(self.reg_len[i]),
                                                     slave=int(self.id, 16)).bits
                    self.server.context[self.as_slave_id].setValues(1, int(self.save_start[i], 16),
                                                                    self.co[0:int(self.save_len[i])])

                elif reg == 'di':
                    self.di = self.client.read_discrete_inputs(address=int(self.reg_addr[i], 16),
                                                               count=int(self.reg_len[i]), slave=int(self.id, 16)).bits
                    self.server.context[self.as_slave_id].setValues(2, int(self.save_start[i], 16),
                                                                    self.di[0:int(self.save_len[i])])

                elif reg == 'hr':
                    self.hr = self.client.read_holding_registers(address=int(self.reg_addr[i], 16),
                                                                 count=int(self.reg_len[i]),
                                                                 slave=int(self.id, 16)).registers
                    self.server.context[self.as_slave_id].setValues(3, int(self.save_start[i], 16),
                                                                    self.hr[0:int(self.save_len[i])])

                elif reg == 'ir':
                    self.ir = self.client.read_input_registers(address=int(self.reg_addr[i], 16),
                                                               count=int(self.reg_len[i]),
                                                               slave=int(self.id, 16)).registers
                    self.server.context[self.as_slave_id].setValues(4, int(self.save_start[i], 16),
                                                                    self.ir[0:int(self.save_len[i])])

            time.sleep(float(self.freq))
        print("slave thread stopped.")

    def stop(self):
        self.running = False
