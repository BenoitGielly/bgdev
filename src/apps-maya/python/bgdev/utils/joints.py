"""Utility methods about joints.

:created: 13/02/2018
:author: Benoit GIELLY <benoit.gielly@gmail.com>
"""
from __future__ import absolute_import

from maya import cmds


def show_joint_orient(state=True):
    """Toggle jointOrient and preferredAngle attributes in channelBox.

    Applies to all joints in the scene.

    Args:
        state (bool): True if you want to display jointOrients in channelbox.
    """
    for each in cmds.ls(type="joint"):
        for attr in "XYZ":
            cmds.setAttr(
                "{}.jointOrient{}".format(each, attr),
                channelBox=state,
            )

            cmds.setAttr(
                "{}.preferredAngle{}".format(each, attr),
                channelBox=state,
            )


def add_joints(number=None):
    """Add joints inbetween.

    Args:
        number (int): amount of joints to add. If none given, a prompt will ask the user.

    Raises:
        TypeError: If given type is not a number.
        RuntimeError: If no joints are selected, or only one is but has no children.

    """
    number = number if number else input()
    if not isinstance(number, (int, float)):
        raise TypeError("Number is not of <type float> or <type int>")

    joints = cmds.ls(selection=True, type="joint")
    if not joints:
        raise RuntimeError("Please, select at least 1 joint")

    elif len(joints) == 1:
        children = cmds.listRelatives(joints[0], children=True, type="joint")
        if not children:
            raise RuntimeError("Selected joint has no child!")
        joints.extend(children)

    elif len(joints) > 2:
        joints = joints[0:2]

    old, jnt = "", None
    for i in range(number):
        jnt = cmds.duplicate(
            joints[-1], returnRootsOnly=True, parentOnly=True
        )[0]
        dist = cmds.getAttr(jnt + ".translateX")
        value = float(dist) / (number + 1)
        cmds.setAttr(jnt + ".translateX", value * (i + 1))
        try:
            cmds.parent(jnt, old)
        except (RuntimeError, ValueError):
            pass
        old = jnt
    cmds.parent(joints[-1], jnt)
