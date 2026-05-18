import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from confluent_kafka import Consumer, Producer, KafkaException
import redis

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
ENRICHED_TOPIC = "rail_movement_live"


def enrich_position(msg_value, r):
    """Attach geo, TOC, and schedule info from Redis for the current movement."""
    train_id = msg_value.get("train_id")
    if not train_id:
        logging.warning("Message missing train_id, skipping enrichment")
        return msg_value

    msg_value["train_signalling_id"] = train_id[2:6] if len(train_id) >= 6 else None

    train_signalling_id = msg_value.get("train_signalling_id")
    loc_stanox = msg_value.get("loc_stanox")
    next_loc_stanox = msg_value.get("next_report_stanox")
    toc_id = msg_value.get("toc_id")

    # Geo lookup
    geo = r.get(f"geo:{loc_stanox}")
    next_geo = r.get(f"geo:{next_loc_stanox}")
    toc_name = r.get(f"toc:{toc_id}")

    # Schedule lookup — stored as a JSON list
    schedules_raw = r.get(f"schedule:{train_signalling_id}")
    schedules = json.loads(schedules_raw) if schedules_raw else []
    now = datetime.utcnow().date()
    msg_value.setdefault("train_uid", None)
    if isinstance(schedules, list):
        for sched in schedules:
            try:
                start = datetime.fromisoformat(sched["start_date"]).date()
                end = datetime.fromisoformat(sched["end_date"]).date()
                if start <= now <= end:
                    msg_value["train_uid"] = sched.get("train_uid") or sched.get("schedule_id")
                    break
            except (KeyError, ValueError):
                continue

    if geo and next_geo:
        geo = json.loads(geo)
        next_geo = json.loads(next_geo)
        msg_value["latitude"] = geo.get("lat")
        msg_value["longitude"] = geo.get("lon")
        msg_value["location_name"] = geo.get("location_name")
        msg_value["next_location"] = next_geo.get("location_name")
    else:
        msg_value["latitude"] = None
        msg_value["longitude"] = None
        msg_value["location_name"] = None
        msg_value["next_location"] = None

    if toc_name:
        msg_value["toc_name"] = toc_name.decode('utf-8') if isinstance(toc_name, bytes) else toc_name
    else:
        msg_value["toc_name"] = None

    return msg_value


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'rail-live-movements',
        'auto.offset.reset': 'earliest'
    })
    producer = Producer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
    })

    consumer.subscribe(['rail_movement_clean'])
    logging.info("Enrichment pipeline started. Consuming from rail_movement_clean.")

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
                enriched_data = enrich_position(raw_data, r)
                producer.produce(
                    topic=ENRICHED_TOPIC,
                    value=json.dumps(enriched_data).encode('utf-8')
                )
                producer.poll(0)
                logging.info(f"Produced live movement for train {enriched_data.get('train_id')}")

            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
            except KafkaException as e:
                logging.error(f"Kafka exception: {e}")
            except Exception as e:
                logging.error(f"Unexpected error processing message: {e}", exc_info=True)

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.flush()
        logging.info("Live train movement enrichment stopped gracefully")


if __name__ == "__main__":
    main()
