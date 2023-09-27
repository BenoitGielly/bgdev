"""Main UI for the renamer.

:created: 06/04/2016
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from functools import partial

from PySide2 import QtCore, QtWidgets

from .utils import check_image


def maya_window():
    """Return the MayaWindow if in Maya else None."""
    for each in QtWidgets.QApplication.topLevelWidgets():
        if each.objectName() == "MayaWindow":
            return each
    return None


class GroupBox(QtWidgets.QGroupBox):
    """Create a custom groupBox."""

    def __init__(self, title, visible=True, color=None, height=None):
        super(GroupBox, self).__init__()
        self.default_visibility = visible
        self.header_color = color or "palette(light)"
        self.header_height = height or 24

        # set properties
        self.setStyleSheet(self.css)
        self.setCheckable(True)
        self.setTitle(title)
        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.setFlat(True)

        # add a layout
        main_layout = QtWidgets.QVBoxLayout(self)
        top = self.header_height
        main_layout.setContentsMargins(0, top if top > 0 else 1, 0, 0)
        main_layout.setSpacing(0)

        # create content widget
        self.widget = QtWidgets.QFrame(self)
        main_layout.addWidget(self.widget)
        self.layout = QtWidgets.QVBoxLayout(self.widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1)

        # set signal and visibility
        self.setChecked(self.default_visibility)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

    def set_style(self, shape, shadow):
        """Set the children frame style.

        Args:
            shape (str): Any property belonging to QtWidgets.QFrame.Shape
            shadow (str): Any property belonging to QtWidgets.QFrame.Shadow
        """
        shape = getattr(self.widget, shape, None)
        if shape:
            self.widget.setFrameShape(shape)

        shadow = getattr(self.widget, shadow, None)
        if shadow:
            self.widget.setFrameShadow(shadow)

    @property
    def css(self):
        """Create the styleSheet for the groupBox."""
        css = """
            GroupBox {
                font: bold;
                border: none;
            }
            GroupBox::title {
                padding-right: 10000;
                background-color: %s;
            }
            GroupBox::indicator {
                width: %s;
                height: %s;
            }
            GroupBox::indicator:checked {
                image: url(%s);
            }
            GroupBox::indicator:unchecked {
                image: url(%s);
            }
        """
        css = css % (
            self.header_color,
            self.header_height,
            self.header_height,
            check_image("../arrow_down.png", normalized=True),
            check_image("../arrow_right.png", normalized=True),
        )

        return css

    def setChecked(self, checked):  # pylint: disable=invalid-name
        """Add the widget visibility toggle to the setChecked method."""
        super(GroupBox, self).setChecked(checked)
        self.widget.setVisible(checked)

    def mouseReleaseEvent(self, event):  # pylint: disable=invalid-name
        """Trigger the setChecked method when mouse is released."""
        pos_y = event.pos().y()
        if pos_y < self.header_height:
            self.setChecked(1 - self.isChecked())
            self.shift_expand()

    def shift_expand(self):
        """Expand all siblings when shift is pressed.

        Note:
            Pressing "Ctrl" will reset the visibility to default.
        """
        modifier = QtWidgets.QApplication.queryKeyboardModifiers()
        if modifier != QtCore.Qt.ShiftModifier:
            return

        siblings = []
        for each in self.parent().children() or []:
            if isinstance(each, GroupBox):
                siblings.append(each)

        visibility = self.isChecked()
        index = siblings.index(self) or 0
        for each in siblings[index::]:
            each.setChecked(visibility)


class RenamerUi(QtWidgets.QDialog):
    """Main UI for the renamer."""

    def __init__(self, *args, **kwargs):
        parent = kwargs.pop("parent", None) or maya_window()
        super(RenamerUi, self).__init__(parent=parent, *args, **kwargs)

        # get icons
        self.icons = {}
        for each in ["rename", "add", "remove", "replace"]:
            name = "../{0}.png".format(each)
            self.icons[each] = check_image(name, as_icon=True)

        # set properties
        self.setWindowTitle("Renamer")
        self.setStyleSheet(self.css)
        self.setup_ui()

    @property
    def css(self):
        """Return the CSS string."""
        return """
            QWidget, Qlabel {
                font: 9pt utopia;
                color: rgb(220,220,220)
            }
            QLineEdit {
                font: 10pt helvetica;
                background-color: None
            }
        """

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Override the keyPressedEvent to avoid Maya taking focus out."""
        pass

    def hash_rename(self, text=None, start=None, letters=None):
        """Override this method in the main class."""
        pass

    def search_replace(self, search=None, replace=None, hierarchy=None):
        """Override this method in the main class."""
        pass

    def prefix_suffix(self, prefix=None, suffix=None, mode=None):
        """Override this method in the main class."""
        pass

    def setup_ui(self):  # pylint: disable=too-many-statements, too-many-locals
        """Create widgets."""
        main_layout = QtWidgets.QVBoxLayout(self)

        # --- HASH RENAME
        hash_box = GroupBox("Hash rename", color="None")

        hash_row1 = QtWidgets.QHBoxLayout()
        hash_row1.setSpacing(5)
        hash_row1.setContentsMargins(2, 2, 2, 2)
        hash_box.layout.addLayout(hash_row1)

        self.hash_text = QtWidgets.QLineEdit(hash_box)
        tip = 'Use hashes ("##") for padding'
        self.hash_text.setToolTip(tip)
        self.hash_text.setStatusTip(tip)
        self.hash_text.setPlaceholderText(" L name ## suffix")
        self.hash_text.returnPressed.connect(self.hash_rename)

        hash_start_label = QtWidgets.QLabel(hash_box)
        tip = "Choose the start index"
        hash_start_label.setToolTip(tip)
        hash_start_label.setStatusTip(tip)
        hash_start_label.setText("Start :")

        self.hash_spinbox = QtWidgets.QSpinBox(hash_box)
        self.hash_spinbox.setMinimum(1)
        tip = "Choose the start index"
        self.hash_spinbox.setToolTip(tip)
        self.hash_spinbox.setStatusTip(tip)

        hash_row1.addWidget(self.hash_text)
        hash_row1.addWidget(hash_start_label)
        hash_row1.addWidget(self.hash_spinbox)
        hash_row1.setStretch(0, 1)

        hash_row2 = QtWidgets.QHBoxLayout()
        hash_row2.setSpacing(0)
        hash_row2.setContentsMargins(2, 2, 2, 2)
        hash_box.layout.addLayout(hash_row2)

        self.hash_number_radio = QtWidgets.QRadioButton(hash_box)
        self.hash_number_radio.setChecked(True)
        tip = 'Replace hashes ("##") with numbers'
        self.hash_number_radio.setToolTip(tip)
        self.hash_number_radio.setStatusTip(tip)
        self.hash_number_radio.setText("Numbers")

        self.hash_letters_radio = QtWidgets.QRadioButton(hash_box)
        tip = 'Replace hashes ("##") with letters'
        self.hash_letters_radio.setToolTip(tip)
        self.hash_letters_radio.setStatusTip(tip)
        self.hash_letters_radio.setText("Letters")

        hash_rename_btn = QtWidgets.QPushButton(hash_box)
        hash_rename_btn.setMaximumWidth(30)
        hash_rename_btn.setMinimumHeight(26)
        hash_rename_btn.setIcon(self.icons["rename"])
        hash_rename_btn.setToolTip("Execute hash renamer")
        hash_rename_btn.setStatusTip("Execute hash renamer")
        hash_rename_btn.clicked.connect(self.hash_rename)

        hash_row2.addWidget(self.hash_number_radio)
        hash_row2.addWidget(self.hash_letters_radio)
        hash_row2.addWidget(hash_rename_btn)

        main_layout.addWidget(hash_box)

        # SEARCH AND REPLACE ---
        snr_box = GroupBox("Search and replace", color="None")

        self.search_text = QtWidgets.QLineEdit(snr_box)
        tip = "Type in string to search"
        self.search_text.setToolTip(tip)
        self.search_text.setStatusTip(tip)
        self.search_text.setPlaceholderText(" Search")
        self.search_text.returnPressed.connect(self.search_replace)

        self.replace_text = QtWidgets.QLineEdit(snr_box)
        tip = "Type in string to replace with"
        self.replace_text.setStatusTip(tip)
        self.replace_text.setWhatsThis(tip)
        self.replace_text.setPlaceholderText(" Replace")
        self.replace_text.returnPressed.connect(self.search_replace)

        snr_box.layout.addWidget(self.search_text)
        snr_box.layout.addWidget(self.replace_text)

        snr_row = QtWidgets.QHBoxLayout()
        snr_row.setSpacing(0)
        snr_row.setContentsMargins(2, 2, 2, 2)
        snr_box.layout.addLayout(snr_row)

        self.select_radio = QtWidgets.QRadioButton(snr_box)
        self.select_radio.setChecked(True)
        tip = "Affects the current selection"
        self.select_radio.setToolTip(tip)
        self.select_radio.setStatusTip(tip)
        self.select_radio.setText("Select")

        self.hierarchy_radio = QtWidgets.QRadioButton(snr_box)
        tip = "Affects the whole hierarchy under selection"
        self.hierarchy_radio.setToolTip(tip)
        self.hierarchy_radio.setStatusTip(tip)
        self.hierarchy_radio.setText("Hierarchy")

        snr_rename_btn = QtWidgets.QPushButton(snr_box)
        snr_rename_btn.setMaximumWidth(30)
        snr_rename_btn.setMinimumHeight(26)
        snr_rename_btn.setIcon(self.icons["rename"])
        tip = "Execute search & replace"
        snr_rename_btn.setToolTip(tip)
        snr_rename_btn.setStatusTip(tip)
        snr_rename_btn.clicked.connect(self.search_replace)

        snr_row.addWidget(self.select_radio)
        snr_row.addWidget(self.hierarchy_radio)
        snr_row.addWidget(snr_rename_btn)

        main_layout.addWidget(snr_box)

        # PREFIX AND SUFFIX ---
        pns_box = GroupBox("Prefix and suffix", color="None")

        prefix_row = QtWidgets.QHBoxLayout()
        prefix_row.setSpacing(0)
        prefix_row.setContentsMargins(2, 2, 2, 2)
        pns_box.layout.addLayout(prefix_row)

        self.prefix_text = QtWidgets.QLineEdit(pns_box)
        self.prefix_text.setStatusTip("Type prefix here")
        self.prefix_text.setWhatsThis("Type prefix here")
        self.prefix_text.setPlaceholderText(" Prefix")
        cmd = partial(self.prefix_suffix, prefix=True, mode="replace")
        self.prefix_text.returnPressed.connect(cmd)

        prefix_replace_btn = QtWidgets.QPushButton(pns_box)
        prefix_replace_btn.setMaximumWidth(30)
        prefix_replace_btn.setMinimumHeight(26)
        prefix_replace_btn.setIcon(self.icons["replace"])
        tip = "Replace current prefix with given one"
        prefix_replace_btn.setToolTip(tip)
        prefix_replace_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, prefix=True, mode="replace")
        prefix_replace_btn.clicked.connect(cmd)

        prefix_add_btn = QtWidgets.QPushButton(pns_box)
        prefix_add_btn.setMaximumWidth(30)
        prefix_add_btn.setMinimumHeight(26)
        prefix_add_btn.setIcon(self.icons["add"])
        tip = "Add given prefix"
        prefix_add_btn.setToolTip(tip)
        prefix_add_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, prefix=True, mode="add")
        prefix_add_btn.clicked.connect(cmd)

        prefix_remove_btn = QtWidgets.QPushButton(pns_box)
        prefix_remove_btn.setMaximumWidth(30)
        prefix_remove_btn.setMinimumHeight(26)
        prefix_remove_btn.setIcon(self.icons["remove"])
        tip = "Remove current prefix"
        prefix_remove_btn.setToolTip(tip)
        prefix_remove_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, prefix=True, mode="remove")
        prefix_remove_btn.clicked.connect(cmd)

        prefix_row.addWidget(self.prefix_text)
        prefix_row.addWidget(prefix_replace_btn)
        prefix_row.addWidget(prefix_add_btn)
        prefix_row.addWidget(prefix_remove_btn)
        prefix_row.setStretch(0, 1)

        suffix_row = QtWidgets.QHBoxLayout()
        suffix_row.setSpacing(0)
        suffix_row.setContentsMargins(2, 2, 2, 2)
        pns_box.layout.addLayout(suffix_row)

        self.suffix_text = QtWidgets.QLineEdit(pns_box)
        tip = "Type suffix here"
        self.suffix_text.setStatusTip(tip)
        self.suffix_text.setWhatsThis(tip)
        self.suffix_text.setPlaceholderText(" Suffix")
        cmd = partial(self.prefix_suffix, suffix=True, mode="replace")
        self.suffix_text.returnPressed.connect(cmd)

        suffix_replace_btn = QtWidgets.QPushButton(pns_box)
        suffix_replace_btn.setMaximumWidth(30)
        suffix_replace_btn.setMinimumHeight(26)
        suffix_replace_btn.setIcon(self.icons["replace"])
        tip = "Replace current suffix with given one"
        suffix_replace_btn.setToolTip(tip)
        suffix_replace_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, suffix=True, mode="replace")
        suffix_replace_btn.clicked.connect(cmd)

        suffix_add_btn = QtWidgets.QPushButton(pns_box)
        suffix_add_btn.setMaximumWidth(30)
        suffix_add_btn.setMinimumHeight(26)
        suffix_add_btn.setIcon(self.icons["add"])
        tip = "Add given suffix"
        suffix_add_btn.setToolTip(tip)
        suffix_add_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, suffix=True, mode="add")
        suffix_add_btn.clicked.connect(cmd)

        suffix_remove_btn = QtWidgets.QPushButton(pns_box)
        suffix_remove_btn.setMaximumWidth(30)
        suffix_remove_btn.setMinimumHeight(26)
        suffix_remove_btn.setIcon(self.icons["remove"])
        tip = "Remove current suffix"
        suffix_remove_btn.setToolTip(tip)
        suffix_remove_btn.setStatusTip(tip)
        cmd = partial(self.prefix_suffix, suffix=True, mode="remove")
        suffix_remove_btn.clicked.connect(cmd)

        suffix_row.addWidget(self.suffix_text)
        suffix_row.addWidget(suffix_replace_btn)
        suffix_row.addWidget(suffix_add_btn)
        suffix_row.addWidget(suffix_remove_btn)
        suffix_row.setStretch(0, 1)

        main_layout.addWidget(pns_box)
        main_layout.addStretch()
