# from zai import ZhipuAiClient
from openai import OpenAI
import os

# client = ZhipuAiClient(api_key="$GLM_API_KEY")  # 请填写您自己的 API Key
client = OpenAI(
        # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为: api_key="sk-xxx",
        api_key=os.getenv("GLM_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
    )
response = client.chat.completions.create(
    model="glm-4.5-air",
    messages=[
        {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
        {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
        {"role": "user", "content": "智谱开放平台"}
    ],
    # thinking={
    #     "type": "enabled",    # 启用深度思考模式
    # },
    max_tokens=65536,          # 最大输出 tokens
    temperature=1.0           # 控制输出的随机性
)

# 获取完整回复
print(response.choices[0].message)