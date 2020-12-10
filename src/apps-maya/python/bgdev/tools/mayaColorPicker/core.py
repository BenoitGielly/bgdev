"""Color picker for Maya. (old)

:created: 25/02/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from functools import partial

from PySide2 import QtWidgets
from PySide2.QtWidgets import QSizePolicy
import pymel.core as pm


class ColorPicker(QtWidgets.QDialog):
    def __init__(self):
        maya = pm.toQtObject("MayaWindow") or None
        super(ColorPicker, self).__init__(parent=maya)

        # default attrs
        self.color_list = (
            (16, 14, 17, 6, 13, 9, 20, 19),
            (3, 27, 22, 29, 12, 31, 21, 28),
            (2, 23, 25, 15, 4, 30, 24, 18),
            (1, 7, 26, 5, 11, 8, 10),
        )

        # ui setup
        self.setWindowTitle("Maya quick color picker")
        self.setup_ui()

    def setup_ui(self):
        """Create widgets."""
        # create grid
        grid_lay = QtWidgets.QGridLayout(self)
        grid_lay.setSpacing(2)
        grid_lay.setContentsMargins(2, 2, 2, 2)

        i, j = 0, 0
        for j, each in enumerate(self.color_list):
            for i, index in enumerate(each):
                # create btn
                btn = QtWidgets.QPushButton()
                btn.setMaximumSize(18, 18)
                btn.pressed.connect(partial(self.set_color, index))

                # set background color
                bgc = str(
                    tuple([int(x * 254) for x in pm.colorIndex(index, q=True)])
                )
                btn.setStyleSheet("background-color: rgba%s" % bgc)

                # add to grid
                grid_lay.addWidget(btn, j, i)
            grid_lay.setRowStretch(j, 1)

        # add spacers
        v_spacer = QtWidgets.QSpacerItem(
            1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        h_spacer = QtWidgets.QSpacerItem(
            1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        grid_lay.addItem(v_spacer, j + 1, i)
        grid_lay.addItem(h_spacer, j, i + 1)

    @staticmethod
    def set_color(index):
        """Set the given color on selected shapes."""
        selection = pm.selected()
        for each in selection:
            shapes = each.getShapes()
            if shapes:
                for shp in shapes:
                    if shp.hasAttr("overrideEnabled") and shp.hasAttr(
                        "overrideColor"
                    ):
                        shp.overrideEnabled.set(1)
                        shp.overrideColor.set(index)
            else:
                if each.hasAttr("overrideEnabled") and each.hasAttr(
                    "overrideColor"
                ):
                    each.overrideEnabled.set(1)
                    each.overrideColor.set(index)
