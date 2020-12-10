"""Utility methods for curves.

:created: 04/02/2019
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

import bgdev.utils.vector
from maya import cmds

LOG = logging.getLogger(__name__)


def curve_interpolate(curve=None, segments=3):
    """Interpolate locators along a selected nurbsCurve.

    Args:
        curve (str): Name of the curve node. Use selection if None.
        segments (int): Amount of segments you want.

    Returns:
        list: The created locators.

    """
    if not (curve and cmds.objExists(curve)):
        selection = cmds.ls(selection=True)
        if not selection or len(selection) != 1:
            LOG.warning("Please, select just one nurbsCurve!")
            return
        curve = selection[0]

    rebuild = curve + "_rebuildCurve"
    if not cmds.objExists(rebuild):
        rebuild = cmds.createNode("rebuildCurve", name=rebuild)
        cmds.connectAttr(curve + ".worldSpace", rebuild + ".inputCurve")

    # remove previous nodes
    nodes = cmds.ls(curve + "_cv*_*")
    if nodes:
        cmds.lockNode(rebuild, lock=True)
        cmds.delete(nodes)
        cmds.lockNode(rebuild, lock=False)

    # create a group to parent the locators into
    parent = curve + "_locators_grp"
    if cmds.objExists(parent):
        cmds.delete(parent)
    parent = cmds.createNode("transform", name=parent)

    locators = []
    for i in range(segments + 1):
        name = "{0}_cv{1}_".format(curve, i)

        info = cmds.createNode(
            "pointOnCurveInfo", name=name + "pointOnCurveInfo"
        )
        cmds.connectAttr(
            rebuild + ".outputCurve", info + ".inputCurve", force=True
        )
        cmds.setAttr(info + ".turnOnPercentage", 1)
        cmds.setAttr(info + ".parameter", 1.0 / segments * i)

        locator = cmds.spaceLocator(name=name + "locator")[0]
        cmds.parent(locator, parent)
        if cmds.objExists("modelPanel4ViewSelectedSet"):
            cmds.sets(
                locator, edit=True, forceElement="modelPanel4ViewSelectedSet"
            )

        matrix = bgdev.utils.vector.get_matrix_from_transforms(
            cmds.getAttr(info + ".position")[0],
            cmds.getAttr(info + ".tangent")[0],
            cmds.getAttr(info + ".normal")[0],
        )
        cmds.xform(locator, matrix=matrix, worldSpace=True)
        locators.append(locator)

    return locators
