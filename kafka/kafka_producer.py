from confluent_kafka import Producer
import logging

def create_producer():
    return Producer({
        'bootstrap.servers': 'localhost:9092',
        'linger.ms': 10,
        'acks': 'all',
        'retries': 3
    })

def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(f"Delivered to {msg.topic()} [{msg.partition()}]")