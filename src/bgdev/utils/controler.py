"""Utilities for controlers.

Mostly, controler shapes creation (needs to be turned into data)

:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import logging
import os

import yaml
from maya import cmds
from maya.api import OpenMaya

import bgdev.utils.color

LOG = logging.getLogger(__name__)

CTRL_SET_NAME = "animation_set"


def extract_shape_data(node, as_json=False):
    """Extract Maya's shape.cached attribute value.

    Note:
        Unfortunately, the only way that I found to extract the ".cached"
        attribute was to use Maya Python's API.

    Args:
        node (str): The name of the shape node to extract.
        as_json (bool): Returns the data in a json compatible format.

    Returns:
        list: The arguments needed by the cmds.setAttr() command.

    """

    selection = OpenMaya.MSelectionList()
    selection.add(node)
    dpcn = OpenMaya.MFnDependencyNode(selection.getDependNode(0))
    if dpcn.typeName == "transform":
        dag = selection.getDagPath(0)
        dpcn = OpenMaya.MFnDependencyNode(dag.child(0))
    plug = dpcn.findPlug("cached", 0)
    value = [x.strip().split() for x in plug.getSetAttrCmds()[1:-1]]

    # base arguments
    args = [int(x) for x in value[0][:3] + [value[0][-1]]]
    args.insert(-1, False if value[0][3] == "no" else True)

    # add knots
    args.append([int(x) for x in value[1][1:]])
    args.append(int(value[1][0]))

    # add CVs
    args.append(int(value[2][0]))
    args.extend([[float(y) for y in x] for x in value[3:]])

    if as_json:
        return json.dumps(args)

    return args


def select_all():
    """Select all controlers in the current scene."""
    nodes = get_all_controls() + get_all_controls("*")
    cmds.select(nodes)


def select_rig_controls():
    """Select all controlers from selected rig(s)."""
    nodes = get_rig_controls()
    cmds.select(nodes)


def get_all_controls(namespace=""):
    """Get all rig controlers in the scene."""
    controlers = set()

    # get controls using CONTROLS set
    ctrl_set = "{}:{}".format(namespace, CTRL_SET_NAME)
    if cmds.objExists(ctrl_set):
        controlers.update(cmds.sets(ctrl_set, query=True) or [])

    # get controlers using suffix
    controlers.update(cmds.ls(namespace + ":*_ctrl"))

    # get controlers using TSM3 attribute
    for ctrl in cmds.ls(namespace + ":*.TSM3Control"):
        controlers.add(ctrl.split(".")[0])

    for ctrl in cmds.ls(namespace + ":*TSM3_root"):
        controlers.add(ctrl.split(".")[0])

    return sorted(controlers)


def get_rig_controls():
    """Query all controlers of the selected rig(s)."""
    ctrls = []

    selection = cmds.ls(selection=True)
    if not selection:
        LOG.warning("Please, select any node from a rig!")
        return ctrls

    namespaces = list({x.rpartition(":")[0] for x in selection})
    for each in namespaces:
        ctrls.extend(get_all_controls(each))

    return ctrls


def get_ctrl_data(name, variant=0):
    """Query the controler data from its name."""
    path = os.path.join(
        os.path.dirname(__file__), "controlers", name + ".yaml"
    )
    if not os.path.exists(path):
        msg = (
            "%r doesn't exists. "
            "You can list them using the `list_controlers()` method."
        )
        LOG.warning(msg, name)
        return None

    with open(path, "r") as stream:
        data = yaml.safe_load(stream)

    return data.get("variant%s" % variant)


def list_controlers():
    """List all the available controls."""
    path = os.path.join(os.path.dirname(__file__), "controlers")

    ctrls = []
    for each in os.listdir(path):
        if each.endswith(".yaml"):
            ctrls.append(os.path.join(path, each))

    msg = "\nAvailable controls are (variants, name):\n"
    for each in ctrls:
        with open(each, "r") as stream:
            data = yaml.safe_load(stream)

        name = os.path.splitext(os.path.basename(each))[0]
        msg += "\t%s %r\n" % (len(data), name)
    print(msg)


def create_control(  # pylint: disable=too-many-arguments
    ctrl, variant=0, name=None, size=1.0, normal=(0, 1, 0), color="yellow"
):
    """Create a controler based on its name and variant.

    Args:
        ctrl (str): The type of controler you want to create.
            Use :func:`list_controlers` method to know which ones are available.
        variant (int): Which variant of the controler type you want.
        name (str): Rename the controler with the given name.
        size (float): Scale the controler using given size value.
        normal (tuple): Which axis should the controler aim to when created.
            Default axis is +Y
        color (str): The name of the CSS color to apply as an RGB override.
            Uses the qtpy StyleSheet API to convert names to RGB color.

    Returns:
        tuple: The controler and its shape.

    """
    flags = get_ctrl_data(ctrl, variant)
    if not flags:
        return None

    curve = cmds.curve(**flags)
    curve = cmds.rename(curve, name or ctrl + "1")
    shape = cmds.listRelatives(curve, shapes=True)[0]

    cmds.scale(*[size] * 3 + [curve + ".cv[*]"], relative=True)

    # swap X and Z (Y being the default normal-axis for all shapes)
    normal = normal[-1], normal[1], normal[0]
    normal = [x * 90 for x in normal]
    cmds.rotate(*normal + [curve + ".cv[*]"], relative=True)

    curve = cmds.rename(curve, name or ctrl + "1")
    shape = cmds.listRelatives(curve, shapes=True)[0]

    # set shape color
    rgba = bgdev.utils.color.convert_css_color(color)
    cmds.setAttr(shape + ".overrideEnabled", True)
    cmds.setAttr(shape + ".overrideRGBColors", True)
    cmds.setAttr(shape + ".overrideColorRGB", *rgba)

    return curve, shape
