"""Attribute utilities using OpenMaya.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from collections import OrderedDict

from maya import cmds
from maya.api import OpenMaya

from . import core


def is_free(plug):
    """Get the plug's isFreeToChange state."""
    plug = core.as_plug(plug)
    return plug.isFreeToChange() == OpenMaya.MPlug.kFreeToChange


def is_locked(plug):
    """Get the plug's locked state."""
    return core.as_plug(plug).isLocked


def get_multi_indices(plug):
    """Get the plug's multi-indices."""
    plug = core.as_plug(plug)
    indices = plug.getExistingArrayAttributeIndices() if plug.isArray else []
    return indices or []


def get_next_index(plug):
    """Get next available index in given plug."""
    i = -1
    for i, j in enumerate(get_multi_indices(plug)):
        if i != j:
            return i
    return i + 1


def set_alias(plug, alias, remove=False):
    """Set or remove an alias on given plug."""
    plug = core.as_plug(plug)
    node = core.as_node(plug)
    name = plug.partialName(useLongNames=True)
    return node.setAlias(alias, name, plug, add=not remove)


def get_alias(plug):
    """Get given plug's alias if any."""
    plug = core.as_plug(plug)
    return core.as_node(plug).plugsAlias(plug)


def get_alias_list(node):
    """Get all alias attribute in pair from given node."""
    return core.as_node(node).getAliasList()


def get_node_aliases(node, attr="weight", indices=False):
    """Get a list of given node's aliases ordered by their index.

    Args:
        node (str): The node whose aliases will be queried.
        attr (str): The name of the attribute to query.
        indices (bool): If True, returns a dict with indices as values.

    Returns:
        list or dict: List of aliases in index order.

    """

    def get_index(name):
        """Sort function to return the index as an integer."""
        return int(name.rsplit("[")[-1].split("]")[0])

    pair_data = {y: get_index(x) for y, x in get_alias_list(node) if attr in x}
    targets = sorted(pair_data, key=pair_data.get)
    if indices:
        return OrderedDict((x, pair_data.get(x)) for x in targets)
    return targets


def get_attr(name, settable=None, multiIndices=None, lock=None):
    # pylint:disable=invalid-name
    """Reproduce the getAttr using OpenMaya."""
    plug = core.as_plug(name)
    if lock:
        return plug.isLocked
    if multiIndices:
        if plug.isArray:
            return plug.getExistingArrayAttributeIndices()
        return None
    if settable:
        return is_free(plug)

    type_ = plug.attribute().apiTypeStr
    if type_ == "kTypedAttribute":
        return plug.asString()
    if type_ == "kDoubleAngleAttribute":
        return plug.asMAngle().asDegrees()
    return plug.asFloat()


def disconnect_all_plugs(name, source=True, destination=True):
    """Disconnect all inputs and/or outputs of given node."""
    modifier = OpenMaya.MDagModifier()
    for plug in core.as_node(name).getConnections():
        plug.isLocked = False
        if source and plug.isDestination:
            modifier.disconnect(plug.source(), plug)
        if destination and plug.isSource:
            for each in plug.destinations():
                modifier.disconnect(plug, each)
    modifier.doIt()


def reorder_attributes(node, attributes):
    """Reorder given attributes to the bottom of the channelBox.

    Args:
        node (str): Node to work on.
        attributes (list): List of attributes to reorder.
    """
    locked = []
    for each in attributes:
        plug = node + "." + each
        if cmds.getAttr(plug, lock=True):
            cmds.setAttr(plug, lock=False)
            locked.append(each)
        try:
            cmds.deleteAttr(node, attribute=each)
            cmds.undo()
        except RuntimeError:
            pass

    for each in locked:
        plug = node + "." + each
        cmds.setAttr(plug, lock=True)
