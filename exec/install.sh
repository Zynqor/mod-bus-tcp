#!/bin/bash
# 定义要修改权限的文件列表
files=("run.sh" "modify_net1_conf.sh" "modify_net2_conf.sh")
# 修改文件权限为 777
for file in "${files[@]}"; do
    chmod 777 "$file"
done
# 向指定文件添加内容
echo "/data/run.sh &" >> /etc/htset/autorun
# 执行命令
pip install --no-index --find-links=/data/packages -r requirements.txt
reboot

