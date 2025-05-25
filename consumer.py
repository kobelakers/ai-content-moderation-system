from kafka import KafkaConsumer
import json

try:
    consumer = KafkaConsumer('content_ingestion', bootstrap_servers='101.201.253.35:9092', group_id='moderation_group', auto_offset_reset='latest')
    for message in consumer:
        content = json.loads(message.value.decode('utf-8'))
        print(f"接收消息: {content}")
except Exception as e:
    print(f"Kafka错误: {e}")
