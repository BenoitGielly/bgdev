# pylint: disable=invalid-name
"""Maya toolbar override.

:created: 14/10/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging
import os

import shiboken2
from PySide2 import QtCore, QtWidgets

from maya import OpenMayaUI, cmds

from ... import cfg, main

LOG = logging.getLogger(__name__)


def show(*args, **kwargs):
    """Show the widget within a maya workspaceControl."""
    dock = kwargs.pop("dock", True)
    floating = kwargs.get("floating")
    if not dock:
        kwargs["floating"] = floating if floating is not None else True

    # show the widget
    window = MayaToolbar()
    window.dock(*args, **kwargs)
    return window


def maya_window():
    """Return the MayaWindow if in Maya else None."""
    for each in QtWidgets.QApplication.topLevelWidgets():
        if each.objectName() == "MayaWindow":
            return each
    return None


def to_qwidget(ctrl):
    """Convert a Maya widget to a PySide2 QWidget.

    Args:
        ctrl (str): Name of the maya widget as a string.

    Returns:
        QtWidgets.QWidget: QWidget instance object of the given widget.
    """
    for method in ["findControl", "findLayout", "findMenuItem"]:
        ptr = getattr(OpenMayaUI.MQtUtil, method)(ctrl)
        if ptr:
            return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
    return None


class MayaToolbar(main.BaseToolbar):
    """Create a script launcher window."""

    DCC_TABS_FOLDER = os.path.dirname(__file__)

    def __init__(self, parent=None):
        parent = parent or maya_window()
        super(MayaToolbar, self).__init__(parent=parent)
        self.dock_title = "Launcher"
        self.dock_area = "left"

    def dock(self, title=None, area=None, floating=False):
        """Launch in a dock."""
        dock_widget(
            self,
            title=title or self.dock_title or self.windowTitle(),
            area=area or self.dock_area,
            floating=floating,
        )

    @staticmethod
    def repeatable(callback):
        """Make the command repeatable.

        Note:
            In Maya, the `repeatLast` command can only run MEL code
            which makes the passed python callback unusable.
            To make it work, we have to use the `config` module to run the
            callback as a global variable, accessible in the Maya main scope.

        Args:
            callback (function): Method executed by the button.
        """
        # the callback can error even though mel.eval-ing it works...
        try:
            cmd = "import {0};{0}.COMMAND_CALLBACK()".format(cfg.__name__)
            cmds.repeatLast(addCommand='python("{}")'.format(cmd))
        except BaseException:  # pylint: disable=broad-except
            pass


def dock_widget(widget, title="DockWindow", area="right", floating=False):
    """Dock the given widget properly for both M2016 and 2017+."""
    # convert widget to Qt if needed
    if not issubclass(widget.__class__, QtCore.QObject):
        widget = to_qwidget(widget)

    # make sure our widget has a name
    name = widget.objectName()
    if not name:
        name, num = title + "_mainWindow", 1
        while cmds.control(name, exists=True):
            name = title + "_mainWindow" + str(num)
            num += 1
        widget.setObjectName(title + "_mainWindow")

    # if `floating` is True, return with `widget.show()`
    if floating is True:
        if not widget.windowTitle():
            widget.setWindowTitle(title)
        widget.show()
        return widget

    # make sure the workspaceControl doesn't exist yet
    control = name + "_WorkspaceControl"
    if cmds.control(control, exists=True):
        cmds.deleteUI(control)

    # create workspaceControl (only works with Maya 2017+)
    flags = {"dockToControl": ["ToolBox", "right"]}
    if area == "right":
        # If the ChannelBox is not visible, fallback on the AttributeEditor.
        _control = "ChannelBoxLayerEditor"
        if not cmds.workspaceControl(_control, query=True, visible=True):
            _control = "AttributeEditor"
        flags = {"tabToControl": [_control, -1]}
    control = cmds.workspaceControl(control)
    cmds.workspaceControl(control, edit=True, label=title, r=True, **flags)

    # Convert workspace to Qt and add the widget into its layout.
    workspace = to_qwidget(control)
    layout = workspace.layout()
    layout.addWidget(widget)

    return widget
