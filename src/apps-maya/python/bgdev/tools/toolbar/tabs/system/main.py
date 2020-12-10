# pylint: disable=invalid-name
"""Maya toolbar override.

:created: 14/10/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging
import os
import sys

from PySide2 import QtWidgets

from ... import main

LOG = logging.getLogger(__name__)


def show():
    """Show the window."""
    qapp = QtWidgets.QApplication(sys.argv)
    toolbar = Toolbar()
    toolbar.show()
    qapp.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    sys.exit(qapp.exec_())


class Toolbar(main.BaseToolbar):
    """Create a script launcher window."""

    # DCC_TABS_FOLDER = os.path.dirname(__file__)
    DCC_TABS_FOLDER = os.path.dirname(__file__).replace("system", "maya")

    def __init__(self, parent=None):
        super(Toolbar, self).__init__(parent=parent)
        css = """
            QWidget {
                color: rgb(200, 200, 200);
                background-color: rgb(68, 68, 68);
            }
        """
        self.setStyleSheet(css)
        self.setGeometry(356, 180, 150, 1020)
