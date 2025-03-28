"""Color utilites.

:created: 08/02/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from qtpy.QtWidgets import QWidget


def convert_css_color(css_color):
    """Convert given color using the qtpy CSS API.

    Args:
        css_color (str): Any color-string you would type in a Widget's CSS.

    Return:
        tuple: The RBG-converted color.

    """
    widget = QWidget()
    widget.setStyleSheet("background-color: " + css_color)
    widget.resize(1, 1)
    widget.show()
    color = widget.palette().background().color()
    widget.deleteLater()

    return tuple(color.getRgbF())
