# pylint: disable=invalid-name
"""PySide Widgets used in the main toolbar code.

:created: 09/11/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from collections import OrderedDict
from functools import partial
import logging

from PySide2 import QtCore, QtGui, QtWidgets

from . import utils

LOG = logging.getLogger(__name__)


class Separator(QtWidgets.QLabel):  # pylint: disable=too-few-public-methods
    """Create a separator line."""

    def __init__(self, height=2):
        super(Separator, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setMaximumHeight(height)


class Header(QtWidgets.QWidget):
    """Create the toolbar's header widget."""

    CSS = """
        #refresh:hover {
            background-color: hsva(80, 50, 50, 100);
            border: 1px solid hsva(120, 250, 200, 200);
        }
        #settings:hover {
            background-color: hsva(80, 50, 50,100);
            border: 1px solid hsva(0, 250, 200, 200);
        }
        QPushButton:pressed{
            background-color: palette(dark);
        }
        QLabel, QPushButton {
            font: bold 12px;
            border: None;
            background-color: hsva(210, 100, 100, 200);
        }
        """

    def __init__(self, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)

        # set properties
        self.setStyleSheet(self.CSS)

        # create widgets
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QtWidgets.QLabel("Launcher", self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setMinimumHeight(30)

        tooltip = "Recreate the toolbar's content."
        self.refresh_btn = self.create_button("refresh", tooltip)

        tooltip = "Open the settings dialog."
        self.settings_btn = self.create_button("settings", tooltip)

        layout.addWidget(self.label)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.settings_btn)

    def create_button(self, name, tooltip=""):
        """Create a header button."""
        icon = "../{0}.png".format(name)
        icon = utils.check_image(icon)

        btn = QtWidgets.QPushButton(self)
        btn.setObjectName(name)
        btn.setStyleSheet(self.CSS)
        btn.setMaximumSize(30, 30)
        btn.setIcon(QtGui.QIcon(icon))
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setToolTip(tooltip)
        btn.setStatusTip(tooltip)

        return btn


class TabWidget(QtWidgets.QTabWidget):
    """Create a custom TabWidget."""

    CSS = """
        QTabBar::tab {
            font: bold 10px;
            color: rgb(180, 180, 180);
            background-color: rgb(100, 60, 60);
            border: 1px solid rgb(40, 40, 40);
        }
        QTabBar::tab:!selected {
            background-color: rgb(55,55,55);
        }
        QTabBar::tab:hover:selected {
            color: rgb(220, 220, 220);
        }
        QTabBar::tab:hover:!selected {
            background-color: rgb(75, 40, 40);
        }
        QTabBar::tab:top, QTabBar::tab:bottom {
            width: %(tab_width)spx;
            height: %(tab_height)spx;
        }
        QTabBar::tab:left, QTabBar::tab:right {
            width: %(tab_height)spx;
            height: %(tab_width)spx;
        }
    """

    def __init__(self, *args, **kwargs):
        super(TabWidget, self).__init__(*args, **kwargs)
        self.tab_width, self.tab_height = (60, 20)
        self.refresh_stylesheet()

    def refresh_stylesheet(self):
        """Refresh the stylesheet."""
        lengths = [len(self.tabText(i)) for i in range(self.count())]
        self.tab_width = 30 + max(lengths) * 6 if lengths else self.tab_width
        self.setStyleSheet(self.CSS % self.__dict__)

    def addTab(self, *args, **kwargs):
        """Refresh styleSheet when adding new tab."""
        super(TabWidget, self).addTab(*args, **kwargs)
        self.refresh_stylesheet()


class ScrollArea(QtWidgets.QScrollArea):
    """Create a custom Scroll Area."""

    CSS = """
        QScrollBar:vertical {
            border: 1px solid rgb(55, 55, 55);
            background: rgb(55, 55, 55);
            width: 12px;
            margin: 12px 0 12px 0;
        }
        QScrollBar::handle:vertical {
            background: rgb(93, 93, 93);
            min-height: 20px;
            border-width: 1px;
            border-radius: 4px;
        }
        QScrollBar::sub-line:vertical {
            background: rgb(55, 55, 55);
            height: 12px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
        QScrollBar::add-line:vertical {
            background: rgb(55, 55, 55);
            height: 12px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
        QScrollBar::up-arrow:vertical {
            image: url(icons/arrow_up.png);
            width: 15px;
            height: 15px;
            padding: 0px 0px 0px 1px /* top - right - bottom - left */
        }
        QScrollBar::down-arrow:vertical {
            image: url(icons/arrow_down.png);
            width: 15px;
            height: 15px;
            padding: 0px 0px 0px 1px /* top - right - bottom - left */
        }
    """

    def __init__(self, *args, **kwargs):
        super(ScrollArea, self).__init__(*args, **kwargs)

        # set properties
        self.setStyleSheet(self.CSS)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        # child widget
        self._widget = QtWidgets.QWidget()
        self._layout = QtWidgets.QVBoxLayout(self._widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(1)
        self.setWidget(self.widget)

    @property
    def widget(self):
        """Return the child layout."""
        return self._widget

    @property
    def layout(self):
        """Return the child layout."""
        return self._layout

    def resize_to_children(self):
        """Set the minimum width of the area based on children sizeHints."""
        width = self.get_highest_width()
        self.setMinimumWidth(width)

    def get_highest_width(self):
        """Return the highest width of all children."""
        width = float("-inf")
        for i in range(self._layout.count()):
            widget = self._layout.itemAt(i)
            size = widget.sizeHint()
            if size.width() > width:
                width = size.width()
        return width + 40

    def addWidget(self, *args, **kwargs):
        """Add given widget to the widget's layout."""
        self.layout.addWidget(*args, **kwargs)

    def addLayout(self, *args, **kwargs):
        """Add given layout to the widget's layout."""
        self.layout.addLayout(*args, **kwargs)

    def addStretch(self, *args, **kwargs):
        """Add stretch to the widget's layout."""
        self.layout.addStretch(*args, **kwargs)

    def setStretch(self, *args, **kwargs):
        """Set the stretch ration of the widget's layout."""
        self.layout.setStretch(*args, **kwargs)


class GroupBox(QtWidgets.QGroupBox):
    """Create a custom groupBox."""

    CSS = """
        GroupBox {
            font: bold;
            border: none;
        }
        GroupBox::title {
            padding-right: 10000;
            background-color: %(color)s;
        }
        GroupBox::indicator {
            width: %(height)s;
            height: %(height)s;
        }
        GroupBox::indicator:checked {
            image: url(icons/groupbox_arrow_down.png);
        }
        GroupBox::indicator:unchecked {
            image: url(icons/groupbox_arrow_right.png);
        }
    """

    def __init__(self, title, visible=True, color=None, height=None):
        super(GroupBox, self).__init__()
        self.default_visibility = visible
        self.header_height = height or 20
        header_color = color or "hsv(300, 90, 90)"

        # set properties
        self.setStyleSheet(
            self.CSS % {"color": header_color, "height": self.header_height}
        )
        self.setCheckable(True)
        self.setTitle(title)
        self.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
        self.setFlat(True)

        # add a layout
        main_layout = QtWidgets.QVBoxLayout(self)
        top = self.header_height if self.header_height > 0 else 1
        main_layout.setContentsMargins(0, top, 0, 0)
        main_layout.setSpacing(0)

        # create content widget
        self.widget = QtWidgets.QWidget(self)
        main_layout.addWidget(self.widget)

        self._layout = QtWidgets.QVBoxLayout(self.widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(1)

        # set signal and visibility
        self.setChecked(self.default_visibility)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

    def setChecked(self, checked):
        """Add the widget visibility toggle to the setChecked method."""
        super(GroupBox, self).setChecked(checked)
        self.widget.setVisible(checked)

    def mouseReleaseEvent(self, event):
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

    @property
    def layout(self):
        """Return the child layout."""
        return self._layout

    def addWidget(self, *args, **kwargs):
        """Add given widget to the widget's layout."""
        self.layout.addWidget(*args, **kwargs)

    def addLayout(self, *args, **kwargs):
        """Add given layout to the widget's layout."""
        self.layout.addLayout(*args, **kwargs)

    def addStretch(self, *args, **kwargs):
        """Add stretch to the widget's layout."""
        self.layout.addStretch(*args, **kwargs)

    def setStretch(self, *args, **kwargs):
        """Set the stretch ration of the widget's layout."""
        self.layout.setStretch(*args, **kwargs)


class PushButton(QtWidgets.QPushButton):
    """Create a nice button for the GUI."""

    CSS = """
        QPushButton:hover {
            background-color:palette(highlight);
            border:1px solid #C90;
        }

        QPushButton:pressed {
            background-color: palette(dark);
        }
    """

    alt_clicked = QtCore.Signal()

    def __init__(self, name="", parent=None, settings=None):
        super(PushButton, self).__init__(parent)

        # properties
        self._settings = settings or {}
        self.setStyleSheet(self.CSS)
        self.setMinimumHeight(26)  # with icons, size is raised to 26

        self.setText(self._settings.get("label", name))
        self.setToolTip(name)
        self.setStatusTip(name)

        icon = self._settings.get("image", "")
        icon = utils.check_image(icon)
        if icon:
            self.setIcon(QtGui.QIcon(icon))

        command = self._settings.get("source", "")
        self.clicked.connect(partial(self.set_command, command))

        alt_command = self._settings.get("alt_source", "")
        self.alt_clicked.connect(partial(self.set_command, alt_command))

    def mousePressEvent(self, event):
        """Run menu when right-click button is pressed instead of clicked."""
        modifiers = QtWidgets.QApplication.queryKeyboardModifiers()
        is_valid = modifiers in (
            QtCore.Qt.AltModifier,
            QtCore.Qt.ControlModifier,
            QtCore.Qt.ShiftModifier,
        )
        if event.button() == QtCore.Qt.MouseButton.LeftButton and is_valid:
            self.alt_clicked.emit()
            return

        super(PushButton, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.context_menu()

    def context_menu(self, pos=None):
        """Create a right click menu."""
        pos = pos if pos else QtGui.QCursor.pos()
        menus = self._settings.get("menu", OrderedDict())
        if not menus:
            return

        # setup the menu from data
        menu = QtWidgets.QMenu(self)
        for name, menu_data in menus.items():
            label = menu_data.get("label", name)
            source = menu_data.get("source", "")
            menu.addAction(label, partial(self.set_command, source))

        # run the menu
        menu.exec_(pos)
        self.update()

    def set_command(self, source):
        """Set the command for each buttons."""
        callback = utils.create_module_callback(source)
        if not callback:
            return

        # run the callback and make it repeatable
        try:
            callback()
            self.repeatable(callback)
        except Exception:  # pylint: disable=broad-except
            LOG.error("", exc_info=True)

    @staticmethod
    def repeatable(callback):
        """Make the command repeatable.

        Args:
            callback (function): Method executed by the button.

        Returns:
            method: The method passed in.

        Note:
            This method needs to be overwritten by DDCs with their own
            command in order to make the button command repeateable.
        """
        return callback


class IconButton(PushButton):
    """Custom PushButton with just an icon displayed."""

    _CSS = """
        QPushButton {
            background-color: rgba(0, 0, 0, 0);
            border: 1px rgba(0, 0, 0, 50);
        }
    """
    CSS = PushButton.CSS + _CSS

    def __init__(self, *args, **kwargs):
        super(IconButton, self).__init__(*args, **kwargs)

        size = QtCore.QSize(41, 41)
        self.setMaximumSize(size)
        self.setMinimumSize(size)
        self.setIconSize(size * 0.90)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setText("")

        # add a label on the button
        text = kwargs.get("settings", {}).get("label", "")
        self.add_label(str.encode(text).decode("unicode_escape"))

    def add_label(self, text):
        """Add a text label onto the button."""
        if not text:
            return
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        label = QtWidgets.QLabel(self)
        layout.addStretch()
        layout.addWidget(label)
        label.setText(text)
        css = """
            font: bold 8px 'helvetica';
            color: white;
            background-color: hsva(0, 0, 0, 150);
        """
        label.setStyleSheet(css)
        label.setAlignment(QtCore.Qt.AlignCenter)


class LabelWidget(QtWidgets.QWidget):
    """Create a separator line."""

    CSS = """
        QLabel#RowLabel {
            font: bold italic 11px 'helvetica';
        }
    """

    def __init__(self, text):
        super(LabelWidget, self).__init__()
        self.text = text
        self.setup_ui()

    def setup_ui(self):
        """Create ui widgets."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.upper_separator = Separator(5)
        self.lower_separator = Separator(5)

        self.label = QtWidgets.QLabel(self.text, self)
        self.label.setObjectName("RowLabel")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setMinimumHeight(24)
        self.label.setStyleSheet(self.CSS)

        layout.addWidget(self.upper_separator)
        layout.addWidget(self.label)
        layout.addWidget(self.lower_separator)
