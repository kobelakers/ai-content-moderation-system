from kafka import KafkaProducer
import json

try:
    producer = KafkaProducer(bootstrap_servers='101.201.253.35:9092')
    message = {'text': 'Sample text'}
    producer.send('content_ingestion', json.dumps(message).encode('utf-8'))
    producer.flush()
    print("消息发送成功")
except Exception as e:
    print(f"Kafka错误: {e}")
