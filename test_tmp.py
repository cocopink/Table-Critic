import pickle
from pkl import read_pkl

# 读取 final_result.pkl
data = read_pkl("/home/ubuntu/mnt/lx/M_TC/Table-Critic/results/thought_100/tabfact/qwen3:14b/final_result.pkl")

# 检查第一个样本
print("数据类型:", type(data))
print("样本数量:", len(data))
print("\n第一个样本的键:", data[0].keys())
print("chain 长度:", len(data[0]["chain"]))
print("最后一个操作:", data[0]["chain"][-1]["operation_name"])
print("答案列表:", data[0]["chain"][-1]["parameter_and_conf"])
print("第一个答案:", data[0]["chain"][-1]["parameter_and_conf"][0][0])
print("标签:", data[0]["label"])
print("完整 thought:")
print(data[0]["chain"][-1]["thought"])

# 检查前10个样本的答案
print("\n前10个样本的答案和标签:")
for i in range(min(10, len(data))):
    answer = data[i]["chain"][-1]["parameter_and_conf"][0][0]
    label = data[i]["label"]
    print(f"样本 {i}: 答案='{answer}', 标签={label}")
