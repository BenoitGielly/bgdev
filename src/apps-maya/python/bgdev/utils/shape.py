"""Utility methods for shapes.

:created: 05/03/2017
:author: Benoit Gielly <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

import logging

import bgdev.utils.decorator
from maya import cmds

LOG = logging.getLogger(__name__)


def get_shapes(node, intermediate=False, exclusive=False):
    """Get the shapes of given node.

    Args:
        node (str): Node to query its shapes
        intermediate (bool): Get intermediate shapes when True.
        exclusive (bool): Only return the intermediate shapes if True.
            Please note that the intermediate flag must be True as well.

    Returns:
        list: The shapes found below given node.

    """
    # if given node is a list, assume first element
    if isinstance(node, list):
        node = node[0]
        LOG.info("Given node is a list. Using first element.")

    # return as list if given node is already a shape
    if cmds.objectType(node, isAType="shape"):
        return [node]

    # query shapes
    shapes = (
        cmds.listRelatives(
            node,
            shapes=True,
            type="deformableShape",
        )
        or []
    )

    # separate shapes orig
    orig = []
    for each in list(shapes):  # duplicated `shapes` object to remove safely
        if cmds.ls(each, intermediateObjects=True):
            orig.append(each)
            shapes.remove(each)

    if not intermediate:
        return shapes

    if exclusive:
        return orig

    return shapes + orig


@bgdev.utils.decorator.UNDO_REPEAT
def update_intermediate_callback():
    """Call back :func:`update intermediate`."""
    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please select at least 2 nodes!")

    for target in selection[1:]:
        update_intermediate(selection[0], target)


def update_intermediate(source, target):
    """Update shapeOrig of target with source shape.

    This tool also works on nubrsCurve and any deformableShapes.
    It will only replace one with another.

    Args:
        source (str): source node
        target (str): target node

    """
    if not any([cmds.objExists(_) for _ in (source, target)]):
        LOG.warn("Source or Target doesn't exist!")
        return

    # get source and target shapes
    source_shapes = get_shapes(source) or [None]
    if not source_shapes:
        LOG.error("Source shape not found!")
        return

    target_shapes = get_shapes(target, intermediate=True, exclusive=True)
    if not target_shapes:
        target_shapes = get_shapes(target)

    if not target_shapes:
        LOG.error("Target shapes not found!")
        return

    if len(source_shapes) == len(target_shapes):
        for source_shape, target_shape in zip(source_shapes, target_shapes):
            update_plug(source_shape, target_shape)
    else:
        for target_shape in target_shapes:
            update_plug(source_shapes[0], target_shape)


def update_plug(source_shape, target_shape):
    """Update the plug.

    Args:
        source_shape (str): Name of the source shape.
        target_shape (str): Name of the target shape to update.

    """
    if cmds.nodeType(target_shape) == "mesh":
        src_plug = "{0}.worldMesh".format(source_shape)
        tgt_plug = "{0}.inMesh".format(target_shape)
    elif cmds.nodeType(target_shape) in ("nurbsCurve", "nurbsSurface"):
        src_plug = "{0}.worldSpace".format(source_shape)
        tgt_plug = "{0}.create".format(target_shape)
    else:
        return

    intermediate = cmds.getAttr(target_shape + ".intermediateObject")
    cmds.setAttr(target_shape + ".intermediateObject", False)
    cmds.connectAttr(src_plug, tgt_plug, force=True)
    cmds.refresh()

    # cmds.dgeval(tgt_plug) ? or target_shape + ".create"
    # cmds.dgeval(destination + '.outMesh')

    cmds.disconnectAttr(src_plug, tgt_plug)
    cmds.setAttr(target_shape + ".intermediateObject", intermediate)

    LOG.info("Replaced %s with %s.", target_shape, source_shape)
