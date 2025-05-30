import os
import json
import logging
import httpx
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pika import BlockingConnection, ConnectionParameters

# API 切换开关
use_xai_api = True  # 设置为 True 使用 xAI Grok API，False 使用 DeepSeek V3 API
use_cache = True   # 缓存开关：True 使用缓存，False 不使用缓存（便于测试 API）

# 检查 API 密钥
if use_xai_api:
    if "XAI_API_KEY" not in os.environ:
        raise ValueError("XAI_API_KEY 未设置")
    api_base = "https://api.x.ai/v1"
    api_key = os.environ.get("XAI_API_KEY")
    model_name = "grok-3-mini"  # 使用最便宜的模型
else:
    if "VOLCENGINE_API_KEY" not in os.environ:
        raise ValueError("VOLCENGINE_API_KEY 未设置")
    api_base = "https://ark.cn-beijing.volces.com/api/v3"
    api_key = os.environ.get("VOLCENGINE_API_KEY")
    model_name = "deepseek-v3-250324"

# 配置日志
logging.basicConfig(filename='moderation.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 加载缓存（仅当 use_cache 为 True 时加载）
if use_cache:
    try:
        if os.path.exists('cache.json') and os.path.getsize('cache.json') > 0:
            with open('cache.json', 'r') as f:
                cache = json.load(f)
            logging.info("缓存加载成功")
        else:
            logging.info("cache.json 不存在或为空，初始化为空字典")
            cache = {}
    except json.JSONDecodeError as e:
        logging.error(f"cache.json 解析失败: {e}，初始化为空字典")
        cache = {}
    except FileNotFoundError:
        logging.info("cache.json 不存在，初始化为空字典")
        cache = {}
else:
    cache = {}
    logging.info("不使用缓存，cache 初始化为空")

# 配置代理（仅对 xAI API 启用）
proxy_url = "http://127.0.0.1:7890" if use_xai_api else None
http_client = httpx.Client(proxy=proxy_url) if proxy_url else None

# 配置 ChatOpenAI
llm = ChatOpenAI(
    openai_api_base=api_base,
    openai_api_key=api_key,
    model_name=model_name,
    temperature=0,
    timeout=1800,
    http_client=http_client  # 传递代理客户端
)

# 创建提示模板（根据 API 选择提示词）
if use_xai_api:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Content Moderation Assistant. Your task is to classify the following text as 'appropriate' or 'inappropriate'. Text is 'inappropriate' if it contains hate speech (e.g., 'I hate everyone'), violent language (e.g., 'kill'), or explicit content. Respond only with 'appropriate' or 'inappropriate', without any additional explanation or symbols."),
        ("user", "Text: {text}")
    ])
else:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个内容审核助手。你的任务是将以下文本分类为 'appropriate'（合适）或 'inappropriate'（不合适）。'inappropriate' 包括仇恨言论（例如 'I hate everyone'）、暴力语言（例如 'kill'）、色情内容等，仅回复 'appropriate' 或 'inappropriate'，不要添加任何额外解释或符号。"),
        ("user", "文本: {text}")
    ])

# 创建链
chain = prompt | llm

# 获取审核结果
def get_moderation_result(text):
    if use_cache and text in cache:
        logging.info(f"缓存命中: 文本='{text}', 结果={cache[text]}")
        return cache[text]
    try:
        response = chain.invoke({"text": text})
        logging.info(f"API 原始响应: 文本='{text}', 响应={response}")
        result = response.content.strip().lower()
        logging.info(f"API 解析结果: 文本='{text}', 结果={result}")
        is_inappropriate = result == "inappropriate"
        if use_cache:
            cache[text] = is_inappropriate
            try:
                with open('cache.json', 'w') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                    logging.info("缓存保存成功")
            except Exception as e:
                logging.error(f"写入 cache.json 失败: {e}")
        return is_inappropriate
    except Exception as e:
        logging.error(f"调用 API 失败: 文本='{text}', 错误={e}")
        raise

# RabbitMQ 连接
connection = BlockingConnection(ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='text_moderation', durable=True)

# 回调函数
def callback(ch, method, properties, body):
    task = json.loads(body)
    text = task['text']
    try:
        is_inappropriate = get_moderation_result(text)
        if is_inappropriate:
            print(f"检测到不当内容: {text}")
        else:
            print(f"内容正常: {text}")
        with open('test_results.txt', 'a') as f:
            f.write(f"{text},{is_inappropriate}\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        for attempt in range(3):
            try:
                is_inappropriate = get_moderation_result(text)
                if is_inappropriate:
                    print(f"检测到不当内容: {text}")
                else:
                    print(f"内容正常: {text}")
                with open('test_results.txt', 'a') as f:
                    f.write(f"{text},{is_inappropriate}\n")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            except Exception as retry_e:
                logging.error(f"重试 {attempt+1} 失败: 文本='{text}', 错误={retry_e}")
                if attempt == 2:
                    logging.error(f"最终失败: 文本='{text}', 错误={retry_e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    break

# 启动消费者
channel.basic_consume(queue='text_moderation', on_message_callback=callback)
print("开始消费 text_moderation 队列的消息...")
channel.start_consuming()