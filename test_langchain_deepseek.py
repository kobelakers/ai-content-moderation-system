import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# 检查 API 密钥
if "VOLCENGINE_API_KEY" not in os.environ:
    raise ValueError("VOLCENGINE_API_KEY 未设置")

# 配置 DeepSeek V3 API
llm = ChatOpenAI(
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    openai_api_key=os.environ.get("VOLCENGINE_API_KEY"),
    model_name="deepseek-v3-250324",
    temperature=0  # 设置温度为 0，确保一致性
)

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个内容审核助手。你的任务是将以下文本分类为 'appropriate'（合适）或 'inappropriate'（不合适）。仅回复一个单词：'appropriate' 或 'inappropriate'。不要添加任何额外解释或符号。"),
    ("user", "文本: {text}")
])

# 创建链
chain = LLMChain(llm=llm, prompt=prompt)

# 测试调用
try:
    test_texts = ["Have a great day!", "I hate everyone!"]
    for text in test_texts:
        response = chain.invoke({"text": text})
        result = response['text'].strip().lower()
        print(f"文本: {text}, 分类结果: {result}")
except Exception as e:
    print(f"调用 DeepSeek V3 API 失败: {e}")