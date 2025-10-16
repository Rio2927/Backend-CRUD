import logging
from datetime import datetime, timezone
from typing import Optional

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

def utc_now_iso() -> str:
    "Return current UTC time in ISO8601 with Z suffix."
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)

def parse_bool(value: Optional[str]) -> Optional[bool]:
    "Parse truthy/falsey strings to bool. Returns None if value is None or unrecognized."
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"1", "true", "yes", "y", "t"}:
        return True
    if v in {"0", "false", "no", "n", "f"}:
        return False
    return None

def get_logger(name: str = "task_api") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger