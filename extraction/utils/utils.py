import datetime
def parse_bool(value):
    return value.lower() == "true" if isinstance(value, str) else bool(value)

def parse_int(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def parse_timestamp(ts_ms):
    try:
        return datetime.datetime.utcfromtimestamp(int(ts_ms) / 1000).isoformat()
    except (ValueError, TypeError):
        return None