"""bgdev public package.

:created: 05/09/2021
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging
import sys

from maya import OpenMaya

LOG_FORMATTER = logging.Formatter(
    fmt="(%(asctime)s) %(levelname)s [%(name)s.%(funcName)s]: %(message)s",
    datefmt="%H:%M:%S",
)


class MayaLogHandler(logging.StreamHandler):
    """Custom logging handler for Maya to display messages in color."""

    def display_maya_message(self, message, level):
        """Display a message using OpenMaya."""
        if level > logging.ERROR:
            OpenMaya.MGlobal.displayError(message)
        elif level > logging.WARNING:
            OpenMaya.MGlobal.displayError(message)
        elif level > logging.INFO:
            OpenMaya.MGlobal.displayWarning(message)
        elif level <= logging.DEBUG:
            OpenMaya.MGlobal.displayInfo(message)
        else:
            OpenMaya.MGlobal.displayInfo(message)

    def emit(self, record):
        """Overwrite the emit function to display message in Maya."""
        msg = self.format(record)
        self.display_maya_message(msg, record.levelno)
        super(MayaLogHandler, self).emit(record)


def getLogger(name):  # pylint: disable=invalid-name
    """Backward camelCase compatibility with logging module."""
    return get_logger(name)


def get_logger(name):
    """Create an instance of the Stim logger."""
    logger = logging.getLogger(name)
    configure_logger(logger)
    return logger


def configure_logger(logger):
    """Update given logger handlers."""
    handler = MayaLogHandler(sys.__stdout__)
    handler.setLevel("INFO")
    handler.setFormatter(LOG_FORMATTER)
    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False


# create custom logger
LOG = logging.getLogger("bgdev")
configure_logger(LOG)
