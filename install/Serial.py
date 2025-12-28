import json
import sys
from platform import system
import random
import math  # [新增] 用于 sqrt 计算
import serial.tools.list_ports
import time
import threading
from binascii import *
from crcmod import *
import struct

from Util.RuleUtil import RuleUtil
from Util.log4p import log4p
from Util.DataUtil import DataUtil
from Util.StorageManager import StorageManager


class Serial(threading.Thread):
    def __init__(self, serial_info, context, as_slave_id):
        super().__init__()
        self.running = True
        self.as_slave_id = as_slave_id
        self.context = context

        self.port = serial_info['com']
        self.band = int(serial_info['band'])
        self.save_reg = serial_info['save_reg']
        self.cmd = serial_info['cmd']
        self.read_start = int(serial_info['read_start'], 16)
        self.read_len = int(serial_info['read_len'])
        self.save_start = int(serial_info['save_start'], 16)
        self.save_rule = serial_info['save_rule']
        self.freq = float(serial_info['freq'])
        try:
            self.serial = serial.Serial(port=self.port, baudrate=self.band, timeout=0.2)
            log4p.logs(f"✓ 串口 {self.port} 打开成功")
        except Exception as e:
            log4p.logs(f"✗ 串口 {self.port} 打开失败: {e}")
            self.running = False
            raise
        self.history_data = []
        log4p.logs(f"启动串口主机轮询服务 on {self.port}...")
        with open("correct_data.json", "r") as f:
            self.correct_data = json.load(f)
        self.counter = 0
        self.storage = StorageManager("lightning_cache.json")
        self.lightning_cache = self.storage.load_data()
        self.processing_buffer = b''

    def stop(self):
        self.running = False

    def run(self):
        log4p.logs(f"串口线程开始运行: {self.port}")
        while self.running:
            self.send_serial()
            self.read_serial()
            time.sleep(self.freq)

    def read_serial(self):
        try:
            if self.serial.in_waiting:
                new_data = self.serial.read(self.serial.in_waiting)
                self.processing_buffer += new_data

                if len(new_data) > 0:
                    hex_raw = ''.join('{:02X}'.format(byte) for byte in new_data)
                    log4p.logs(f"[RX-RAW] 收到:{hex_raw} | 缓存总长:{len(self.processing_buffer)}")

                while len(self.processing_buffer) >= 5:
                    addr = self.processing_buffer[0]
                    func = self.processing_buffer[1]
                    expected_len = 0

                    if func in [0x03, 0x04]:
                        if len(self.processing_buffer) < 3: break
                        data_len = self.processing_buffer[2]
                        expected_len = 3 + data_len + 2
                    elif func >= 0x80:
                        expected_len = 5
                    else:
                        log4p.logs(f"[RX-ERR] 未知功能码 {func:02X}, 丢弃头部1字节")
                        self.processing_buffer = self.processing_buffer[1:]
                        continue

                    if len(self.processing_buffer) < expected_len:
                        break

                    packet_bytes = self.processing_buffer[:expected_len]
                    packet_hex = ''.join('{:02X}'.format(byte) for byte in packet_bytes)

                    if self.check_crc(packet_hex):
                        log4p.logs(f"[RX-OK] 切出有效包: {packet_hex}")
                        self.processing_buffer = self.processing_buffer[expected_len:]
                        self.handle_res(packet_hex)
                    else:
                        log4p.logs(f"[RX-FAIL] CRC校验失败: {packet_hex}")
                        self.processing_buffer = self.processing_buffer[1:]

        except Exception as e:
            log4p.logs(f"读取异常: {e}")
            self.processing_buffer = b''

    def send_serial(self):
        cmds = self.cmd.split(';')
        for cmd in cmds:
            send_cmd = cmd + self.get_crc(cmd)
            log4p.logs("Tx:\t" + str(send_cmd))
            self.serial.write(bytes.fromhex(send_cmd))
            time.sleep(0.8)

    def handle_res(self, packet):
        addr = packet[0:2]
        func_code = packet[2:4]

        if func_code == "04":
            if addr in self.correct_data.get("devices", {}):
                log4p.logs(f"[BIZ] 地址 {addr} 匹配成功，开始处理业务...")
                self.process_arrester_data(packet, addr)
            else:
                log4p.logs(f"[WARN] 地址 {addr} 不在配置文件 correct_data.json 中，被忽略！")

        elif func_code == "03":
            self.process_voltage_data(packet)

    def process_arrester_data(self, packet, addr):
        """
        [最终修正版]
        1. 严格按照图片证据: 所有数据(Float/Int)均为 "Low Word First" (CDAB) 格式。
        2. 先进行字序交换，再进行解析。
        3. 电流用 Float32, 次数/时间用 Int32。
        4. [新增] 更新 Ir 和 Ic (阻容比) 的计算公式。
        """
        payload = packet[6:-4]

        def parse_swapped_float(hex_s):
            b = unhexlify(hex_s)
            swapped = b[2:4] + b[0:2]
            return struct.unpack('>f', swapped)[0]

        def parse_swapped_int32(hex_s):
            b = unhexlify(hex_s)
            swapped = b[2:4] + b[0:2]
            return struct.unpack('>i', swapped)[0]

        def int32_to_registers_swapped(val):
            b = struct.pack('>i', int(val))
            high_word = struct.unpack('>H', b[0:2])[0]
            low_word = struct.unpack('>H', b[2:4])[0]
            return [low_word, high_word]

        try:
            raw_iq_a   = parse_swapped_float(payload[72:80])
            # raw_iq_b = parse_swapped_float(payload[8:16])
            # raw_iq_c = parse_swapped_float(payload[16:24])

            raw_cnt_a   = parse_swapped_int32(payload[24:32])
            # raw_cnt_b = parse_swapped_int32(payload[32:40])
            # raw_cnt_c = parse_swapped_int32(payload[40:48])

            raw_time_a = parse_swapped_int32(payload[48:56])
            # raw_time_b = parse_swapped_int32(payload[56:64])
            # raw_time_c = parse_swapped_int32(payload[64:72])

            phases_data = [
                {'name': 'A', 'iq': raw_iq_a, 'cnt': raw_cnt_a, 'time': raw_time_a}
                # {'name': 'B', 'iq': raw_iq_b, 'cnt': raw_cnt_b, 'time': raw_time_b},
                # {'name': 'C', 'iq': raw_iq_c, 'cnt': raw_cnt_c, 'time': raw_time_c}
            ]

            device_cache = self.lightning_cache.get(addr, {})
            cache_changed = False
            calculated_values = {}

            for p in phases_data:
                name = p['name']
                iq = p['iq']  # 全电流 (It)

                # =================== [核心计算公式更新] ===================
                # 1. 阻性电流 (Ir)
                # 公式: Ir = It * 0.91859 * A (A 为 0.996~1.005 随机值)
                rand_A = random.uniform(0.996, 1.005)
                ir = iq * 0.91859 * rand_A

                # 2. "相容性电流" (实际为阻容比 Ir/Ic_real)
                # 原始容性电流分量 Ic_real = sqrt(It^2 - Ir^2)
                # 目标值 = Ir / Ic_real
                ic_val = 0.0
                try:
                    # 防止根号下负数 (理论上 iq > ir，但浮点数可能有误差)
                    val_sq = iq ** 2 - ir ** 2
                    if val_sq > 0:
                        ic_real = math.sqrt(val_sq)
                        if ic_real > 0.000001:  # 防止除以0
                            ic_val = ir / ic_real
                        else:
                            ic_val = 0.0  # 容性分量极小，比值趋于无穷或0处理
                    else:
                        ic_val = 0.0  # 数据异常 (Ir > It)
                except Exception:
                    ic_val = 0.0

                # 更新 ic 变量以便后续写入 "Capacitive_Current" 对应的寄存器
                ic = ic_val
                # =========================================================

                cached_cnt = device_cache.get(f"{name}_cnt", 0)
                cached_time = device_cache.get(f"{name}_time", 0)
                final_cnt = cached_cnt
                final_time = cached_time

                if iq > 0.02:
                    if p['cnt'] != cached_cnt or p['time'] != cached_time:
                        final_cnt = p['cnt']
                        final_time = p['time']
                        device_cache[f"{name}_cnt"] = final_cnt
                        device_cache[f"{name}_time"] = final_time
                        cache_changed = True

                calculated_values[f"{name}_Total_Current"] = iq
                calculated_values[f"{name}_Resistive_Current"] = ir
                calculated_values[f"{name}_Capacitive_Current"] = ic  # 这里写入的是计算后的比值
                calculated_values[f"{name}_Strike_Count"] = final_cnt
                calculated_values[f"{name}_Strike_Time"] = final_time

            if cache_changed:
                self.lightning_cache[addr] = device_cache
                self.storage.save_data(self.lightning_cache)

            device_config = self.correct_data.get("devices", {}).get(addr, {})
            if not device_config: return

            slave_ctx = self.context[self.as_slave_id]

            for key, value in calculated_values.items():
                if key in device_config:
                    item_cfg = device_config[key]
                    k = float(item_cfg.get("k", 1))
                    b = float(item_cfg.get("b", 0))
                    target_addr_str = item_cfg.get("addr")

                    if target_addr_str:
                        target_addr = int(target_addr_str, 16)

                        # if "Count" in key or "Time" in key:
                        if "Time" in key:
                            final_val = int(value * k + b)
                            regs = int32_to_registers_swapped(final_val)
                            slave_ctx.setValues(3, target_addr, regs)
                        else:
                            final_val = value * k + b
                            # 使用 little_endian=True (CDAB) 转发给 TCP
                            regs = DataUtil.expand_arr_2_float32_decimal([final_val], little_endian=True)
                            slave_ctx.setValues(3, target_addr, regs)

        except Exception as e:
            log4p.logs(f"[ERR] 处理避雷器数据出错 设备{addr}: {e}")

    def process_voltage_data(self, packet):
        try:
            addr_hex = packet[0:2]
            raw_bytes = unhexlify(packet)
            if len(raw_bytes) < 5: return

            byte_len = raw_bytes[2]
            data_bytes = raw_bytes[3:-2]

            # [修改] 现在是2字节(16bit)数据，所以检查是否为2的倍数
            if len(data_bytes) != byte_len or len(data_bytes) % 2 != 0:
                log4p.logs(f"[WARN] 电压数据长度异常: 声明{byte_len}, 实际{len(data_bytes)}")
                return

            all_groups = self.correct_data.get("voltage_monitor_groups", {})
            config_list = all_groups.get(addr_hex, [])

            if not config_list:
                log4p.logs(f"[INFO] 电压设备 {addr_hex} 未在 monitor_groups 中配置，忽略。")
                return

            slave_ctx = self.context[self.as_slave_id]
            parsed_count = 0

            # [修改] 循环步长改为 2，解析 16 位整数 (Big Endian)
            for i in range(0, len(data_bytes), 2):
                cfg_idx = i // 2
                if cfg_idx >= len(config_list): break

                # 提取 2 字节
                chunk = data_bytes[i: i + 2]

                # 解析 Int16 (假设无符号 Big Endian >H, 根据例子 0001 -> 1)
                val_int = struct.unpack('>H', chunk)[0]

                # 转为浮点数，以便后续按 float 写入 Modbus TCP
                val = float(val_int)

                item_cfg = config_list[cfg_idx]
                target_addr = int(item_cfg["addr"], 16)
                k = float(item_cfg.get("k", 1))
                b = float(item_cfg.get("b", 0))

                final_val = val * k + b

                # 写入 Modbus TCP: 转回 4字节 Float32 (CDAB 格式)
                regs = DataUtil.expand_arr_2_float32_decimal([final_val], little_endian=True)
                slave_ctx.setValues(3, target_addr, regs)
                parsed_count += 1

            log4p.logs(f"[BIZ] 电压设备 {addr_hex} 处理完成: 转发 {parsed_count} 个数据 (Int16->Float32)")

        except Exception as e:
            log4p.logs(f"[ERR] 处理电压数据出错: {e}")

    def get_crc(self, read):
        crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        data = read.replace(" ", "")
        readcrcout = hex(crc16(unhexlify(data))).upper()
        str_list = list(readcrcout)
        if len(str_list) < 6:
            str_list.insert(2, '0' * (6 - len(str_list)))
        crc_data = "".join(str_list)
        return crc_data[4:] + crc_data[2:4]

    def check_crc(self, read):
        data = read.replace(" ", "")
        a = data[0:len(data) - 4]
        b = data[len(data) - 4:]
        if self.get_crc(a).upper() == b.upper():
            return True
        else:
            return False
