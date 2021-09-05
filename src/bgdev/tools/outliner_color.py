"""Tool to quickly update outliner color of selected nodes.

:created: 11/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from functools import partial

from PySide2 import QtGui, QtWidgets
from maya import cmds


class Separator(QtWidgets.QLabel):  # pylint: disable=too-few-public-methods
    """Create a separtor line."""

    def __init__(self):
        super(Separator, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setMaximumHeight(20)


class OutlinerColorPicker(QtWidgets.QDialog):
    """Set outlinerColor on selection."""

    def __init__(self):
        super(OutlinerColorPicker, self).__init__()
        self.setWindowTitle("Outliner Color Picker")
        self.setup_ui()

    def setup_ui(self):
        """Create widgets."""
        main_layout = QtWidgets.QVBoxLayout(self)

        # create selection layout
        selection_layout = QtWidgets.QHBoxLayout()
        self.selection_list = QtWidgets.QListWidget(self)
        self.selection_list.setSelectionMode(
            self.selection_list.SelectionMode.ContiguousSelection
        )

        # create command layout
        command_layout = QtWidgets.QVBoxLayout()
        command_layout.setSpacing(2)

        add_items_button = QtWidgets.QPushButton("Add items", self)
        add_items_button.clicked.connect(self.get_selection)

        clear_items_button = QtWidgets.QPushButton("Clear items", self)
        clear_items_button.clicked.connect(self.selection_list.clear)

        items_separator = Separator()

        set_color_button = QtWidgets.QPushButton("Set color", self)
        set_color_button.clicked.connect(partial(self.update_color))

        reset_color_button = QtWidgets.QPushButton("Reset color", self)
        reset_color_button.clicked.connect(partial(self.reset_selection_color))

        color_separator = Separator()

        reset_all_button = QtWidgets.QPushButton("Reset all", self)
        reset_all_button.clicked.connect(
            partial(self.reset_selection_color, True)
        )

        self.color_button = QtWidgets.QPushButton("", self)
        self.color_button.setMinimumHeight(100)
        self.color_button.setMinimumWidth(100)
        self.color_button.setStyleSheet("background-color: yellow;")
        self.color_button.clicked.connect(self.exec_color_picker)

        command_layout.addWidget(add_items_button)
        command_layout.addWidget(clear_items_button)
        command_layout.addWidget(items_separator)

        command_layout.addWidget(set_color_button)
        command_layout.addWidget(reset_color_button)
        command_layout.addWidget(self.color_button)
        command_layout.addWidget(color_separator)

        command_layout.addWidget(reset_all_button)
        command_layout.addStretch()

        selection_layout.addWidget(self.selection_list)
        selection_layout.addLayout(command_layout)

        main_layout.addLayout(selection_layout)

        # close button
        close_button = QtWidgets.QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button)

    def get_items(self):
        """Get items in the listWidget by name."""
        count = self.selection_list.count()
        items = [self.selection_list.item(i).text() for i in range(count)]
        return items

    def get_selection(self):
        """Fill the ListWidget with current selection."""
        selection = cmds.ls(selection=True) or []
        self.selection_list.clear()
        self.selection_list.addItems(sorted(selection))
        cmds.select(clear=True)

    def reset_selection_color(self, all_items=False):
        """Reset color on selectionned items."""
        nodes = []
        if all_items:
            for each in cmds.ls("*.useOutlinerColor"):
                if cmds.getAttr(each):
                    nodes.append(each.rsplit(".")[0])
        else:
            nodes = self.get_items()

        for each in nodes:
            if cmds.objExists(each + ".useOutlinerColor"):
                cmds.setAttr(each + ".useOutlinerColor", False)
        if nodes:
            cmds.select(nodes[0])
            cmds.select(clear=True)

    def exec_color_picker(self):
        """Execute the colorPicker."""
        color_dialog = QtWidgets.QColorDialog(self)
        color_dialog.currentColorChanged.connect(partial(self.update_color))
        color = self.color_button.palette().color(QtGui.QPalette.Background)
        color_dialog.setCurrentColor(color)
        color_dialog.show()

    def update_color(self, color=None):
        """Update color on items in the listWidget."""
        if not color:
            color = self.color_button.palette().color(
                QtGui.QPalette.Background
            )

        rgb = color.getRgbF()
        items = self.get_items()
        for each in items:
            cmds.setAttr(each + ".useOutlinerColor", True)
            cmds.setAttr(each + ".outlinerColor", *rgb[0:3])
        self.color_button.setStyleSheet(
            "background-color: rgba%s;" % str(color.getRgb())
        )

        if items:
            cmds.select(items[0])
            cmds.select(clear=True)
