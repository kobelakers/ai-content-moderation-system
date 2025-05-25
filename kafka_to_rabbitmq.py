from kafka import KafkaConsumer
from pika import BlockingConnection, ConnectionParameters
import json

consumer = KafkaConsumer('content_ingestion', bootstrap_servers='101.201.253.35:9092')
connection = BlockingConnection(ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='text_moderation', durable=True)  # 设置 durable=True

for message in consumer:
    content = json.loads(message.value.decode('utf-8'))
    if 'text' in content:
        channel.basic_publish(exchange='', routing_key='text_moderation', body=json.dumps({'text': content['text']}))
        print(f"消息发布到RabbitMQ: {content['text']}")
