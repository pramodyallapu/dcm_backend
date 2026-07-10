import logging
from collections import deque
from threading import Lock

_MAX_RECORDS = 1000
_buffer: deque[str] = deque(maxlen=_MAX_RECORDS)
_lock = Lock()


class RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        with _lock:
            _buffer.append(message)


def get_recent_logs(limit: int = 200) -> list[str]:
    with _lock:
        records = list(_buffer)
    if limit <= 0:
        return records
    return records[-limit:]
