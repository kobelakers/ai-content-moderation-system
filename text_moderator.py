import os
import json
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from pika import BlockingConnection, ConnectionParameters

# 检查 API 密钥
if "VOLCENGINE_API_KEY" not in os.environ:
    raise ValueError("VOLCENGINE_API_KEY 未设置")

# 配置日志
logging.basicConfig(filename='moderation.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 加载缓存
try:
    if os.path.exists('cache.json') and os.path.getsize('cache.json') > 0:
        with open('cache.json', 'r') as f:
            cache = json.load(f)
    else:
        logging.info("cache.json 不存在或为空，初始化为空字典")
        cache = {}
except json.JSONDecodeError as e:
    logging.error(f"cache.json 解析失败: {e}，初始化为空字典")
    cache = {}
except FileNotFoundError:
    logging.info("cache.json 不存在，初始化为空字典")
    cache = {}

# 配置 DeepSeek V3 API
llm = ChatOpenAI(
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
    openai_api_key=os.environ.get("VOLCENGINE_API_KEY"),
    model_name="deepseek-v3-250324",
    temperature=0,
    timeout=1800
)

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个内容审核助手。你的任务是将以下文本分类为 'appropriate'（合适）或 'inappropriate'（不合适）。仅回复一个单词：'appropriate' 或 'inappropriate'。不要添加任何额外解释或符号。"),
    ("user", "文本: {text}")
])

# 创建链
chain = prompt | llm

# 获取审核结果
def get_moderation_result(text):
    if text in cache:
        logging.info(f"缓存命中: 文本='{text}', 结果={cache[text]}")
        return cache[text]
    try:
        response = chain.invoke({"text": text})
        logging.info(f"API 原始响应: 文本='{text}', 响应={response}")
        result = response.content.strip().lower()
        logging.info(f"API 解析结果: 文本='{text}', 结果={result}")
        is_inappropriate = result == "inappropriate"
        cache[text] = is_inappropriate
        try:
            with open('cache.json', 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"写入 cache.json 失败: {e}")
        return is_inappropriate
    except Exception as e:
        logging.error(f"调用 DeepSeek V3 API 失败: 文本='{text}', 错误={e}")
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