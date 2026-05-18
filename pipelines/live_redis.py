import redis
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from confluent_kafka import Consumer

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MAX_TRAIL_POINTS = 20
STALE_MINUTES = 5


def safe_json_load(s):
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def update_live_from_msg(msg_obj, r):
    train_id = msg_obj.get("train_id")
    if not train_id:
        return

    key = f"train3:{train_id}"
    raw = r.get(key)
    state = safe_json_load(raw) or {"trail": []}

    lat = msg_obj.get("latitude")
    lon = msg_obj.get("longitude")
    if lat is None or lon is None:
        return

    trail = state.get("trail", [])
    trail.append([lon, lat])
    if len(trail) > MAX_TRAIL_POINTS:
        trail = trail[-MAX_TRAIL_POINTS:]

    state.update({
        "train_id": train_id,
        "train_uid": msg_obj.get("train_uid"),
        "toc_name": msg_obj.get("toc_name"),
        "latitude": lat,
        "longitude": lon,
        "location_name": msg_obj.get("location_name"),
        "next_station": msg_obj.get("next_location"),
        "planned_event_type": msg_obj.get("planned_event_type"),
        "planned_timestamp": msg_obj.get("planned_timestamp"),
        "timetable_variation": msg_obj.get("timetable_variation"),
        "variation_status": msg_obj.get("variation_status"),
        "event_type": msg_obj.get("event_type"),
        "trail": trail,
        "last_update": datetime.utcnow().isoformat()
    })
    r.set(key, json.dumps(state))
    r.expire(key, STALE_MINUTES * 60)


def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'redis_updater',
        'auto.offset.reset': 'latest'
    })
    consumer.subscribe(['rail_movement_live'])
    logging.info("Redis updater started. Consuming from rail_movement_live.")

    try:
        while True:
            messages = consumer.consume(num_messages=100, timeout=1.0)
            for msg in messages:
                if msg and not msg.error():
                    try:
                        data = json.loads(msg.value())
                        update_live_from_msg(data, r)
                    except Exception as e:
                        logging.error(f"Failed to process message: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        logging.info("Redis updater stopped.")


if __name__ == "__main__":
    main()
