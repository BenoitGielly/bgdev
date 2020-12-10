"""Custom plugin manager for Maya.

:created: 10/07/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from collections import defaultdict
import fnmatch
from functools import partial
import os

from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds, mel


class FrameLayout(QtWidgets.QGroupBox):
    """Improved version of the QGroupBox to make it look like the Maya FrameLayout."""

    def __init__(self, *args, **kwargs):
        super(FrameLayout, self).__init__(*args, **kwargs)

        # set properties
        self.setFlat(True)
        self.setCheckable(True)
        self.setStyleSheet(self.css())
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # create layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)

        # create frame
        self.frame = QtWidgets.QFrame(self)
        frame_layout = QtWidgets.QVBoxLayout(self.frame)
        main_layout.addWidget(self.frame)

        # add a small spacing between the title and the content
        self.title_spacing = QtWidgets.QLabel(self.frame)
        self.title_spacing.setMaximumHeight(7)
        frame_layout.addWidget(self.title_spacing)

        # setup signals
        self.toggled.connect(partial(self.frame.setVisible))

    @staticmethod
    def css():
        """Stylesheet for the groupbox """

        css = (
            "QGroupBox {font: bold helvetica} "
            "QGroupBox::title {padding-right: 10000} "
            "QGroupBox::title {background-color: rgb(93,93,93)} "
            "QGroupBox::indicator {width: 20; height: 20} "
            "QGroupBox::indicator:checked {image: url(:/arrowDown.png)} "
            "QGroupBox::indicator:unchecked {image: url(:/arrowRight.png)} "
        )

        return css

    def layout(self, frame=True):
        """Returns the layout attached to the frame instead of the groupbox.

        Args:
            frame (bool): If True, returns the frame's layout, else the groupbox
        """

        if frame:
            return self.frame.layout()
        return self.layout()

    def mouseReleaseEvent(self, event):
        """Overriding the mouseRelease event """

        mouse = QtCore.Qt.MouseButton
        if event.button() == mouse.LeftButton:
            if not self.frame.underMouse():
                self.setChecked(1 - self.isChecked())


class PluginsManager(QtWidgets.QDialog):
    """Improved version of the Maya's plug-in manager that allows filtering."""

    def __init__(self, *args, **kwargs):
        """Class constructor."""
        super(PluginsManager, self).__init__(*args, **kwargs)

        # source pluginWindow mel file first to init some maya crap
        location = mel.eval("whatIs pluginWin.mel")
        plugin = location.split(":", 1)[-1].strip()
        mel.eval('source "{}"'.format(plugin))

        self.check_instance()
        self.setWindowTitle("Plug-in Manager")
        self.setObjectName("bg_PluginManager")
        self.plugins = self.gather_maya_plugins()
        self.ui_data = {}
        self.all_plugins = {}
        self.setup_ui()
        self.resize(600, 800)
        self.show()

    @staticmethod
    def check_instance():
        """Close the window if already exists. """
        if cmds.window("bg_PluginManager", exists=True):
            cmds.deleteUI("bg_PluginManager")

    @staticmethod
    def gather_maya_plugins():
        """Gather plugins based on the MAYA_PLUG_IN_PATH."""

        plugins = defaultdict(set)
        for path in os.environ.get("MAYA_PLUG_IN_PATH").split(":"):
            if os.path.isdir(path):
                for each in os.listdir(path):
                    if any([each.endswith(_) for _ in [".py", ".pyc", ".so"]]):
                        plugins[path].add(each)

        return plugins

    @staticmethod
    def load_plugin(path, plugin, load):
        """Load or unload the given plugin."""

        fullname = os.path.join(path, plugin)
        if load is True:
            cmds.loadPlugin(fullname, quiet=True)
        else:
            cmds.unloadPlugin(plugin)

    @staticmethod
    def autoload_plugin(path, plugin, load):
        """Set autoload of given plugin."""

        fullname = os.path.join(path, plugin)
        cmds.pluginInfo(fullname, edit=True, autoload=load)

    @staticmethod
    def get_plugin_info(path, plugin):
        """Get the loaded and autoload information for given plugin."""

        fullname = os.path.join(path, plugin)
        loaded, autoload, _ = cmds.pluginInfo(
            fullname, query=True, settings=True
        )

        return loaded, autoload

    @staticmethod
    def display_plugin_info(path, plugin):
        """Display the PluginInfo window for given plugin path/plug."""

        fullname = os.path.join(path, plugin)
        if cmds.pluginInfo(fullname, query=True, loaded=True):
            mel.eval('displayPluginInfo "{}";'.format(fullname))

    def filter_plugins(self, text):
        """Filter the list of plugins based on input text."""

        filtered = fnmatch.filter(
            self.all_plugins.values(), "*" + text.lower() + "*"
        )

        for widget, name in self.all_plugins.items():

            if text and name not in filtered:
                widget.hide()
            else:
                widget.show()

    def collapse_all(self, collapsed=True):
        """Collapse/uncollapse all the groupboxes."""

        for _, widgets in self.ui_data.items():
            widgets.get("group").setChecked(1 - collapsed)

    def setup_ui(self):
        """Create the UI."""

        # set layout to ui
        self.ui_layout = QtWidgets.QVBoxLayout(self)
        self.ui_layout.setContentsMargins(5, 5, 5, 5)

        # add filter bar
        self.filter_layout = QtWidgets.QHBoxLayout()
        self.filter_label = QtWidgets.QLabel("Filter :")
        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.textEdited.connect(partial(self.filter_plugins))

        self.collapse_btn = QtWidgets.QToolButton()
        self.collapse_btn.setAutoRaise(True)
        self.collapse_btn.setCheckable(True)
        self.collapse_btn.setIcon(QtGui.QIcon(":/nodeGrapherToggleView.png"))
        self.collapse_btn.toggled.connect(partial(self.collapse_all))

        self.filter_layout.addWidget(self.filter_label)
        self.filter_layout.addWidget(self.filter_text)
        self.filter_layout.addWidget(self.collapse_btn)
        self.ui_layout.addLayout(self.filter_layout)

        # create main widget and layout
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(0)

        # create frameLayout based on plugin data
        for path, value in sorted(self.plugins.items()):
            widgets = {}

            widgets["group"] = FrameLayout(path, self)
            widgets["group"].layout().setSpacing(0)
            self.main_layout.addWidget(widgets["group"])

            # populate plugins
            widgets["plugins"] = {}
            for each in sorted(value):
                plugins = {}

                plugins["widget"] = QtWidgets.QWidget()
                plugins["layout"] = QtWidgets.QHBoxLayout(plugins["widget"])
                plugins["layout"].setSpacing(20)
                plugins["layout"].setContentsMargins(0, 0, 0, 0)

                widgets["group"].layout().addWidget(plugins["widget"])

                plugins["label"] = QtWidgets.QLabel(each)

                loaded, autoload = self.get_plugin_info(path, each)
                plugins["loaded"] = QtWidgets.QCheckBox("Loaded")
                plugins["loaded"].setChecked(loaded)
                plugins["autoload"] = QtWidgets.QCheckBox("Auto load")
                plugins["autoload"].setChecked(autoload)

                plugins["info"] = QtWidgets.QToolButton()
                plugins["info"].setEnabled(loaded)
                plugins["info"].setAutoRaise(True)
                plugins["info"].setIcon(QtGui.QIcon(":/info.png"))
                plugins["info"].setIconSize(QtCore.QSize(14, 14))

                plugins["layout"].addWidget(plugins["label"])
                plugins["layout"].addStretch()
                plugins["layout"].addWidget(plugins["loaded"])
                plugins["layout"].addWidget(plugins["autoload"])
                plugins["layout"].addWidget(plugins["info"])

                # setup signals
                plugins["loaded"].toggled.connect(
                    partial(plugins["info"].setEnabled)
                )
                plugins["loaded"].toggled.connect(
                    partial(self.load_plugin, path, each)
                )
                plugins["autoload"].toggled.connect(
                    partial(self.autoload_plugin, path, each)
                )
                plugins["info"].clicked.connect(
                    partial(self.display_plugin_info, path, each)
                )

                # update data
                widgets["plugins"].update({each: plugins})
                self.all_plugins[plugins["widget"]] = each.lower()

            # update ui data dictionary
            self.ui_data.update({path: widgets})

        # push the groups to the top
        self.main_layout.addStretch()

        # set scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.main_widget)
        self.scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui_layout.addWidget(self.scroll_area)

        # add close button
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.ui_layout.addWidget(self.close_btn)
