import logging
import os
from logging.config import dictConfig

from dictionary.config import DevConfig, TestConfig, config


class ColoredFormatter(logging.Formatter):
    FONT_COLOR_DEFAULT = "\033[39m"
    FONT_TYPE_DEFAULT = ""
    FONT_RESET_SUFFIX = "\033[0m"

    MAPPING = {
        "DEBUG": "\033[97m",  # WHITE
        "INFO": "\033[96m",  # LIGTH_BLUE_CYAN
        "WARNING": "\033[93m",  # YELLOW
        "ERROR": "\033[91m",  # RED
        "CRITICAL": "\033[91m",  # RED
    }

    def __init__(
        self,
        custom_format=None,
        name_color=FONT_COLOR_DEFAULT,
        name_font_type=FONT_TYPE_DEFAULT,
        message_color=FONT_COLOR_DEFAULT,
        message_font_type=FONT_TYPE_DEFAULT,
        *args,
        **kwargs,
    ):
        datefmt = kwargs.pop("datefmt", "%Y-%m-%d %H:%M:%S")
        logging.Formatter.__init__(self, *args, datefmt=datefmt, **kwargs)

        if not custom_format:
            self.desired_format = (
                # "%(asctime)s.%(msecs)03dZ - "
                "%(levelname)-8s"
                f"{name_color}{name_font_type}%(name)s | "
                f"%(filename)s:%(lineno)s | %(funcName)s{self.FONT_RESET_SUFFIX}"
                f"{self.MAPPING["WARNING"]} >>> {self.FONT_RESET_SUFFIX}"
                f"[{message_color}{message_font_type}%(message)s{self.FONT_RESET_SUFFIX}]"
            )
        else:
            self.desired_format = custom_format

    def format(self, record):
        # Making a copy of a record to prevent altering the message for other loggers
        record = logging.makeLogRecord(record.__dict__)  # noqa: E501 >> or import copy and record = copy.copy(record)

        extra_info = record.__dict__.pop("additional information", "")
        if extra_info:
            record.msg += f"\nAdditional information: {extra_info}"

        # Changing levelname color depending on logger actual level
        color = self.MAPPING.get(record.levelname, self.FONT_COLOR_DEFAULT)
        record.levelname = f"{color}{record.levelname:<10}{self.FONT_RESET_SUFFIX}"

        # Formatting the record using desired_format
        self._style._fmt = self.desired_format
        msg = super().format(record)  # noqa: E501 >> msg = logging.Formatter.format(self, record)
        return msg


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "libraries": {
                    "()": ColoredFormatter,
                    "name_color": "\033[92m",  # GREEN
                    "name_font_type": "\033[2m",  # FAINT
                },
                "app": {
                    "()": ColoredFormatter,
                    "name_color": "\033[94m",  # BLUE
                    "message_color": "\033[97m",  # WHITE
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s %(msecs)03d %(levelname)s %(name)s %(filename)s %(lineno)s \033[93m>>>\033[0m [%(message)s]",
                },
                "test": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ - %(levelname)8s - TEST - %(name)s - %(filename)s:%(lineno)s \033[93m>>>\033[0m [%(message)s]",
                },
            },
            "handlers": {
                "console_libraries": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "libraries",
                },
                "console_app": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "app",
                },
                "fixed": {
                    "class": "logging.FileHandler",
                    "level": "ERROR",
                    "formatter": "file",
                    "filename": "logs_error.log",
                    "encoding": "utf-8",
                },
                "rotating": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "logs_rotating.log",
                    "mode": "a",
                    "maxBytes": 1024 * 512,  # 0.5MB
                    "backupCount": 3,
                    "encoding": "utf-8",
                },
                "tests": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "test",
                    "filename": os.path.join(
                        os.path.dirname(__file__), "tests", "logs_test.log"
                    ),
                    "mode": "a",
                    "maxBytes": 1024 * 256,  # 0.25MB
                    "backupCount": 1,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "dictionary": {
                    "handlers": [
                        "console_app",
                        "tests" if isinstance(config, TestConfig) else "rotating",
                        "fixed",
                    ],
                    "level": "DEBUG"
                    if isinstance(config, (DevConfig, TestConfig))
                    else "INFO",
                    "propagade": False,
                },
                # "uvicorn": {
                #     "handlers": ["console_libraries", "fixed", "rotating"],
                #     "level": "INFO",
                # },
            },
        }
    )
