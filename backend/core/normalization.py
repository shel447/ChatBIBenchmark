from datetime import datetime

def _normalize_string(value):
    if value is None:
        return None
    return str(value).strip().lower()


def _try_parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_param_value(param):
    if param is None:
        return None
    if isinstance(param, dict):
        param_type = param.get("type")
        value = param.get("value")
    else:
        param_type = None
        value = param

    if param_type in ("enum", "string", "metric", "dimension"):
        if isinstance(value, list):
            return sorted([_normalize_string(v) for v in value])
        return _normalize_string(value)
    if param_type in ("number", "int", "float"):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if param_type == "date":
        return _try_parse_date(value)
    if param_type == "date_range":
        if isinstance(value, dict):
            start = _try_parse_date(value.get("start"))
            end = _try_parse_date(value.get("end"))
            return (start, end)
        return None

    if isinstance(value, list):
        return sorted([_normalize_string(v) for v in value])
    return _normalize_string(value)


def normalize_param_map(params):
    normalized = {}
    for key, param in (params or {}).items():
        normalized[key] = normalize_param_value(param)
    return normalized


def normalize_fact_value(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        return sorted([_normalize_string(v) for v in value])
    return _normalize_string(value)
