"""Utility methods that parses names.

:created: 27/02/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging
import re

import bgdev.utils.decorator
from maya import cmds

LOG = logging.getLogger(__name__)


def find_conflicts(query=False):
    """Create two selection sets to store name conflicts.

    Args:
        query (bool): Only query the nodes without creating sets.

    Returns:
        tuple: Two separate lists for conflicting transforms and shapes.

    """
    conflict_nodes = []
    conflict_shapes = []

    for each in cmds.ls(transforms=True, shapes=True):
        if "|" in each:
            if cmds.objectType(each, isAType="shape"):
                conflict_shapes.append(each)
            else:
                conflict_nodes.append(each)

    # return here if query flag is True
    if query:
        return conflict_nodes, conflict_shapes

    # delete existing set_
    for set_ in ["NODES_NAME_CONFLICTS", "SHAPES_NAME_CONFLICTS"]:
        if cmds.objExists(set_):
            cmds.delete(set_)

    # create set if conflicts
    if conflict_nodes:
        cmds.sets(conflict_nodes, name="NODES_NAME_CONFLICTS")

    if conflict_shapes:
        cmds.sets(conflict_shapes, name="SHAPES_NAME_CONFLICTS")

    if not conflict_nodes and not conflict_shapes:
        LOG.warning("No conflincting names detected!")

    return conflict_nodes, conflict_shapes


def generate_unique_name(name):
    """Generate a unique name based on the given one."""
    count = 1
    while cmds.objExists(name):
        name = "{0}{1}".format(remove_end_digits(name, False), count)
        count += 1

    return name


@bgdev.utils.decorator.UNDO_REPEAT
def remove_end_digits_callback():
    """Call back :func:`remove_end_digits`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select something!")
        return

    for each in selection:
        remove_end_digits(each)


def remove_end_digits(node, rename=True):
    """Remove digits at the end of a name.

    Args:
        node (str): Name of the node to "cleanup"
        rename (bool): If True, rename the node, else just return the cleaned up name

    Returns:
        str: Name of the node stripped ouf ot end digits.

    """
    regex = re.compile(r"\w+\D+")
    name = node.rpartition("|")[2]
    new = regex.findall(name)[0]
    if rename:
        cmds.rename(node, new)

    return new


@bgdev.utils.decorator.UNDO_REPEAT
def rename_deformers_callback():
    """Call back :func:`rename_deformers`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select something!")
        return

    for each in selection:
        rename_deformers(each)


def rename_deformers(node=None):
    """Rename all the deformers in the history of the given node.

    The name string will be build according
    to the deformerType and the node name

    Args:
        node (str): The node you want to rename deformers attached to it

    Example:

        >>> node = "L_arm_geo"
        >>> deformerType = "skinCluster"
        >>> name = L_arm_geo_skinCluster"

    """
    # rename each according to their type
    history = cmds.listHistory(node)
    for each in history:
        if cmds.objectType(each, isAType="geometryFilter"):
            name = "{}_{}".format(node, cmds.nodeType(each))
            cmds.rename(each, name)
