import logging
import os
from typing import ClassVar


class PrettyFormatter(logging.Formatter):
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
        "ENDC": "\033[0m",
    }  # RUF012 Mutable class attributes should be annotated with `typing.ClassVar`

    def format(self, record: logging.LogRecord) -> str:
        formatted_record = super().format(record)
        color_prefix = self.COLORS[record.levelname]
        color_suffix = self.COLORS["ENDC"]
        return f"{color_prefix}{record.levelname}: {color_suffix}{formatted_record}"


class LoggerFactory:
    _instance = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if not cls._instance:
            cls._instance = cls._setup_logger()
        return cls._instance

    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger("cliptale")

        # Console handler with pretty formatting
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(PrettyFormatter())
        logger.addHandler(stream_handler)

        # File handler
        log_file = "./logs/cliptale.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        logger.setLevel(logging.DEBUG)

        return logger
