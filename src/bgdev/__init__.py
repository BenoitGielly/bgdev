"""bgdev public package.

:created: 05/09/2021
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging.config
import sys

# logging setup
LOG_FORMAT = "(%(asctime)s) %(levelname)s [%(name)s.%(funcName)s]: %(message)s"
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "defaultFormatter": {"format": LOG_FORMAT, "datefmt": "%H:%M:%S"}
    },
    "handlers": {
        "defaultHandler": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "defaultFormatter",
        },
        "stdoutHandler": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "defaultFormatter",
            "stream": sys.__stdout__,
        },
    },
    "loggers": {
        __name__: {
            "level": "INFO",
            "propagate": False,
            "handlers": ["defaultHandler", "stdoutHandler"],
        },
    },
}

logging.config.dictConfig(LOG_CONFIG)
