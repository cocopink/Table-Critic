import pickle
import subprocess
import fire
import os
import sys
from tqdm import tqdm
sys.path.insert(0, 'critic/TableQA')
sys.path.insert(0, 'refine/TableQA')
sys.path.insert(0, '.')
from tools import CRITIC_TREE_JSON
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
    thought_results_dir: str = "",
    refine_results_dir: str = "",
    base_url="http://localhost:11434/v1",
    openai_api_key="EMPTY",
    model_name="qwen3:14b",
    first_n=-1,
    n_proc=1,
    chunk_size=1,
    use_controller: bool = True,
    use_clarifier: bool = True,
    use_verifier: bool = False,
    router_variant: str = "",
):
    # Auto-switch results directory based on mode
    mode_dir = "new" if use_controller else "orig"
    model_dir = f"wikitq/{model_name}"
    if not thought_results_dir:
        thought_results_dir = f"results/{mode_dir}/thought/{model_dir}"
    if not refine_results_dir:
        refine_results_dir = f"results/{mode_dir}/refine/{model_dir}"

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

    # 启用token日志
    gpt_llm.set_token_log_dir(refine_results_dir, run_tag="wikitq_refine")

    if use_controller:
        # Use controller-based refinement
        print("Using controller-based refinement...")
        print(f"Clarifier enabled: {use_clarifier}")
        print(f"Router variant: {router_variant or 'none (standard FULL)'}")

        # Initialize critic tree
        # critic_tree_init(file_path=CRITIC_TREE_JSON)

        # Process samples with controller
        refined_samples = []
        route_stats = {"SKIP": 0, "LITE": 0, "FULL": 0}
        for idx, sample in tqdm(enumerate(all_samples), total=len(all_samples), desc="Controller-based refinement"):
            # Skip None samples (failed in thought stage)
            if sample is None:
                print(f"Warning: Sample {idx} is None (failed in thought stage), skipping...")
                continue

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
                use_verifier=use_verifier,
                router_variant=router_variant or None,
            )
            # 若要控制debug 在controller 中DEBUG变量的修改
            refined_samples.append(refined_sample)

            if router_variant:
                route = refined_sample.get("_route", "UNKNOWN")
                route_stats[route] = route_stats.get(route, 0) + 1

        refine_list = refined_samples

        # Print route distribution
        if router_variant and any(v > 0 for v in route_stats.values()):
            total = sum(route_stats.values())
            print(f"\n[ROUTER] Route distribution ({router_variant}):")
            for route, count in route_stats.items():
                if count > 0:
                    pct = count / total * 100
                    print(f"  {route}: {count} ({pct:.1f}%)")

    else:
        # Use original method
        print("Using original refinement method...")

        critic_tree_init(file_path=CRITIC_TREE_JSON)
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
            use_verifier=use_verifier,
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

    # 汇总并保存token统计
    token_usage = LLM.collect_token_usage(
        refine_results_dir,
        output_path=os.path.join(refine_results_dir, "token_usage.json")
    )
    if token_usage["total_tokens"] > 0:
        print(f"\nRefine Stage Token Usage:")
        print(f"  Input Tokens:  {token_usage['input_tokens']:,}")
        print(f"  Output Tokens: {token_usage['output_tokens']:,}")
        print(f"  Total Tokens: {token_usage['total_tokens']:,} ({token_usage['api_calls']} calls)")
    else:
        print(f"\nRefine Stage: no new API calls (all cached).")


if __name__ == "__main__":
    fire.Fire(main)