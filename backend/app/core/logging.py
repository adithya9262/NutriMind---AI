import logging
import sys

from .config import Settings

_logging_initialized = False


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from .middleware import get_request_id

            record.request_id = get_request_id() or "-"
        except Exception:
            record.request_id = "-"
        return True


def setup_logging(settings: Settings | None = None) -> None:
    global _logging_initialized
    if _logging_initialized:
        return

    from .config import Settings as SettingsClass

    s = settings or SettingsClass()
    level = logging.DEBUG if s.DEBUG else logging.INFO

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)

    _logging_initialized = True
