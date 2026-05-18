import datetime
from extraction.utils.utils import *

def transform(raw_event: dict, msg_type: str) -> dict:
    body = raw_event.get("body", {})
    return {
        "msg_type": msg_type,
        "train_id": body.get("train_id"),
        "current_train_id": body.get("current_train_id"),
        "coo_timestamp": parse_timestamp(body.get("coo_timestamp")),
        "reason_code": body.get("reason_code"),
        "dep_timestamp": parse_timestamp(body.get("dep_timestamp")),
        "loc_stanox": parse_int(body.get("loc_stanox")),
        "original_loc_stanox": parse_int(body.get("original_loc_stanox")),
        "original_loc_timestamp": parse_timestamp(body.get("original_loc_timestamp")),
        "toc_id": parse_int(body.get("toc_id")),
        "division_code": body.get("division_code"),
        "train_service_code": body.get("train_service_code"),
        "train_file_address": body.get("train_file_address"),
        "ingest_ts": datetime.datetime.utcnow().isoformat()
    }
