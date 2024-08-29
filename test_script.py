history_data = []

def add_data(new_data):
    history_data.append(new_data)
    if len(history_data) > 50:
        history_data.pop(0)

# 示例用法
for i in range(100):
    add_data([i, i*2, i*3])
    tmp = []
    for data in history_data:
        tmp.append(data[0])


    print(max(tmp))
    print(history_data)
# print(history_data)