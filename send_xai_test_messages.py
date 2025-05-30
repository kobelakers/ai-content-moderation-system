import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='text_moderation', durable=True)

with open('test_data/xai_sample_texts.txt', 'r') as file:
    for line in file:
        text = line.strip()
        if text and not text.startswith('#'):
            message = {'text': text}
            channel.basic_publish(exchange='', routing_key='text_moderation', body=json.dumps(message))
            print(f"发送消息: {text}")

connection.close()