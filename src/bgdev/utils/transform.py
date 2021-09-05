"""Utility methods for transforms.

:created: 16/02/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>"""
from __future__ import absolute_import

from maya import cmds


def reset_groups(suffix="_grp"):
    """Run :func:`reset_group` on a selection of multiple nodes.

    Args:
        suffix (str): suffix to use for the reset group name

    Returns:
        list: all reset group created

    """
    selection = cmds.ls(selection=True)

    groups = []
    for each in selection:
        reset_grp = reset_group(each, suffix)
        groups.append(reset_grp)

    return groups


def reset_group(node, suffix="_grp"):
    """Create a transform node to reset the value of the selected object.

    Args:
        node (str): name of node to reset
        suffix (str): suffix to use for the reset group name

    Returns:
        str: reset group

    """
    # create transform group
    name = "{}_{}".format(node.rsplit("_", 1)[0], suffix)
    reset_grp = cmds.createNode("transform", name=name)
    cmds.parent(reset_grp, node)
    cmds.makeIdentity(reset_grp, translate=True, rotate=True, scale=True)

    # reparent under parent if any, else world
    parent = (cmds.listRelatives(node, parent=True) or [None])[0]
    if parent:
        cmds.parent(reset_grp, parent)
    else:
        cmds.parent(reset_grp, world=True)
    cmds.parent(node, reset_grp)

    # for joints, reset rotates and jointOrients
    if cmds.nodeType(node) == "joint":
        cmds.makeIdentity(node, jointOrient=True, rotate=True, apply=True)

    cmds.select(clear=True)

    return reset_grp
