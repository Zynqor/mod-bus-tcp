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
## 目录介绍
1. exec:最终完整版安装包,包含剩下的文件
2. modbus:串口读取,modbustcp服务端,modbustcp客户端的模块
3. Web:控制网页
4. Util:项目使用的工具类

## 配置介绍
> 以下配置都可以在网关管理的页面上实现控制,下面对于参数的介绍

### Slave.json

> 是指本系统作为modbustcp作为从机供其他modbustcp主机访问的设置

#### 内容介绍

1. ip:本机作为modbustcp从机的ip
2. port: 作为modbustcp从机的端口
3. id: 作为modbustcp从机的id
4. 线圈（co）：1个bit,co_len代表对应类型的有几个
5. 离散输入（di）：1个bit,di_len代表对应类型的有几个
6. 保持寄存器（hr）：2个字节,hr_len代表对应类型的有几个
7. 输入寄存器（ir）：2个字节,ir_len代表对应类型的有几个

### Serial.json

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
9. save_rule: 保存规则
10. freq:查询频率

### master.json

> 针对本系作为主机,连接的其他modbustcp从机的设置

#### 内容介绍

1. ip:从机ip
2. port:从机端口
3. id:从机id
4. save_reg: 存放在As Slave的哪种寄存器中,可选co,di,hr,ir,如有多个英文分号分割,建议与reg一致
5. save_start: 存放起始地址
6. save_rule: 保存规则
7. reg:取目标的哪些寄存器,英文分号分割,可选co,di,hr,ir
8. reg_len:读取目标寄存器的长度,英文分号分割,长度与reg对应
9. freq:查询频率
10. reg_addr:读取目标寄存器的起始地址,英文分号分割,长度与reg对应