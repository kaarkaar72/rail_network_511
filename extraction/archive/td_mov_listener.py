import os
import time
import json
import logging
import socket
from dotenv import load_dotenv
import stomp
import socket
from utils.trust import *
import sys
sys.path.append("./kafka/")
from kafka_producer import create_producer

CLIENT_ID = socket.getfqdn()
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TRAIN_MOVEMENTS_TOPIC = os.getenv("TRAIN_MOVEMENTS_TOPIC", "train_describer_raw")
STOMP_HOST = os.getenv("STOMP_HOST", "publicdatafeeds.networkrail.co.uk")
STOMP_PORT = int(os.getenv("STOMP_PORT", 61618))
STOMP_USER = os.getenv("STOMP_USER", "user")
STOMP_PASS = os.getenv("STOMP_PASS", "pass")
STOMP_QUEUE = os.getenv("STOMP_QUEUE", "/topic/TD_ALL_SIG_AREA")
RECONNECT_DELAY_SECS = int(os.getenv("RECONNECT_DELAY_SECS", 5))
HEARTBEAT_INTERVAL_MS = int(os.getenv("RECONNECT_DELAY_SECS", 15000))


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
        print('received an error {}'.format(frame.body))  # debug print

    def on_disconnected(self):
        logging.warning("Disconnected from STOMP. Reconnecting...")
        try:
            connect_and_subscribe(self.connection)  
        except Exception as e:
            logging.error(f"Failed to reconnect: {e}")
            time.sleep(RECONNECT_DELAY_SECS)

    def on_connecting(self, host_and_port):
        logging.info('Connecting to ' + host_and_port[0])


    def on_message(self,frame):
        logging.info("Received message from STOMP")
        try:
            headers, message_raw = frame.headers, frame.body
            parsed_body = json.loads(message_raw)
            if "TD_ALL_SIG_AREA" in headers.get("destination", ""): 
                print_td_frame(parsed_body)
                for record in parsed_body:
                    for k,v in record.items():
                        if k.startswith('C'):
                            self.producer.send("rail_td_mov_raw", v)
                self.producer.flush()

        except Exception as e:
            logging.error(f"Exception processing message: {e}", exc_info=True)

def connect_and_subscribe(connection):
    if stomp.__version__[0] < '5':
        connection.start()

    connect_header = {'client-id': STOMP_USER + '-' + CLIENT_ID}
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


