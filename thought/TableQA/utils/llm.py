import openai
from openai import OpenAI
import time
import numpy as np

class LLM:
    def __init__(self, model_name, key, base):
        self.model_name = model_name
        self.key = key
        self.base = base
        # 添加token统计
        self.input_tokens = 0
        self.output_tokens = 0
        self._token_log_dir = None
        self._run_tag = ""

    def set_token_log_dir(self, log_dir, run_tag=""):
        """设置token日志目录和运行标签，启用后每次API调用会自动追加写入"""
        import os
        self._token_log_dir = log_dir
        self._run_tag = run_tag
        os.makedirs(log_dir, exist_ok=True)

    def _log_token_usage(self, prompt_tokens, completion_tokens):
        """将单次API调用的token用量追加写入日志文件"""
        import json, os, time
        if self._token_log_dir is None:
            return
        tag = self._run_tag or "unknown"
        log_path = os.path.join(self._token_log_dir, f"token_{tag}_{os.getpid()}.jsonl")
        entry = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "pid": os.getpid(),
            "model": self.model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_model_options(
        self,
        temperature=0,
        per_example_max_decode_steps=150,
        per_example_top_p=1,
        n_sample=1,
    ):
        options = dict(
            temperature=temperature,
            n=n_sample,
            top_p=per_example_top_p,
            max_tokens=per_example_max_decode_steps,
        )

        # 只有非GPT模型才添加enable_thinking参数
        # GPT模型不支持这个参数，但Qwen等模型需要
        if not self.model_name.startswith('gpt-'):
            options['extra_body'] = {"enable_thinking": False}  # 显式关闭思考模式

        return options

    def _create_mock_response(self):
        """创建模拟响应对象，兼容API响应的属性访问"""
        class MockChoice:
            def __init__(self, content):
                self.message = type('obj', (object,), {'content': content})()

        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice("PLACEHOLDER")]
                self.usage = None

        return MockResponse()

    def generate_plus_with_score(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        messages = [
            {
                "role": "system",
                "content": "I will give you some examples, you need to follow the examples and complete the text, and no other content.",
            },
            {"role": "user", "content": prompt},
        ]
        gpt_responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        client = OpenAI(
            api_key=self.key,
            base_url=self.base,
            timeout=600.0,  # 10分钟超时，适应单线程处理
        )
        while gpt_responses is None:
            try:
                print("1 options",options)
                gpt_responses = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stop=end_str,
                    **options
                )
                error = None
            except Exception as e:
                print(str(e), flush=True)
                # 检查是否是内容审核错误（不可恢复）
                if "data_inspection_failed" in str(e) or "inappropriate content" in str(e):
                    print(f"[WARNING] Content moderation error, skipping with PLACEHOLDER...", flush=True)
                    gpt_responses = self._create_mock_response()
                    error = None
                    break  # 不要重试内容审核错误
                elif "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    gpt_responses = self._create_mock_response()
                    error = None
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    gpt_responses = self._create_mock_response()
                else:
                    error = str(e)
                    time.sleep(60)
                retry_num += 1
        if error:
            raise Exception(error)

        # 检查响应是否包含错误
        if hasattr(gpt_responses, 'error'):
            print(f"API返回错误: {gpt_responses.error}", flush=True)
            raise Exception(f"API Error: {gpt_responses.error}")

        # 检查是否有 choices 字段
        if not hasattr(gpt_responses, 'choices') or not gpt_responses.choices:
            print(f"API响应无效: {gpt_responses}", flush=True)
            raise Exception("Invalid API response: no choices")

        # 提取token使用信息
        if hasattr(gpt_responses, 'usage') and gpt_responses.usage:
            self.input_tokens += gpt_responses.usage.prompt_tokens
            self.output_tokens += gpt_responses.usage.completion_tokens
            self._log_token_usage(gpt_responses.usage.prompt_tokens, gpt_responses.usage.completion_tokens)

        results = []
        for i, res in enumerate(gpt_responses.choices):
            text = res.message.content
            fake_conf = (len(gpt_responses.choices) - i) / len(
                gpt_responses.choices
            )
            results.append((text, np.log(fake_conf)))

        return results

    def generate_plus_with_score_final_query(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {"role": "user", "content": prompt},
        ]
        gpt_responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        client = OpenAI(
            api_key=self.key,
            base_url=self.base,
            timeout=600.0,  # 10分钟超时，适应单线程处理
        )
        while gpt_responses is None:
            try:
                print("2 options",options)
                gpt_responses = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stop=end_str,
                    **options
                )
                error = None
            except Exception as e:
                print(str(e), flush=True)
                # 检查是否是内容审核错误（不可恢复）
                if "data_inspection_failed" in str(e) or "inappropriate content" in str(e):
                    print(f"[WARNING] Content moderation error, skipping with PLACEHOLDER...", flush=True)
                    gpt_responses = self._create_mock_response()
                    error = None
                    break  # 不要重试内容审核错误
                elif "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    gpt_responses = self._create_mock_response()
                    error = None
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    gpt_responses = self._create_mock_response()
                else:
                    error = str(e)
                    time.sleep(60)
                retry_num += 1
        if error:
            raise Exception(error)

        # 检查响应是否包含错误
        if hasattr(gpt_responses, 'error'):
            print(f"API返回错误: {gpt_responses.error}", flush=True)
            raise Exception(f"API Error: {gpt_responses.error}")

        # 检查是否有 choices 字段
        if not hasattr(gpt_responses, 'choices') or not gpt_responses.choices:
            print(f"API响应无效: {gpt_responses}", flush=True)
            raise Exception("Invalid API response: no choices")

        # 提取token使用信息
        if hasattr(gpt_responses, 'usage') and gpt_responses.usage:
            self.input_tokens += gpt_responses.usage.prompt_tokens
            self.output_tokens += gpt_responses.usage.completion_tokens
            self._log_token_usage(gpt_responses.usage.prompt_tokens, gpt_responses.usage.completion_tokens)

        results = []
        for i, res in enumerate(gpt_responses.choices):
            text = res.message.content
            fake_conf = (len(gpt_responses.choices) - i) / len(
                gpt_responses.choices
            )
            results.append((text, np.log(fake_conf)))

        return results

    def generate(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        options["n"] = 1
        result = self.generate_plus_with_score(prompt, options, end_str)[0][0]
        return result

    def get_token_usage(self):
        """返回当前进程的token使用统计"""
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.input_tokens + self.output_tokens
        }

    def save_token_usage(self, filepath):
        """保存token使用统计到文件"""
        import json
        import time
        usage = self.get_token_usage()
        usage['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        usage['model'] = self.model_name
        with open(filepath, 'w') as f:
            json.dump(usage, f, indent=2)
        print(f"Token usage saved to {filepath}")

    @staticmethod
    def collect_token_usage(log_dir, output_path=None):
        """汇总所有进程的token日志文件，返回总统计并可选保存到文件"""
        import json, os, glob, time
        total_input = 0
        total_output = 0
        total_calls = 0
        model = "unknown"
        log_files = glob.glob(os.path.join(log_dir, "token_*.jsonl"))
        for lf in log_files:
            with open(lf, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    total_input += entry.get("prompt_tokens", 0)
                    total_output += entry.get("completion_tokens", 0)
                    total_calls += 1
                    if model == "unknown":
                        model = entry.get("model", "unknown")
        result = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "model": model,
            "log_files_count": len(log_files),
            "api_calls": total_calls,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }
        total = total_input + total_output
        if total > 0:
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(result, f, indent=2)
                print(f"Token usage saved to {output_path}")
            print(f"Token summary: {total_calls} API calls, "
                  f"input={total_input:,}, output={total_output:,}, total={total:,}")
        return result
