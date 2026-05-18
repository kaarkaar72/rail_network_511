import datetime
from extraction.utils.utils import *

def transform(raw_event: dict, msg_type: str) -> dict:
    body = raw_event.get("body", {})
    return {
        "msg_type": msg_type,
        "train_id": body.get("train_id"),
        "train_service_code": body.get("train_service_code"),
        "division_code": body.get("division_code"),
        "toc_id": parse_int(body.get("toc_id")),
        "route": body.get("route"),
        "loc_stanox": parse_int(body.get("loc_stanox")),
        "next_report_stanox": parse_int(body.get("next_report_stanox")),
        "reporting_stanox": parse_int(body.get("reporting_stanox")),
        "platform": body.get("platform"),
        "actual_timestamp": parse_timestamp(body.get("actual_timestamp")),
        "planned_timestamp": parse_timestamp(body.get("planned_timestamp")),
        "planned_event_type": body.get("planned_event_type"),
        "event_type": body.get("event_type"),
        "timetable_variation": parse_int(body.get("timetable_variation")),
        "variation_status": body.get("variation_status"),
        "next_report_run_time": parse_int(body.get("next_report_run_time")),
        "correction_ind": parse_bool(body.get("correction_ind")),
        "offroute_ind": parse_bool(body.get("offroute_ind")),
        "train_terminated": parse_bool(body.get("train_terminated")),
        "delay_monitoring_point": parse_bool(body.get("delay_monitoring_point")),
        "auto_expected": parse_bool(body.get("auto_expected")),
        "event_source": body.get("event_source"),
        "ingest_ts": datetime.datetime.utcnow().isoformat()
    }
