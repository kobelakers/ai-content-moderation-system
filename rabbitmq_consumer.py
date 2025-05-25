from pika import BlockingConnection, ConnectionParameters
import json

connection = BlockingConnection(ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='text_moderation', durable=True)

def callback(ch, method, properties, body):
    task = json.loads(body)
    print(f"接收任务: {task}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='text_moderation', on_message_callback=callback)
channel.start_consuming()
