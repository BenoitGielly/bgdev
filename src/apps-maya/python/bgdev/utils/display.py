"""Utility methods about viewport display.

:created: 13/02/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from maya import cmds


def real_focus():
    """Zoom to the current selection's manipulator position."""
    panel = cmds.getPanel(withFocus=True)
    if cmds.getPanel(typeOf=panel) == "modelPanel":
        camera = cmds.lookThru(panel, query=True)
        cmds.viewFit(camera, allObjects=False, fitFactor=1.0)


def real_focus_old():
    """Zoom to the current selection's manipulator position."""
    panel = cmds.getPanel(withFocus=True)
    if cmds.getPanel(typeOf=panel) != "modelPanel":
        return

    # get selection
    selection = cmds.ls(selection=True)
    if not selection:
        return

    # get current manipulator position
    current = cmds.currentCtx()
    cmds.setToolTo("moveSuperContext")
    position = cmds.manipMoveContext("Move", query=True, position=True)
    cmds.setToolTo(current)

    # create and snap a locator to the manipulator position
    camera = cmds.lookThru(panel, query=True)
    locator = cmds.spaceLocator(position=position)
    cmds.select(locator)
    cmds.viewFit(camera, allObjects=False, fitFactor=0.250)
    cmds.delete(locator)

    # restore selection
    cmds.select(selection)


def viewport_display_types(flag=None):
    """Toggle the viewport options.

    Possible flags:
        - allObjects
        - nurbsCurves
        - polymeshes
        - joints
        - locators
        - etc...

    """
    if flag == "allObjects":
        all_objects_value = 1 - globals().setdefault("all_objects_value", 1)
        cmds.modelEditor(
            "modelPanel4", edit=True, allObjects=all_objects_value
        )

    elif flag is not None:
        flag_value = 1 - cmds.modelEditor(
            "modelPanel4", query=True, **{flag: True}
        )
        cmds.modelEditor("modelPanel4", edit=True, **{flag: flag_value})
