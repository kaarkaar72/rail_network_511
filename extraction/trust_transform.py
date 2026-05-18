import json
import os
import sys
import logging
from confluent_kafka import Consumer, Producer, KafkaException

# Ensure the trust sub-package is importable regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trust import activation, cancellation, change_identity, change_location, change_origin, movement, reinstatement

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

MSG_TYPE_TO_TOPIC = {
    "0001": "rail_activation_clean",
    "0002": "rail_cancellation_clean",
    "0003": "rail_movement_clean",
    "0005": "rail_reinstatement_clean",
    "0006": "rail_change_origin_clean",
    "0007": "rail_change_identity_clean",
    "0008": "rail_change_location_clean"
}

DLQ_TOPIC = "rail_movement_dlq"

TRANSFORMERS = {
    "0001": activation.transform,
    "0002": cancellation.transform,
    "0003": movement.transform,
    "0005": reinstatement.transform,
    "0006": change_origin.transform,
    "0007": change_identity.transform,
    "0008": change_location.transform
}


def dispatch_transform(raw_event, msg_type):
    transform_fn = TRANSFORMERS.get(msg_type)
    if transform_fn:
        return transform_fn(raw_event, msg_type)
    return None


def main():
    consumer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'rail-movement-transformer',
        'auto.offset.reset': 'earliest'
    }
    producer_conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    }

    consumer = Consumer(consumer_conf)
    producer = Producer(producer_conf)

    consumer.subscribe(['rail_movement_raw'])
    logging.info("Consumer subscribed and transformation started.")

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                logging.error(f"Consumer error: {msg.error()}")
                continue

            try:
                raw_data = json.loads(msg.value().decode('utf-8'))
                message_type = raw_data.get("header", {}).get("msg_type")
                dest_topic = MSG_TYPE_TO_TOPIC.get(message_type)

                if not dest_topic:
                    logging.warning(f"Unknown msg_type={message_type!r}, routing to DLQ")
                    producer.produce(
                        topic=DLQ_TOPIC,
                        value=json.dumps({
                            "reason": f"unknown msg_type={message_type}",
                            "raw": raw_data
                        }).encode('utf-8')
                    )
                    producer.poll(0)
                    continue

                transformed = dispatch_transform(raw_data, message_type)
                if transformed:
                    producer.produce(
                        topic=dest_topic,
                        value=json.dumps(transformed).encode('utf-8')
                    )
                    logging.info(f"Produced cleaned data for feed: {dest_topic}")
                else:
                    logging.warning(f"Transform returned None for msg_type={message_type}, routing to DLQ")
                    producer.produce(
                        topic=DLQ_TOPIC,
                        value=json.dumps({
                            "reason": "transform returned None",
                            "raw": raw_data
                        }).encode('utf-8')
                    )

            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode message: {e}")
                producer.produce(
                    topic=DLQ_TOPIC,
                    value=json.dumps({
                        "reason": f"JSONDecodeError: {e}",
                        "raw": msg.value().decode('utf-8', errors='replace')
                    }).encode('utf-8')
                )
            except KafkaException as e:
                logging.error(f"Kafka exception: {e}")

            producer.poll(0)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.flush()
        logging.info("Kafka consumer closed and producer flushed.")


if __name__ == "__main__":
    main()
