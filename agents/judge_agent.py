# Copyright 2024 Table-Critic contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
JudgeAgent: Final arbiter for table QA answers

This agent serves as the final judge that determines whether an answer
is correct or incorrect. It can accept input from various stages including
initial reasoning and third-stage dispute resolution.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from thought.TableQA.utils.helper import table2string


class JudgeAgent:
    """
    Judge Agent for final evaluation of table QA answers.

    This agent acts as the final arbiter, evaluating answers from
    various stages and providing the final correctness judgment.
    """

    def __init__(self, llm):
        """
        Initialize the JudgeAgent.

        Args:
            llm: Language model instance for evaluation
        """
        self.llm = llm
        self.judgment_history = []

    def build_judge_prompt(
        self,
        sample: Dict[str, Any],
        include_validator_feedback: bool = False,
        include_dispute_context: bool = False
    ) -> str:
        """
        Build the prompt for judging an answer.

        Args:
            sample: Sample dictionary containing table, question, and answer
            include_validator_feedback: Whether to include validator's feedback
            include_dispute_context: Whether to include dispute resolution context

        Returns:
            Complete prompt for judgment
        """
        prompt = self._get_base_instruction()

        # Add context from various stages if available
        if include_dispute_context and 'dispute_history' in sample:
            prompt += self._format_dispute_history(sample['dispute_history'])

        if include_validator_feedback and 'validator_feedback' in sample:
            prompt += self._format_validator_feedback(sample['validator_feedback'])

        # Add the main question context
        prompt += self._get_sample_context(sample)
        prompt += "Explanation:"

        return prompt

    def _get_base_instruction(self) -> str:
        """Get the base judge instruction prompt."""
        return """You are an intelligent judge tasked with determining whether the given Prediction Answer is correct or incorrect based on the following information:

1. Original Table: The raw table data.
2. Question: The question pertaining to the table data.
3. Prediction Answer: The answer to the above question, which needs validation.
4. Additional Context: (Optional) Feedback from validators or dispute resolution process.

Instruction:
1. **Explanation**: Conduct a thorough explanation of why the Prediction Answer is correct or incorrect. Consider all available context.
2. **Conclusion**:
    - If the Prediction Answer is correct, conclude with 'Conclusion: [Correct]'.
    - If the Prediction Answer is incorrect, conclude with 'Conclusion: [Incorrect]'.

"""

    def _format_dispute_history(self, dispute_history: List[Dict[str, Any]]) -> str:
        """Format the dispute history for inclusion in the prompt."""
        if not dispute_history:
            return ""

        context = "\n--- Dispute Resolution Context ---\n"
        for i, dispute in enumerate(dispute_history, 1):
            context += f"\nRound {i}:\n"
            context += f"  Issue: {dispute.get('issue', 'N/A')}\n"
            context += f"  Resolution Attempt: {dispute.get('resolution', 'N/A')}\n"
            context += f"  Validator Opinion: {dispute.get('validator_opinion', 'N/A')}\n"
            if 'refiner_response' in dispute:
                context += f"  Refiner Response: {dispute['refiner_response']}\n"

        context += "\n--- End of Dispute Context ---\n\n"
        return context

    def _format_validator_feedback(self, validator_feedback: Dict[str, Any]) -> str:
        """Format the validator feedback for inclusion in the prompt."""
        if not validator_feedback:
            return ""

        context = "\n--- Validator Audit Results ---\n"
        context += f"Numerical Validation: {validator_feedback.get('numerical_check', 'N/A')}\n"
        context += f"Cell Location Check: {validator_feedback.get('cell_check', 'N/A')}\n"
        context += f"Logic Validation: {validator_feedback.get('logic_check', 'N/A')}\n"
        context += f"Overall Confidence: {validator_feedback.get('confidence', 'N/A')}\n"
        context += "\n--- End of Validator Results ---\n\n"
        return context

    def _get_sample_context(self, sample: Dict[str, Any]) -> str:
        """Get the context (table, question, answer) for a sample."""
        cot = "Original Table:\n/*\n"
        cot += table2string(sample['table_text']) + "\n*/\n\n"
        cot += "Question: \n" + sample['statement'] + "\n\n"

        # Get the prediction answer - try different sources
        if 'final_answer' in sample:
            answer = sample['final_answer']
        elif 'chain' in sample and len(sample['chain']) > 0:
            # Extract from chain
            table_log, _ = self._get_table_log(sample)
            answer = table_log[-1].get("cotable_result", "").lower()
        else:
            answer = "N/A"

        cot += "Prediction Answer: \n" + str(answer).lower() + "\n\n"

        return cot

    def _get_table_log(self, sample: Dict[str, Any]) -> Tuple[List, List]:
        """Get table log and thought log from sample."""
        from critic.TableQA.tools.get_info import get_table_log
        return get_table_log(sample)

    def judge_sample(
        self,
        sample: Dict[str, Any],
        llm_options: Dict[str, Any] = None,
        include_third_stage_input: bool = False
    ) -> Dict[str, Any]:
        """
        Judge a single sample.

        Args:
            sample: Sample dictionary
            llm_options: Options for LLM generation
            include_third_stage_input: Whether to include third-stage (dispute) input

        Returns:
            Sample with added judge field containing conclusion
        """
        if llm_options is None:
            llm_options = self.llm.get_model_options(
                temperature=0.0,
                per_example_max_decode_steps=500,
                per_example_top_p=1.0
            )

        # Build prompt with optional third-stage context
        prompt = self.build_judge_prompt(
            sample,
            include_validator_feedback=include_third_stage_input,
            include_dispute_context=include_third_stage_input
        )

        response = self.llm.generate(prompt, options=llm_options)

        # Extract conclusion from response
        conclusion = self._extract_conclusion(response)
        explanation = self._extract_explanation(response)

        # Add judge information to sample
        sample['judge'] = conclusion
        sample['judge_explanation'] = explanation
        sample['judge_response'] = response

        # Track judgment history
        self.judgment_history.append({
            'sample_id': sample.get('id', 'unknown'),
            'conclusion': conclusion,
            'third_stage_input': include_third_stage_input
        })

        return sample

    def _extract_conclusion(self, response: str) -> str:
        """
        Extract the conclusion from the judge response.

        Args:
            response: Full response from LLM

        Returns:
            Extracted conclusion ([Correct] or [Incorrect])
        """
        patterns = [
            r'Conclusion:\s*\[([^\]]+)\]',
            r'conclusion:\s*\[([^\]]+)\]',
            r'\[([Cc]orrect)\]',
            r'\[([Ii]ncorrect)\]'
        ]

        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                conclusion = match.group(1)
                if 'correct' in conclusion.lower():
                    return '[Correct]'
                elif 'incorrect' in conclusion.lower():
                    return '[Incorrect]'

        return '[Incorrect]'

    def _extract_explanation(self, response: str) -> str:
        """
        Extract the explanation from the judge response.

        Args:
            response: Full response from LLM

        Returns:
            Extracted explanation text
        """
        # Remove the conclusion part to get explanation
        if "Conclusion:" in response:
            parts = response.split("Conclusion:")
            return parts[0].strip()
        return response.strip()

    def judge_batch(
        self,
        samples: List[Dict[str, Any]],
        llm_options: Dict[str, Any] = None,
        use_third_stage_input: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Judge a batch of samples.

        Args:
            samples: List of sample dictionaries
            llm_options: Options for LLM generation
            use_third_stage_input: Whether to use third-stage context

        Returns:
            List of samples with judge information added
        """
        judged_samples = []
        for sample in samples:
            judged_sample = self.judge_sample(
                sample,
                llm_options,
                include_third_stage_input=use_third_stage_input
            )
            judged_samples.append(judged_sample)

        return judged_samples

    def final_arbitration(
        self,
        sample: Dict[str, Any],
        critic_conclusion: Optional[str] = None,
        validator_conclusion: Optional[str] = None,
        refiner_conclusion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform final arbitration when there are disagreements between stages.

        Args:
            sample: Sample dictionary
            critic_conclusion: Conclusion from Critic Agent
            validator_conclusion: Conclusion from Validator Agent
            refiner_conclusion: Conclusion from Refiner Agent

        Returns:
            Sample with final judge decision
        """
        # Store all conclusions for reference
        sample['critic_conclusion'] = critic_conclusion
        sample['validator_conclusion'] = validator_conclusion
        sample['refiner_conclusion'] = refiner_conclusion

        # If all agree, use that conclusion
        conclusions = [c for c in [critic_conclusion, validator_conclusion, refiner_conclusion] if c]
        if len(set(conclusions)) == 1:
            sample['judge'] = conclusions[0]
            sample['arbitration_method'] = 'unanimous'
            return sample

        # Otherwise, do full judgment with all context
        sample['dispute_history'] = []
        if critic_conclusion != refiner_conclusion:
            sample['dispute_history'].append({
                'issue': 'Critic-Refiner disagreement',
                'critic_opinion': critic_conclusion,
                'refiner_opinion': refiner_conclusion
            })

        if validator_conclusion and validator_conclusion != refiner_conclusion:
            sample['dispute_history'].append({
                'issue': 'Validator-Refiner disagreement',
                'validator_opinion': validator_conclusion,
                'refiner_opinion': refiner_conclusion
            })

        # Perform final judgment
        return self.judge_sample(sample, include_third_stage_input=True)

    def filter_by_conclusion(
        self,
        samples: List[Dict[str, Any]]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter samples into correct and incorrect lists.

        Args:
            samples: List of judged samples

        Returns:
            Tuple of (correct_samples, incorrect_samples)
        """
        correct = []
        incorrect = []

        for sample in samples:
            judge = sample.get('judge', '').strip()
            if judge == '[Correct]':
                correct.append(sample)
            else:
                incorrect.append(sample)

        return correct, incorrect

    def calculate_accuracy(self, samples: List[Dict[str, Any]]) -> float:
        """
        Calculate accuracy of judged samples.

        Args:
            samples: List of judged samples

        Returns:
            Accuracy as a float between 0 and 1
        """
        if not samples:
            return 0.0

        correct_count = sum(
            1 for s in samples
            if s.get('judge', '').strip() == '[Correct]'
        )
        return correct_count / len(samples)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about judgments made.

        Returns:
            Dictionary with judgment statistics
        """
        if not self.judgment_history:
            return {'total': 0}

        total = len(self.judgment_history)
        correct = sum(1 for j in self.judgment_history if j['conclusion'] == '[Correct]')
        with_third_stage = sum(1 for j in self.judgment_history if j['third_stage_input'])

        return {
            'total': total,
            'correct': correct,
            'incorrect': total - correct,
            'accuracy': correct / total if total > 0 else 0,
            'with_third_stage_input': with_third_stage,
            'third_stage_ratio': with_third_stage / total if total > 0 else 0
        }
