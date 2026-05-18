import datetime
from extraction.utils.utils import *

def transform(raw_event: dict, msg_type: str) -> dict:
    body = raw_event.get("body", {})
    header = raw_event.get("header", {})

    return {
        "msg_type": msg_type,
        "train_id": body.get("train_id"),
        "train_uid": body.get("train_uid"),
        "train_service_code": body.get("train_service_code"),
        "train_file_address": body.get("train_file_address"),
        "schedule_type": body.get("schedule_type"),
        "schedule_source": body.get("schedule_source"),
        "schedule_start_date": body.get("schedule_start_date"),
        "schedule_end_date": body.get("schedule_end_date"),
        "schedule_wtt_id": body.get("schedule_wtt_id"),
        "sched_origin_stanox": parse_int(body.get("sched_origin_stanox")),
        "tp_origin_stanox": parse_int(body.get("tp_origin_stanox")),
        "tp_origin_timestamp": f"{body.get('tp_origin_timestamp')}T00:00:00Z",  # already a date string
        "origin_dep_timestamp": parse_timestamp(body.get("origin_dep_timestamp")),
        "creation_timestamp": parse_timestamp(body.get("creation_timestamp")),
        "train_call_type": body.get("train_call_type"),
        "train_call_mode": body.get("train_call_mode"),
        "toc_id": parse_int(body.get("toc_id")),
        "d1266_record_number": body.get("d1266_record_number"),
        "source_dev_id": header.get("source_dev_id"),
        "user_id": header.get("user_id"),
        "original_data_source": header.get("original_data_source"),
        "source_system_id": header.get("source_system_id"),
        "msg_queue_timestamp": parse_timestamp(header.get("msg_queue_timestamp")),
        "ingest_ts": datetime.datetime.utcnow().isoformat()
    }
