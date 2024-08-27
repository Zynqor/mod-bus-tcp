# ModBusTcp

## 环境配置

1. python版本：3.8
2. 依赖包
   ```shell
    pip install pymodbus -i https://pypi.doubanio.com/simple/
    pip install pyserial -i https://pypi.doubanio.com/simple/
    pip install pandas -i https://pypi.doubanio.com/simple/
    pip install tornado -i https://pypi.doubanio.com/simple/
    ```

## 配置文件

### As Slave

> 是指本系统作为modbustcp作为从机供其他modbustcp主机访问的设置

#### 内容介绍

1. ip:本机作为modbustcp从机的ip
2. port: 作为modbustcp从机的端口
3. id: 作为modbustcp从机的id
4. 线圈（co）：1个字节,co_len代表对应类型的有几个
5. 离散输入（di）：1个字节,di_len代表对应类型的有几个
6. 保持寄存器（hr）：2个字节,hr_len代表对应类型的有几个
7. 输入寄存器（ir）：2个字节,ir_len代表对应类型的有几个

### Serial

> 针对本系统串口资源的设置

#### 内容介绍

1. COM:本系统自带的串口号,和linux串口文件内容对应,无需修改
2. band:波特率
3. activate:是否开启该串口,1为开启,0为不开启
4. save_reg: 存放在As Slave的哪种寄存器中,可选co,di,hr,ir
5. cmd:串口轮询访问的命令(不含crc部分)
6. read_start:返回的指令读取起始位,从0开始计数
7. read_len:读取长度
8. save_start: 存放起始地址
9. save_len: 数据长度
10. freq:查询频率

### As Master

> 针对本系作为主机,连接的其他modbustcp从机的设置

#### 内容介绍

1. ip:从机ip
2. port:从机端口
3. id:从机id
4. save_reg: 存放在As Slave的哪种寄存器中,可选co,di,hr,ir,如有多个英文逗号分割,建议与reg一致
5. save_start: 存放起始地址
6. save_len: 数据长度
7. reg:取目标的哪些寄存器,英文逗号分割,可选co,di,hr,ir
8. reg_len:读取目标寄存器的长度,英文逗号分割,长度与reg对应
9. freq:查询频率
10. reg_addr:读取目标寄存器的起始地址,英文逗号分割,长度与reg对应