"""Create an easy attribute setting loop.

:created: 14/10/2016
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import logging

from PySide2 import QtCore, QtWidgets
from maya import cmds

LOG = logging.getLogger(__name__)


def maya_window():
    """Return the MayaWindow if in Maya else None."""
    for each in QtWidgets.QApplication.topLevelWidgets():
        if each.objectName() == "MayaWindow":
            return each
    return None


class LineEdit(QtWidgets.QLineEdit):
    """Customize QLineEdit with an enterPressed signal."""

    enterPressed = QtCore.Signal()

    def __init__(
        self, *args, **kwargs
    ):  # pylint: disable=useless-super-delegation
        super(LineEdit, self).__init__(*args, **kwargs)

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Override press event."""
        super(LineEdit, self).keyPressEvent(event)
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.enterPressed.emit()


class Uniloop(QtWidgets.QDialog):
    """Quick GUI to loop simple commands on selected nodes."""

    def __init__(self, *args, **kwargs):
        """Class init."""
        kwargs.setdefault("parent", maya_window())
        super(Uniloop, self).__init__(*args, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        """Create widgets."""
        # base widget
        self.uni_layout = QtWidgets.QVBoxLayout(self)
        self.uni_layout.setContentsMargins(5, 5, 5, 5)
        self.uni_layout.setSpacing(5)
        self.setWindowTitle("Uniloop 2.0")

        # widgets
        self.uni_attr_label = QtWidgets.QLabel("Attributes :", self)
        self.uni_attr_text = LineEdit(self)
        self.uni_value_label = QtWidgets.QLabel("Value :", self)
        self.uni_value_text = LineEdit(self)
        self.uni_cb = QtWidgets.QCheckBox("Add", self)
        self.uni_selection_rb = QtWidgets.QRadioButton("Selection", self)
        self.uni_type_rb = QtWidgets.QRadioButton("Type", self)
        self.uni_type_text = QtWidgets.QLineEdit(self)
        self.uni_execute_btn = QtWidgets.QPushButton("Execute UniLoop", self)

        # properties
        self.uni_selection_rb.setChecked(1)
        self.uni_attr_label.setMinimumWidth(50)
        self.uni_value_label.setMinimumWidth(50)
        self.uni_type_text.setEnabled(0)

        # signals
        self.uni_type_rb.toggled.connect(self.uni_type_text.setEnabled)
        self.uni_execute_btn.clicked.connect(self.execute)
        self.uni_attr_text.enterPressed.connect(self.execute)
        self.uni_value_text.enterPressed.connect(self.execute)

        # layout
        self.uni_row1_layout = QtWidgets.QHBoxLayout()
        self.uni_row1_layout.addWidget(self.uni_attr_label)
        self.uni_row1_layout.addWidget(self.uni_attr_text)
        self.uni_row1_layout.setStretch(1, 1)

        self.uni_row2_layout = QtWidgets.QHBoxLayout()
        self.uni_row2_layout.addWidget(self.uni_value_label)
        self.uni_row2_layout.addWidget(self.uni_value_text)
        self.uni_row2_layout.addWidget(self.uni_cb)
        self.uni_row2_layout.setStretch(1, 1)

        self.uni_row3_layout = QtWidgets.QHBoxLayout()
        self.uni_row3_layout.addWidget(self.uni_selection_rb)
        self.uni_row3_layout.addWidget(self.uni_type_rb)
        self.uni_row3_layout.addWidget(self.uni_type_text)
        self.uni_row3_layout.setStretch(2, 1)

        self.uni_layout.addLayout(self.uni_row1_layout)
        self.uni_layout.addLayout(self.uni_row2_layout)
        self.uni_layout.addLayout(self.uni_row3_layout)
        self.uni_layout.addWidget(self.uni_execute_btn)

    def execute(self):
        """Run the loop."""
        attribute_list = self.uni_attr_text.text().replace(" ", "").split(",")
        try:
            value = float(self.uni_value_text.text())
        except ValueError:
            value = self.uni_value_text.text()

        if self.uni_selection_rb.isChecked():
            node_list = cmds.ls(selection=True, long=True)
        else:
            type_name = self.uni_type_text.text()
            node_list = cmds.ls(type=type_name, long=True)

        if not node_list:
            if self.uni_selection_rb.isChecked():
                err = "Make sure you selected something!"
            else:
                err = "TypeName is probably wrong. Please double check it!"
            LOG.error(err)
            return

        for each in node_list:
            for attr in attribute_list:
                val = cmds.getAttr(each + "." + attr)
                if self.uni_cb.isChecked():
                    try:
                        cmds.setAttr(each + "." + attr, val + value)
                    except Exception:  # pylint: disable=broad-except
                        LOG.error("", exc_info=True)
                else:
                    try:
                        cmds.setAttr(each + "." + attr, value)
                    except Exception:  # pylint: disable=broad-except
                        LOG.error("", exc_info=True)
