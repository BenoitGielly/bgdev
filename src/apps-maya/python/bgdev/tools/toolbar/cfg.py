"""Config file to be shared in the toolbar project.

:created: 26/11/2020
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging
import os

LOG = logging.getLogger(__name__)

ICON_PATHS = []
COMMAND_CALLBACK = None
LABEL = "{} | {}".format(
    os.environ.get("SHOW", "Toolbar"), os.environ.get("SHOT")
)
