import pickle

def read_pkl(pkl_file):
    with open(pkl_file, 'rb') as pkl_f:
        data = pickle.load(pkl_f)
    return data

if __name__ =="__main__":
    file = "/home/ubuntu/mnt/lx/Table-Critic/results/thought/wikitq/qwen3:32b/final_result.pkl"
    data = read_pkl(file)
    print(type(data),data[0])