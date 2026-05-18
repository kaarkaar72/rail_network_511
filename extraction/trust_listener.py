import os
import time
import json
import logging
import socket
from dotenv import load_dotenv
import stomp
import sys
sys.path.append("./kafka/")
from kafka_producer import delivery_report,create_producer

CLIENT_ID = socket.getfqdn()
load_dotenv()

TRAIN_MOVEMENTS_TOPIC = os.getenv("TRAIN_MOVEMENTS_TOPIC", "rail_movement_raw")
STOMP_HOST = os.getenv("STOMP_HOST", "publicdatafeeds.networkrail.co.uk")
STOMP_PORT = int(os.getenv("STOMP_PORT", 61618))
STOMP_USER = os.getenv("STOMP_USER", "user")
STOMP_PASS = os.getenv("STOMP_PASS", "pass")
STOMP_QUEUE = os.getenv("STOMP_QUEUE", "/topic/TRAIN_MVT_ALL_TOC")
RECONNECT_DELAY_SECS = int(os.getenv("RECONNECT_DELAY_SECS", 5))
HEARTBEAT_INTERVAL_MS = int(os.getenv("HEARTBEAT_INTERVAL_MS", 15000))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class RailMovementListener(stomp.ConnectionListener):
    def __init__(self,producer,connection):
        self.producer = producer
        self.connection = connection

    def on_heartbeat(self):
        logging.info('Received a heartbeat')

    def on_heartbeat_timeout(self):
        logging.error('Heartbeat timeout')

    def on_error(self, frame):
        logging.error('Received a STOMP error: {}'.format(frame.body))

    def on_disconnected(self):
        logging.warning("Disconnected from STOMP. Reconnecting...")
        reconnect(self)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])


    def on_message(self,frame):
        logging.info("Received message from STOMP")
        try:
            if not frame or not frame.body:
                return

            frame_body = json.loads(frame.body)
            records = frame_body if isinstance(frame_body, list) else [frame_body]
            for record in records:
                self.producer.produce(TRAIN_MOVEMENTS_TOPIC, 
                                        value=json.dumps(record).encode('utf-8'),
                                        callback=delivery_report)
            self.producer.flush()

        except Exception as e:
            logging.error(f"Exception processing message: {e}", exc_info=True)


def reconnect(listener):
    delay = RECONNECT_DELAY_SECS
    max_delay = 60

    while True:
        try:
            # Safely close old connection if open
            conn = listener.connection
            try:
                if hasattr(conn, "transport") and getattr(conn.transport, "is_connected", False):
                    conn.disconnect()
            except Exception as e:
                logging.debug(f"Connection cleanup failed: {e}")

            # Create new connection
            new_conn = stomp.Connection12(
                [(STOMP_HOST, STOMP_PORT)],
                auto_decode=False,
                heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS)
            )
            new_conn.set_listener('', listener)
            listener.connection = new_conn  # update listener reference

            connect_and_subscribe(new_conn)
            logging.info("✅ Successfully reconnected to STOMP broker")
            return  # success — exit loop
        except Exception as e:
            logging.error(f"Reconnect failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)


def connect_and_subscribe(connection):
    if stomp.__version__[0] < '5':
        connection.start()

    connect_header = {'client-id': f"{STOMP_USER}-{CLIENT_ID}-trust"}
    subscribe_header = {'activemq.subscriptionName': CLIENT_ID}

    connection.connect(username=STOMP_USER,
                       passcode=STOMP_PASS,
                       wait=True,
                       headers=connect_header)

    connection.subscribe(destination=STOMP_QUEUE,
                         id='1',
                         ack='auto',
                         headers=subscribe_header)

def main():
    conn = stomp.Connection12([(STOMP_HOST, STOMP_PORT)],
                                auto_decode=False,
                                heartbeats=(HEARTBEAT_INTERVAL_MS, HEARTBEAT_INTERVAL_MS))
    producer = create_producer()
    listener = RailMovementListener(producer,conn)
    conn.set_listener('', listener)
    connect_and_subscribe(conn)

    logging.info("Listening for train movements...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Interrupted, shutting down")
    finally:
        conn.disconnect()

if __name__ == "__main__":
    main()


