import requests
import json
import os

# 获取 API 密钥
api_key = os.environ.get("VOLCENGINE_API_KEY")
if not api_key:
    raise ValueError("VOLCENGINE_API_KEY 未设置")

# DeepSeek V3 API 配置
url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
data = {
    "model": "deepseek-v3-250324",
    "messages": [
        {
            "role": "system",
            "content": "你是一个内容审核助手。你的任务是将以下文本分类为 'appropriate'（合适）或 'inappropriate'（不合适）。仅回复一个单词：'appropriate' 或 'inappropriate'。"
        },
        {
            "role": "user",
            "content": "文本: Have a great day!"
        }
    ]
}

# 发送请求
try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    print(f"API 响应: {result}")
    choice = result['choices'][0]['message']['content']
    print(f"分类结果: {choice}")
except requests.exceptions.RequestException as e:
    print(f"调用 DeepSeek V3 API 失败: {e}")