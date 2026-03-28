import pickle
import subprocess
import fire
import os
import sys
from tqdm import tqdm
sys.path.append('critic/TableQA')
sys.path.append('refine/TableQA')
sys.path.append('.')
from utils.read_pkl import read_pkl
from utils.extract_step import return_incorrect_max_step
from utils.llm import LLM
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *
from tools import read_pkl, critic_tree_init
from utils.controller import controller_main_loop

def main(
    thought_results_dir: str = "results/thought_100/wikitq/qwen3:14b",
    refine_results_dir: str = "results/refine_100_control/wikitq/qwen3:14b",
    base_url="http://localhost:11434/v1",
    openai_api_key="EMPTY",
    model_name="qwen3:14b",
    first_n=-1,
    n_proc=1,
    chunk_size=1,
    use_controller: bool = True,
    use_clarifier: bool = True,
):

    result_pkl = os.path.join(thought_results_dir, "final_result.pkl")

    if first_n != -1:
        all_samples = read_pkl(result_pkl)[:first_n]
    else:
        all_samples = read_pkl(result_pkl)

    gpt_llm = LLM(
        model_name=model_name,
        key=openai_api_key,
        base=base_url
    )

    # Create results directory structure
    os.makedirs(refine_results_dir, exist_ok=True)
    cache_dir = os.path.join(refine_results_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)

    if use_controller:
        # Use controller-based refinement
        print("Using controller-based refinement...")
        print(f"Clarifier enabled: {use_clarifier}")
        
        # Initialize critic tree
        critic_tree_init(file_path="critic/TableQA/tools/few_shot_critic.json")
        
        # Process samples with controller
        refined_samples = []
        for idx, sample in tqdm(enumerate(all_samples), total=len(all_samples), desc="Controller-based refinement"):
            sample_id = sample.get('id', idx)
            
            # Use Controller main loop with cache support
            refined_sample = controller_main_loop(
                sample,
                llm=gpt_llm,
                llm_options=gpt_llm.get_model_options(
                    temperature=0,
                    per_example_max_decode_steps=2048,
                    per_example_top_p=1
                ),
                max_iterations=2,
                cache_dir=cache_dir,
                sample_idx=idx,
                use_clarifier=use_clarifier,
                thought_results_dir=thought_results_dir,
            )
            # 若要控制debug 在controller 中DEBUG变量的修改
            refined_samples.append(refined_sample)
        
        refine_list = refined_samples

    else:
        # Use original method
        print("Using original refinement method...")

        critic_tree_init(file_path="critic/TableQA/tools/few_shot_critic.json")
        refine_list = judge_critic_refine_with_cache_mp(
            all_samples,
            llm=gpt_llm,
            llm_options=gpt_llm.get_model_options(
                temperature=0.0, per_example_max_decode_steps=2048, per_example_top_p=1.0
            ),
            strategy="top",
            cache_dir=cache_dir,
            n_proc=n_proc,
            chunk_size=chunk_size,
        )

    # Calculate accuracy
    acc = wikitq_match_func_for_samples(refine_list)
    print("Accuracy:", acc)

    # Save results
    with open(os.path.join(refine_results_dir, "result.txt"), "w") as f:
        f.write(f'Accuracy: {acc}\n')

    pickle.dump(
        refine_list, open(os.path.join(refine_results_dir, "final_result.pkl"), "wb")
    )

    # Save accuracy
    with open(os.path.join(refine_results_dir, "acc.txt"), "w") as f:
        f.write(f"Refine Stage Accuracy: {acc}\n")


if __name__ == "__main__":
    fire.Fire(main)