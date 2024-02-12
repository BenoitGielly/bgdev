"""Config file to be shared in the toolbar project.

:created: 26/11/2020
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

LOG = logging.getLogger(__name__)

ICON_PATHS = []
COMMAND_CALLBACK = None

SHOW = os.environ.get("STIM_SHOW")
SHOT = os.environ.get("SHOT") or os.environ.get("STIM_SHOT")
LABEL = "{}".format(SHOW or "Toolbar")
