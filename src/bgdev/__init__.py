"""bgdev public package.

:created: 05/09/2021
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging
import sys

LOG = logging.getLogger(__name__)
LOG.handlers = []
LOG.propagate = False

LOG_FORMATTER = logging.Formatter(
    fmt="(%(asctime)s) %(levelname)s [%(name)s.%(funcName)s]: %(message)s",
    datefmt="%H:%M:%S",
)

# add Maya UI handler if not in batch mode
try:
    from maya import cmds

    if not cmds.about(batch=True):
        LOG_STREAM_HANDLER = logging.StreamHandler()
        LOG_STREAM_HANDLER.setLevel("INFO")
        LOG_STREAM_HANDLER.setFormatter(LOG_FORMATTER)
        LOG.addHandler(LOG_STREAM_HANDLER)
except ImportError:
    pass

# always add stdout handler
LOG_STD_OUT_HANDLER = logging.StreamHandler(sys.__stdout__)
LOG_STD_OUT_HANDLER.setLevel("INFO")
LOG_STD_OUT_HANDLER.setFormatter(LOG_FORMATTER)
LOG.addHandler(LOG_STD_OUT_HANDLER)
