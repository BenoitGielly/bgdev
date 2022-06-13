"""Attribute utilities.

:author: Benoit Gielly (benoit.gielly@gmail.com)
"""
from ast import literal_eval

from maya import cmds


def create_separator_attribute(node, name=None):
    """Create a separator attribute on the given node.

    Args:
        node (str): Name of the node to add the separator attribute.
        name (str): Name nice (category)

    """
    i, node_attr = 1, "{0}.separator1".format(node)
    while cmds.objExists(node_attr):
        i += 1
        node_attr = "{0}.separator{1}".format(node, i)

    node, attr = node_attr.split(".")
    cmds.addAttr(
        node,
        longName=attr,
        niceName=name or "-" * 12,
        attributeType="enum",
        enumName=":--------",
    )
    cmds.setAttr(node_attr, channelBox=True)


def attributes_toggle(nodes=None, attr_list=None):
    """Toggle attributes between default and unlocked states.

    Args:
        nodes (list): List of nodes to toggle. If not given, use viewport selection.
        attr_list (list): List of extra attributes to toggle
    """

    attr_list = attr_list or []
    nodes = nodes or cmds.ls(selection=True)
    for node in nodes:
        if not attributes_restore(node):
            attributes_unlock(node, attr_list=attr_list)


def attributes_restore(node):
    """Restore previously unlocked attributes to their default state.

    Args:
        node (str): Node to restore attributes

    Returns:
        bool: False if attribute doesn't exists else True

    """

    attr_name = "attributes_state"
    base_attr = "{}.{}".format(node, attr_name)
    if not cmds.objExists(base_attr):
        return False

    attr_data = literal_eval(cmds.getAttr(base_attr) or "{}")
    for _attr, values in attr_data.iteritems():
        node_attr = "{}.{}".format(node, _attr)
        cmds.setAttr(node_attr, **values)

    cmds.deleteAttr(base_attr)

    return True


def attributes_unlock(node, base=True, user=True, attr_list=None):
    """Unlock attributes on given node

    Args:
        node (str): Node to unlock attributes
        attr_list (list): List of extra attributes to toggle
        base (bool): If True, will toggle base attributes (translate, rotate, scale, visibility).
        user (bool): If True, will toggle user's attributes.
    """

    if not cmds.objExists(node):
        return

    # build attributes list with base attrs, user defined, and passed ones
    if not attr_list:
        attr_list = []

    if base:
        attr_list.extend("trsv")
        attr_list.extend([x + y for x in "trs" for y in "xyz"])

    if user:
        attr_list.extend(cmds.listAttr(node, userDefined=True) or [])

    attr_list = list(set(attr_list))

    # create attribute if doesn't exist
    attr_name = "attributes_state"
    base_attr = "{}.{}".format(node, attr_name)

    # if attribute already exists and has value, skip.
    if cmds.objExists(base_attr) and cmds.getAttr(base_attr):
        return

    # if doesn't exists, create it
    if not cmds.objExists(base_attr):
        cmds.addAttr(node, longName=attr_name, dataType="string")

    # unlock each attributes and store their original state in a str(dict) attr
    attr_data = {}
    is_ref = cmds.referenceQuery(node, isNodeReferenced=True)
    flags = {} if is_ref else {"keyable": True}
    for _attr in attr_list:
        node_attr = "{}.{}".format(node, _attr)
        attr_data[_attr] = {
            "channelBox": cmds.getAttr(node_attr, channelBox=True),
            "keyable": cmds.getAttr(node_attr, keyable=True),
            "lock": cmds.getAttr(node_attr, lock=True),
        }

        cmds.setAttr(node_attr, lock=False, **flags)

    # convert data to string and store it on the node
    attr_str = str(attr_data)
    cmds.setAttr(base_attr, attr_str, type="string")


def reorder_attributes(node, attributes):
    """Reorder attributes at the end.

    Args:
        node (str): Node that contains the attributes.
        attributes (list): Attributes to reorder as a list.
    """
    locked = []
    for each in attributes:
        plug = "{}.{}".format(node, each)
        if cmds.getAttr(plug, lock=True):
            cmds.setAttr(plug, lock=False)
            locked.append(each)
        try:
            cmds.deleteAttr(node, attribute=each)
            cmds.undo()
        except RuntimeError:
            pass

    # restore locked attributes
    for each in locked:
        cmds.setAttr("{}.{}".format(node, each), lock=True)
