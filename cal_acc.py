# /home/ubuntu/mnt/lx/new_TC/Table-Critic/refine/TableFV/utils/evaluate.py
#
from  refine.TableFV.utils.evaluate import tabfact_match_func_for_samples
from  refine.TableQA.utils.evaluate import wikitq_match_func_for_samples
from pkl import read_pkl
import pickle


if __name__ == "__main__":
    data_type = "FV"
    data_file = "/home/ubuntu/mnt/lx/new_TC/Table-Critic/results/thought/tabfact/qwen3:14b/final_result.pkl" #final_results.pkl
    ans_list = read_pkl(data_file)

    if data_type == "FV":
        acc = tabfact_match_func_for_samples(ans_list)
        print("FV(tabfact) Accuracy:", acc)

        print(
            f'FV(tabfact) Accuracy: {acc}',
            file=open("result.txt", "w")
        )
    
    else:
        acc = wikitq_match_func_for_samples(ans_list)
        print("QA(wikiq) Accuracy:", acc)

        print(
            f'QA(wikiq) Accuracy: {acc}',
            file=open("result.txt", "w")
        )
