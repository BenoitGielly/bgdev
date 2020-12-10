"""Create and set bindpose on controlers.

:created: 17/01/2019
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
import json

from maya import cmds
import pymel.core as pm

RIG_UNLOCK_LIST = [
    "translate",
    "translateX",
    "translateY",
    "translateZ",
    "rotate",
    "rotateX",
    "rotateY",
    "rotateZ",
    "scale",
    "scaleX",
    "scaleY",
    "scaleZ",
    "jointOrientX",
    "jointOrientY",
    "jointOrientZ",
    "visibility",
    "rotateOrder",
]


def get_all_controls():
    """Get all rig controlers in the scene."""
    controlers = set()

    # get controls using CONTROLS set
    if cmds.objExists("CONTROLS"):
        controlers.update(cmds.sets("CONTROLS", query=True) or [])

    # get controlers using suffix
    controlers.update(cmds.ls("*_ctrl"))

    # get controlers using TSM3 attribute
    for ctrl in cmds.ls("*.TSM3Control"):
        controlers.add(ctrl.split(".")[0])

    return controlers


def create_bindpose():
    """Create a bindpose attribute on every controls."""
    attr_name = "bindpose_value"

    for ctrl in get_all_controls():
        attr_data = {}
        all_attr = list(RIG_UNLOCK_LIST)
        all_attr.extend(cmds.listAttr(ctrl, userDefined=True) or [])

        # remove the unwanted attributes from the list
        for attr in ["attributeAliasList", attr_name]:
            if attr in all_attr:
                all_attr.remove(attr)

        # remove the attribute if its type is "message"
        for attr in list(all_attr):
            node_attr = "{0}.{1}".format(ctrl, attr)
            if not cmds.objExists(node_attr):
                all_attr.remove(attr)
            elif cmds.getAttr(node_attr, type=True) == "message":
                all_attr.remove(attr)

        for attr in all_attr:
            node_attr = "{0}.{1}".format(ctrl, attr)
            if cmds.getAttr(node_attr, lock=True):
                continue

            value = cmds.getAttr(node_attr)
            if isinstance(value, list) and isinstance(value[0], (list, tuple)):
                value = value[0]
            elif value is None:
                value = ""
            attr_data[attr] = value

        # create a string attribute to store the data
        node_attr = "{0}.{1}".format(ctrl, attr_name)
        if not cmds.objExists(node_attr):
            cmds.addAttr(ctrl, longName=attr_name, dataType="string")
        cmds.setAttr(node_attr, json.dumps(attr_data), type="string")


def restore_bindpose(selected=True):
    """Restore the rig controls to their bindpose.

    Args:
        selected (bool): If True, reset only selected controls, otherwise
            reset every controls of each selected rigs.

    """
    nodes = cmds.ls(selection=True)
    if not selected:
        namespaces = set()
        for each in nodes:
            namespaces.add(each.rpartition(":")[0] + ":")

        nodes = []
        for each in namespaces:
            nodes.extend(
                [x.split(".")[0] for x in cmds.ls(each + "*.bindpose_value")]
            )

    for ctrl in nodes:
        data = json.loads(cmds.getAttr(ctrl + ".bindpose_value"))
        for attr, value in data.items():
            node_attr = "{0}.{1}".format(ctrl, attr)
            if cmds.getAttr(node_attr, settable=True):
                # using pymel here to prevent multiple if/elses
                # for each attribute type...
                pm.setAttr(node_attr, value)
