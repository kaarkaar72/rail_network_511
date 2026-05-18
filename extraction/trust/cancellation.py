import datetime
from extraction.utils.utils import *

def transform(raw_event: dict, msg_type: str) -> dict:
    body = raw_event.get("body", {})
    header = raw_event.get("header", {})

    return {
        "msg_type": msg_type,
        "train_id": body.get("train_id"),
        "train_service_code": body.get("train_service_code"),
        "train_file_address": body.get("train_file_address"),
        "canx_type": body.get("canx_type"),
        "canx_reason_code": body.get("canx_reason_code"),
        "canx_timestamp": parse_timestamp(body.get("canx_timestamp")),
        "orig_loc_stanox": parse_int(body.get("orig_loc_stanox")),
        "orig_loc_timestamp": parse_timestamp(body.get("orig_loc_timestamp")),
        "dep_timestamp": parse_timestamp(body.get("dep_timestamp")),
        "loc_stanox": parse_int(body.get("loc_stanox")),
        "toc_id": parse_int(body.get("toc_id")),
        "division_code": body.get("division_code"),
        "ingest_ts": datetime.datetime.utcnow().isoformat()
    }
