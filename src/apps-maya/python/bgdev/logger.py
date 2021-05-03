"""Create a custom logger to be used accross the package.

:created: 11/12/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging
import sys

LOG = logging.getLogger("bgdev")


def configure_logger(logger, reset=False):
    """Configure logger with custom handlers."""
    logger.propagate = False
    logger.setLevel(logging.INFO)

    if reset is True:
        logger.handlers = []

    if not logger.handlers:
        formatter = logging.Formatter(
            "(%(asctime)s) %(levelname)s [%(name)s]: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        stdout_handler = logging.StreamHandler(sys.__stdout__)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)


if not LOG.handlers:
    configure_logger(LOG)
