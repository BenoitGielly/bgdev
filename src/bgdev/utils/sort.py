"""Utility methods used to sort nodes and graphs.

:created: 05/03/2017
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging
import re

from maya import cmds

LOG = logging.getLogger(__name__)


def as_int(text):
    """Convert text to integer."""
    return int(text) if text.isdigit() else text


def _human(text):
    """Sort elements using Human/Natural order.

    Notes:
        https://nedbatchelder.com/blog/200712/human_sorting.html
        https://blog.codinghorror.com/sorting-for-humans-natural-sort-order

    Args:
        text (str): One string element of the list to sort.

    Returns:
        list: List of integers to be used as a sorting key.

    """
    return [as_int(c) for c in re.split("([0-9]+)", text)]


def _human2(text):
    """Old algorithm, didn't work in all cases."""
    result = [as_int(x) for x in re.split(r"(\d+)", text) if x.isdigit()]
    return result[-1] if result else None


def sort_descendants():
    """Sort all descandant children alphabetically."""
    selection = cmds.ls(selection=True)

    nodes = cmds.listRelatives(
        selection, allDescendents=True, type="transform"
    )
    nodes = [x for x in nodes if not cmds.listRelatives(x, shapes=True)]
    nodes.extend(selection)

    for each in nodes:
        children = cmds.listRelatives(each, children=True)
        if children:
            sort_children(each)

    cmds.select(selection)


def sort_children(parent=None):
    """Sort children of the given parent alphabetically.

    Args:
        parent (str): Name of the parent to use as a starting point.

    """
    parent = parent or cmds.ls(selection=True)[0]
    children = cmds.listRelatives(parent, children=True)

    nodes = []
    with_shapes = []
    for each in children:
        if cmds.nodeType(each) != "joint":
            if not cmds.listRelatives(each, shapes=True):
                nodes.append(each)
            else:
                with_shapes.append(each)

    nodes.sort(key=_human)
    with_shapes.sort(key=_human)

    cmds.parent(children, world=True)
    cmds.parent(nodes, with_shapes, parent)
    cmds.select(parent)


def sort_selection():
    """Sort all children node alphabetically."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please, select at least one node!")
        return

    selection.sort(key=_human)

    parent = cmds.listRelatives(selection[0], parent=True)
    cmds.parent(selection, world=True)
    cmds.parent(selection, parent)
