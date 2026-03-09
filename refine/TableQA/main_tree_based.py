import pickle
import subprocess
import fire
import os
import sys
import copy
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
from agents import (
    InitialReasoner,
    JudgeAgent,
    CriticAgent,
    RefinerAgent,
    ValidatorAgent,
    MultiAgentOrchestrator,
    DisputeHandler
)

def main(
    thought_results_dir: str = "results/thought/wikitq",
    refine_results_dir: str = "results/refine/wikitq",
    base_url="",
    openai_api_key="EMPTY",
    model_name="qwen2.5-72b-instruct",
    first_n=-1,
    n_proc=10,
    chunk_size=5,
    use_multi_agent: bool = True,
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

    if use_multi_agent:
        # Use new multi-agent framework
        print("Using multi-agent framework for refinement...")

        # Initialize agents
        reasoner = InitialReasoner(llm=gpt_llm)
        judge = JudgeAgent(llm=gpt_llm)
        critic = CriticAgent(llm=gpt_llm)
        refiner = RefinerAgent(llm=gpt_llm)
        validator = ValidatorAgent(llm=gpt_llm)

        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(llm=gpt_llm)
        orchestrator.register_agent(reasoner)
        orchestrator.register_agent(judge)
        orchestrator.register_agent(critic)
        orchestrator.register_agent(refiner)
        orchestrator.register_agent(validator)

        # Create dispute handler
        dispute_handler = DisputeHandler(critic, refiner, validator, judge)

        # Process samples
        refined_samples = []
        for sample in all_samples:
            sample_id = sample.get('id', 'unknown')

            # Save original chain (first incorrect chain)
            original_chain = copy.deepcopy(sample.get('chain', []))

            # Check if already correct
            judge_sample = judge.judge_sample(sample, task_type="TableQA")
            if judge_sample.get('judge') == '[Correct]':
                refined_samples.append(judge_sample)
                continue

            # Run dispute resolution
            refined_sample, dispute_history = dispute_handler.resolve_dispute(
                judge_sample,
                error_route='random'
            )

            # Save thinking chains
            final_chain = copy.deepcopy(refined_sample.get('chain', []))

            # Create save data
            save_data = {
                'sample_id': sample_id,
                'original_chain': original_chain,
                'final_chain': final_chain,
                'dispute_history': dispute_history,
                'original_conclusion': '[Incorrect]',
                'final_conclusion': refined_sample.get('judge', '[Incorrect]')
            }

            # Save to cache
            cache_path = os.path.join(cache_dir, f'case_{sample_id}.pkl')
            pickle.dump(save_data, open(cache_path, 'wb'))

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