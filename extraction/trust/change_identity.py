import datetime
from extraction.utils.utils import *

def transform(raw_event: dict, msg_type: str) -> dict:
    body = raw_event.get("body", {})
    return {
        "msg_type": msg_type,
        "train_id": body.get("train_id"),
        "current_train_id": body.get("current_train_id"),
        "revised_train_id": body.get("revised_train_id"),
        "event_timestamp": parse_timestamp(body.get("event_timestamp")),
        "train_service_code": body.get("train_service_code"),
        "train_file_address": body.get("train_file_address"),
        "ingest_ts": datetime.datetime.utcnow().isoformat()
    }
