"""Make any window dockable within Maya.

:created: 8 Jun 2018
:author: Benoit Gielly <benoit.gielly@gmail.com>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from maya import cmds
from maya import mel
from qtpy.QtCore import QObject

from . import utils


def dock_widget(widget, label="DockWindow", area="right", floating=False):
    """Dock the given widget properly for both M2016 and 2017+."""
    # convert widget to Qt if needed
    if not issubclass(widget.__class__, QObject):
        widget = utils.to_qwidget(widget)

    # make sure our widget has a name
    name = widget.objectName()
    if not name:
        name, num = label + "_mainWindow", 1
        while cmds.control(name, exists=True):
            name = label + "_mainWindow" + str(num)
            num += 1
        widget.setObjectName(label + "_mainWindow")

    # if `floating` is True, return with `widget.show()`
    if floating is True:
        if not widget.windowTitle():
            widget.setWindowTitle(label)
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
    cmds.workspaceControl(control, edit=True, label=label, r=True, **flags)

    # Convert workspace to Qt and add the widget into its layout.
    workspace = utils.to_qwidget(control)
    layout = workspace.layout()
    layout.addWidget(widget)

    return widget


def get_available_controls():
    """Return all the available Controls in list.

    Returns:
        list: List of existing workspaceControls.

    """
    if not hasattr(cmds, "workspaceControl"):
        return []

    tools = mel.eval("$ctrl_tmp_var = $gUIComponentToolBarArray;")
    docks = mel.eval("$ctrl_tmp_var = $gUIComponentDockControlArray;")
    controls = sorted({
        x for x in tools + docks if cmds.workspaceControl(x, exists=True)
    })

    return controls
