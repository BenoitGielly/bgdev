"""Utility methods about constraints.

:created: 05/03/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

from maya import cmds

import bgdev.utils.decorator

LOG = logging.getLogger(__name__)


@bgdev.utils.decorator.UNDO_REPEAT
def matrix_constraint_callback(srt="trs"):
    """Call back :func:`update intermediate`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")

    for target in selection[1:]:
        matrix_constraint(selection[0], target, srt=srt)


def matrix_constraint(driver, target, srt="srt"):
    """Constraint one node to another using their worldMatrix attributes.

    Args:
        driver (str): The driver node
        target (str): The node that follow the driver.
        srt (str): The attributes to connect.

    Returns:
        tuple: The multMatrix and decomposeMatrix nodes.

    """
    cmds.loadPlugin("matrixNodes", quiet=True)

    # define/create nodes
    mult = cmds.createNode("multMatrix", name=target + "_multMatrix")
    decompose = cmds.createNode(
        "decomposeMatrix", name=target + "_decomposeMatrix"
    )

    # pylint: disable=pointless-statement,expression-not-assigned
    plug = driver + ".worldMatrix[0]"
    if cmds.nodeType(driver) == "choice":
        plug = driver + ".output"

    cmds.connectAttr(plug, mult + ".matrixIn[0]")
    cmds.connectAttr(target + ".parentInverseMatrix[0]", mult + ".matrixIn[1]")
    cmds.connectAttr(mult + ".matrixSum", decompose + ".inputMatrix")

    for attr in [x + y for x in srt.lower() for y in "xyz"]:
        cmds.connectAttr(
            "{0}.o{1}".format(decompose, attr), "{0}.{1}".format(target, attr)
        )

    return mult, decompose


def aim_to_children(up_vector=(0, 1, 0), aim_vector=(1, 0, 0)):
    """Find an up vector for the selection and aim toward each others.

    Args:
        up_vector:
        aim_vector:

    """
    import pymel.core as pm

    # make sure selection order is active
    pref = pm.selectPref(query=True, trackSelectionOrder=True)
    if not pref:
        pm.selectPref(trackSelectionOrder=True)
        msg = "Turning on 'Selection-Order Tracking' option."
        msg += "You need to re-do your selection !"
        pm.error(msg)

    # get selection in order
    selection = pm.ls(orderedSelection=True)

    # create up loc
    pt_up = pm.spaceLocator(name="pt_up")
    point = pm.pointConstraint([selection[0], selection[-1]], pt_up)
    aim = pm.aimConstraint(
        selection[-1],
        pt_up,
        upVector=(0, 1, 0),
        worldUpObject=selection[1],
        worldUpType="object",
        aimVector=(1, 0, 0),
    )
    pm.delete(point, aim)

    pt_a = selection[0].getTranslation(space="world")
    pt_b = selection[-1].getTranslation(space="world")
    dist = [0, (pt_a - pt_b).length(), 0]
    pm.move(
        pt_up, dist, relative=True, objectSpace=True, worldSpaceDistance=True,
    )

    # aim each others according to the pt_up Vector
    for i, each in enumerate(selection):
        if (i + 1) < len(selection):
            aim = pm.aimConstraint(
                selection[i + 1],
                each,
                upVector=up_vector,
                worldUpObject=pt_up,
                worldUpType="object",
                aimVector=aim_vector,
            )
            pm.delete(aim)
        else:
            rotation = pm.xform(
                selection[i - 1], query=True, rotation=True, worldSpace=True,
            )
            pm.xform(each, rotation=rotation, worldSpace=True)

    pm.delete(pt_up)
