import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct', exchange_type='direct', durable=True)

result = channel.queue_declare(queue='', durable=True)
queue_name = result.method.queue

channel.queue_bind(
        exchange='direct', queue=queue_name, routing_key="route1")

print(' [*] Waiting for logs. To exit press CTRL+C')


def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(
    queue=queue_name, on_message_callback=callback)

channel.start_consuming()
