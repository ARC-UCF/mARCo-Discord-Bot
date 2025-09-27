import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

_LEVEL_NAMES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


class UTCFormatter(logging.Formatter):
    converter = staticmethod(__import__("time").gmtime)


DEFAULT_FMT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _coerce_level(level: Optional[int | str]) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        return _LEVEL_NAMES.get(level.strip().upper(), logging.INFO)
    return logging.INFO


def setup_logging(
    level: Optional[int | str] = None,
    *,
    logger_name: str = "marco_bot",
    use_utc: bool = True,
    file_path: Optional[str] = None,
    file_max_bytes: int = 2_000_000,
    file_backup_count: int = 3,
) -> logging.Logger:

    # Resolve level with ENV override
    env_level = os.getenv("MARCO_LOG_LEVEL")
    resolved_level = _coerce_level(level if level is not None else env_level)

    logger = logging.getLogger(logger_name)
    logger.setLevel(resolved_level)
    logger.propagate = False

    # Avoid duplicate handlers on hot-reload
    if not logger.handlers:
        # Console handler (stdout)
        stream_handler = logging.StreamHandler(sys.stdout)
        fmt_cls = UTCFormatter if use_utc else logging.Formatter
        formatter = fmt_cls(DEFAULT_FMT, datefmt=DEFAULT_DATEFMT)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Optional rotating file handler
        if file_path:
            file_handler = RotatingFileHandler(
                file_path, maxBytes=file_max_bytes, backupCount=file_backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Tame noisy libraries (tweak as needed)
        for noisy in ("discord", "aiohttp", "asyncio"):
            nl = logging.getLogger(noisy)
            nl.setLevel(max(resolved_level, logging.WARNING))

    # Record effective configuration once
    logger.debug(
        "Logging configured",
        extra={
            "logger_name": logger_name,
            "level": logging.getLevelName(resolved_level),
        },
    )

    return logger
