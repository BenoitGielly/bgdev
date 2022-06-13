"""Utility methods about locators.

:created: 05/03/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

from maya import cmds

import bgdev.utils.decorator
import bgdev.utils.vector

LOG = logging.getLogger(__name__)


@bgdev.utils.decorator.UNDO_REPEAT
def create_aim_locator(
    middle=False, aim_vector=(1, 0, 0), up_vector=(0, 1, 0)
):
    """Create a locator that's oriented on the selection.

    If selection is 2 or 3, it will use the second as the aim axis,
    and the third as up.
    If middle is set to False, it will snap it to the first selected.

    Args:
        middle (bool): snap in between points 1 and 2 if True, else on point 1.
        aim_vector (tuple): default aim vector for the aimConstraint.
        up_vector (tuple): default up vector for the aimConstraint.

    Returns:
        str: The locator created.

    Raises:
        RuntimeError: If nothing is selected.

    """
    # make sure orderedSelection is enabled
    if not cmds.selectPref(query=True, trackSelectionOrder=True):
        cmds.selectPref(trackSelectionOrder=True)
        cmds.select(clear=True)
        cmds.warning(
            "Selection Order was disabled. " "Please run the tool again!"
        )
        return None

    # get selection
    selection = cmds.ls(orderedSelection=True, flatten=True)
    if not selection:
        raise RuntimeError("You must select at least 1 node or component!")

    # get matrix array
    matrix_array = bgdev.utils.vector.get_matrix_from_nodes(
        selection, middle, aim_vector, up_vector
    )

    # create name string
    _split = selection[0].rsplit("_", 1)[0]
    if "." in selection[0]:
        _split = selection[0].rsplit(".", 1)[0].replace("Shape", "")
    name = _split + "_locator" if _split else selection[0] + "_locator"
    name = name + "#" if cmds.objExists(name) else name

    # create locator and set matrix
    locator = cmds.spaceLocator(name=name)[0]
    cmds.xform(locator, matrix=matrix_array, worldSpace=True)
    cmds.setAttr(locator + ".scale", 1, 1, 1)
    cmds.isolateSelect("modelPanel4", addDagObject=locator)

    # try to set locator scale
    distance = 2
    try:
        furthest_node = bgdev.utils.vector.get_closest_point(
            locator, selection, furthest=True
        )
        distance = bgdev.utils.vector.get_distance_between(
            locator, furthest_node
        )
    except ValueError:
        pass

    if distance > 2:
        cmds.setAttr(locator + ".localScale", *[distance / 2.0] * 3)

    return locator


def locator_on_selection(method="matrix"):
    """Create and snap a locator on selected nodes.

    Args:
        method (str):
            "matrix" uses Maya's xform command with matrix flag enabled.
            "pivot" uses Maya's xform command with rotatePivot flag enabled.
            "manip" queries Maya's move manipulator position and orientation.

    """
    # get selection
    selection = cmds.ls(selection=True, flatten=True)
    for each in selection:

        name = each + ("locator" if each.endswith("]") else "_locator")
        if cmds.objExists(name):
            name += "#"

        if method == "matrix":
            matrix = cmds.xform(each, query=True, matrix=True, worldSpace=True)
            locator = cmds.spaceLocator(name=name)[0]
            cmds.xform(locator, matrix=matrix, worldSpace=True)

        elif method == "translation":
            position = cmds.xform(
                each, query=True, worldSpace=True, translation=True
            )
            rotation = cmds.xform(
                each, query=True, rotation=True, worldSpace=True
            )
            locator = cmds.spaceLocator(name=name)[0]
            cmds.xform(
                locator,
                translation=position,
                rotation=rotation,
                worldSpace=True,
            )

        elif method == "pivot":
            position = cmds.xform(
                each, query=True, worldSpace=True, rotatePivot=True
            )
            rotation = cmds.xform(
                each, query=True, rotation=True, worldSpace=True
            )
            locator = cmds.spaceLocator(name=name)[0]
            cmds.xform(
                locator,
                translation=position,
                rotation=rotation,
                worldSpace=True,
            )

        elif method == "manip":
            position = cmds.manipMoveContext("Move", query=True, position=True)
            rotation = cmds.manipPivot(query=True, orientation=True)[0]
            locator = cmds.spaceLocator(name=name)[0]
            cmds.xform(
                locator,
                translation=position,
                rotation=rotation,
                worldSpace=True,
            )

        else:
            continue

        # set locator scale
        furthest_node = bgdev.utils.vector.get_closest_point(
            locator, selection, furthest=True
        )
        distance = (
            bgdev.utils.vector.get_distance_between(locator, furthest_node)
            or 10
        )
        cmds.setAttr(locator + ".localScale", *[distance / 10.0] * 3)
        cmds.isolateSelect("modelPanel4", addDagObject=locator)


def attach_locators_to_curve():
    """Attach a locator on each curve CVs."""
    import pymel.core as pm

    selection = pm.ls(selection=True)
    curve = [x for x in selection if x.getShape().type() == "nurbsCurve"][0]
    locator = [x for x in selection if x.getShape().type() != "nurbsCurve"]

    if not locator:
        for i, point in enumerate(curve.getShape().getCVs()):
            loc = pm.spaceLocator(name=curve + "{0:02d}_pos".format(i + 1))
            pm.xform(loc, translation=point, worldSpace=True)
            locator.append(loc)

    for i, point in enumerate(curve.comp("point")):
        if locator:
            loc = bgdev.utils.vector.get_closest_point(point, locator)
        else:
            pos = point.getPosition(space="world")
            loc = pm.spaceLocator()
            loc.setTranslation(pos, space="world")
        shp = loc.getShape()
        shp.wp[0] >> curve.cp[i]  # pylint: disable=pointless-statement
