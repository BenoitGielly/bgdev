"""Main toolbar code.

:created: 09/11/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import traceback
from collections import OrderedDict
from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from . import cfg
from . import ui
from . import utils

logging.basicConfig()
LOG = logging.getLogger(__name__)

PROJECT = os.environ.get("PROJECT")
HOME = os.path.normpath(os.environ.get("HOME", os.environ.get("USERPROFILE")))
TABS = os.path.join(".toolbar", "tabs")
ICONS = os.path.join(os.path.dirname(__file__), "icons")


def show(*args, **kwargs):
    """Show the window."""
    dcc_module = utils.get_dcc_package()
    return dcc_module.show(*args, **kwargs)


def get_class_name(cls):
    """Get the class full path name."""
    return "{}.{}".format(cls.__module__, cls.__name__)


class BaseToolbar(QtWidgets.QWidget):
    """Create a script launcher window.

    Args:
        parent (QObject): Instance of parent widget.
    """

    DCC_TABS_FOLDER = None
    PROJECT_TABS_FOLDER = os.path.join(PROJECT, TABS) if PROJECT else ""
    USER_TABS_FOLDER = os.path.join(HOME, TABS) if HOME else ""
    CUSTOM_TABS_FOLDER = os.environ.get("TOOLBAR_PATH", "").split(os.pathsep)

    def __init__(self, parent=None):
        """Initialise the class."""
        super(BaseToolbar, self).__init__(parent=parent)
        self.config_name = ".config.yaml"
        self.setObjectName("Toolbar_mainWindow")

        # default variables
        QtCore.QDir.addSearchPath("bgdev_toolbar_icons", ICONS)
        self.scroll_areas = []
        self.group_boxes = []

        # reset config variables
        cfg.ICON_PATHS = []
        cfg.COMMAND_CALLBACK = None

        # gather data folders
        self.data_folders = [
            self.DCC_TABS_FOLDER,
            self.PROJECT_TABS_FOLDER,
            self.USER_TABS_FOLDER,
        ]
        # self.data_folders.extend([x for x in self.CUSTOM_TABS_FOLDER if x])

        # create the toolbar folder if not exising
        if not os.path.exists(self.USER_TABS_FOLDER):
            os.makedirs(self.USER_TABS_FOLDER)

        # get data files
        self.data_files = self.get_data_files()

        # delete previous instances
        for each in QtWidgets.QApplication.topLevelWidgets():
            bases = [get_class_name(x) for x in type(each).__bases__]
            if (
                each != self
                and each.objectName() == self.objectName()
                and get_class_name(BaseToolbar) in bases
            ):
                each.deleteLater()

        # create ui and setup properties
        self.setWindowTitle("Toolbar")
        self.setup_ui()
        self.adjustSize()
        self.setMinimumWidth(197)

    def get_data_files(self):
        """Find data files based on existing folders."""
        data_files = []
        for path in self.data_folders:
            if not os.path.exists(path or ""):
                continue

            config = None
            if self.config_name in os.listdir(path):
                config = os.path.join(path, self.config_name)

            files = []
            for each in sorted(os.listdir(path)):
                if each.endswith(".yaml") and each != self.config_name:
                    files.append(os.path.join(path, each))

            data_files.append((config, files))

        return data_files

    def setup_ui(self):
        """Create the gui widgets."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # create header widget
        self.header_widget = ui.Header()
        self.header_widget.label.setText(cfg.LABEL)
        self.header_widget.refresh_btn.clicked.connect(self.refresh_content)
        self.header_widget.settings_btn.clicked.connect(
            partial(LOG.warn, "Settings window not yet implemented.")
        )
        main_layout.addWidget(self.header_widget)

        # create tabWidget
        self.tab_widget = ui.TabWidget(self)
        main_layout.addWidget(self.tab_widget)
        self.create_toolbar_content()

    def refresh_content(self):
        """Remove all tabs and recreate them from fresh."""
        self.data_files = self.get_data_files()
        index = self.tab_widget.currentIndex()
        self.tab_widget.clear()
        self.scroll_areas = []
        self.group_boxes = []
        self.create_toolbar_content()
        self.tab_widget.setCurrentIndex(index)

    def create_toolbar_content(self):
        """Create all the widgets for the tab widget."""
        for config, files in self.data_files:
            settings = {}
            if config:
                config_data = utils.yaml_load(config, ordered=True)
                settings = config_data.get("settings", {})

            for data_file in files:
                name = os.path.basename(data_file).rsplit(".")[0]
                content = self.create_tab_content(data_file, settings)
                insert = settings.get("insertAt", -1)
                self.tab_widget.insertTab(insert, content, name.upper())

        # resize window to fit children
        # self.resize_window()

    @staticmethod
    def sort_config(files, data):
        """Sort each files based their basename compared to the ordered list.

        Args:
            files (list): List of file paths.
            data (dict): The tab config data.

        Returns:
            list: The sorted files path.
        """
        names = {os.path.basename(x).rsplit(".")[0]: x for x in files}

        # sort the matching names first
        sorted_data = OrderedDict()
        for each, settings in data.items():
            if each in names:
                settings["path"] = names.get(each)
                sorted_data[each] = settings

        # add the un-found ones after
        for each in sorted(names):
            if each not in sorted_data:
                sorted_data[each] = OrderedDict({"path": names.get(each)})

        return sorted_data

    def resize_window(self):
        """Resize window to fit children."""
        # turn all groupboxes visible
        for group_box in self.group_boxes:
            group_box.setChecked(True)

        # resize scroll area to fit children
        for scroll_area in self.scroll_areas:
            scroll_area.resize_to_children()

        # restore default visibility
        for group_box in self.group_boxes:
            group_box.setChecked(group_box.default_visibility)

    def create_tab_content(self, data_file, settings=None):
        """Create a QWidget to add to the tab."""
        settings = settings or {}
        data = utils.yaml_load(data_file, ordered=True)
        if not data:
            return None

        # append icon path
        path = os.path.join(os.path.dirname(data_file or ""), "icons")
        if path not in cfg.ICON_PATHS:
            cfg.ICON_PATHS.append(path)

        tab_content_widget = QtWidgets.QWidget(self)
        tab_layout = QtWidgets.QVBoxLayout(tab_content_widget)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(2, 2, 2, 2)

        scroll_area = ui.ScrollArea(tab_content_widget)
        tab_layout.addWidget(scroll_area)
        self.scroll_areas.append(scroll_area)

        # read data and create group boxes
        self.group_boxes = []
        for title, group_data in data.items():
            type_ = group_data.get("type", "")

            # parse specific JSON type
            if type_.lower() == "json":
                type_, group_data = self.extract_json_type(group_data)

            # stop here if type is not specified
            if not type_:
                msg = "The 'type' key is missing for %r category. skipped..."
                LOG.warning(msg, title)
                continue

            # extract settings for group_boxes
            visible = group_data.pop("visible", True)
            color = group_data.get("color", settings.get("color"))
            height = group_data.get("height")

            # create group box
            group_box = ui.GroupBox(title, visible, color, height)
            self.group_boxes.append(group_box)
            scroll_area.addWidget(group_box)

            # add a separator line
            line = ui.Separator()
            scroll_area.addWidget(line)

            # create widgets
            if type_ == "custom":
                source = group_data.get("source")
                group_box.addWidget(self.create_custom_widget(source))

            elif type_ == "flow":
                content = group_data.get("content", [])
                group_box.addWidget(self.create_flow_widget(content))

            elif type_ == "box":
                content = group_data.get("content", [])
                for each in content:
                    group_box.addWidget(self.create_box_widget(each))

        # add stretcher and (somehow needs to) force the last child stretch
        scroll_area.layout.addStretch()
        index = scroll_area.layout.count() - 1
        scroll_area.layout.setStretch(index, 1)

        return tab_content_widget

    def extract_json_type(self, data):
        """Extract custom data from an external json file.

        Args:
            data (dict): The current group data to override.

        Returns:
            dict: The updated group data with the external JSON file.
        """
        category = data.get("category")
        env = data.get("env")
        data_file = os.environ.get(env) or data.get("path")

        new_data = utils.yaml_load(data_file, ordered=True)
        category_data = new_data.get(category, {})
        type_ = category_data.get("type")

        return type_, category_data

    def create_custom_widget(self, source):
        """Create a custom widget from source code.

        Warning:
            The source code MUST return the class object and not an instance!

        Args:
            source (str): Source code to import and create the widget.

        Returns:
            QWidget: A QWidget containing the custom widgets.
        """
        base = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(base)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        try:
            callback = utils.create_module_callback(source)
            widget_class = callback()

            class Widget(widget_class):
                """Ensures show method isn't triggered when instanciated."""

                def show(self):
                    """Clean up the show method."""
                    pass

            widget = Widget()

        except Exception:  # pylint: disable=broad-except
            widget = self.create_broken_widget()

        layout.addWidget(widget)

        return base

    def create_flow_widget(self, content):
        """Create widget in either a flow layout.

        Args:
            content (dict): Data about widgets to create.

        Returns:
            QWidget: A parent QWidget containing the widgets in layout.
        """
        base = QtWidgets.QWidget(self)
        flow = ui.FlowLayout(base)
        flow.setContentsMargins(0, 0, 0, 0)
        flow.setSpacing(1)
        for data in content:
            for name, settings in data.items():
                icon_btn = ui.IconButton(name, settings=settings)
                icon_btn.repeatable = self.repeatable
                flow.addWidget(icon_btn)
        return base

    def create_box_widget(self, content):
        """Create widget in either row or column layout.

        Args:
            content (dict): Data about widgets to create.

        Returns:
            QWidget: A parent QWidget containing the widgets in layout.
        """
        base = QtWidgets.QWidget(self)
        if "row" in content:
            layout = QtWidgets.QHBoxLayout(base)
        else:
            layout = QtWidgets.QVBoxLayout(base)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        for widgets in content.values():
            for each in widgets:
                for name, settings in each.items():
                    widget = self.create_type_widget(name, settings)
                    if widget:
                        layout.addWidget(widget)

        return base

    def create_type_widget(self, name, settings):
        """Create a new widget based on the settings.

        Args:
            name (str): Name used as button label.
            settings (dict): Data used to create the widget.

        Returns:
            QObject: Created widget instance.
        """
        widget = None

        if settings.get("type") == "button":
            widget = ui.PushButton(name, settings=settings)
            widget.repeatable = self.repeatable

        elif settings.get("type") == "icon":
            widget = ui.IconButton(name, settings=settings)
            widget.repeatable = self.repeatable

        elif settings.get("type") == "label":
            widget = ui.LabelWidget(name)

        return widget

    def create_broken_widget(self):
        """Create a button for broken widgets."""
        widget = QtWidgets.QPushButton("\tBroken :-/")
        icon = "../broken_icon.png"
        icon = utils.check_image(icon)
        widget.setIcon(QtGui.QIcon(icon))
        widget.clicked.connect(partial(LOG.error, traceback.format_exc()))
        return widget

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
