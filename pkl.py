import pickle

def read_pkl(pkl_file):
    with open(pkl_file, 'rb') as pkl_f:
        data = pickle.load(pkl_f)
    return data

if __name__ == "__main__":
    file = "/home/ubuntu/mnt/lx/new_TC/Table-Critic/results/thought/tabfact/gpt-5.4/cache/case-0.pkl"
    data = read_pkl(file)
    print(type(data),len(data),data[1])